"""
Core implementation of the AYON OpenAssetIO Manager Interface.
"""

import pathlib
from pathlib import Path
from typing import List, Set

import openassetio
import openassetio_mediacreation.traits as mc_traits
from openassetio.trait import TraitsData
from openassetio.errors import BatchElementError
from openassetio import EntityReference, access, Context
from openassetio.managerApi import HostSession, ManagerStateBase
from openassetio.utils import FileUrlPathConverter
from openassetio_mediacreation.traits.managementPolicy import ManagedTrait

import ayon_api
from ayon_core import pipeline

from . import ayon
from . import ayon_core_util

InfoDictionary = dict[str, str | float | int | bool]


class AyonManagerState(ManagerStateBase):
    """
    Ayon-specific manager state that can be used to cache project settings, etc.
    """

    # noinspection PyMissingConstructor
    def __init__(self, settings, entity_info: ayon.EntityInfo):
        ManagerStateBase.__init__(self)
        self.most_recent_resolved_entity_info = entity_info
        self.settings = settings


class AyonOpenAssetIOManagerInterfaceCore:
    """
    Implementation of the AYON OpenAssetIO Manager Interface.

    This class contains the actual implementation of the manager interface,
    while AyonOpenAssetIOManagerInterface acts as a proxy that delegates
    method calls to this class.

    This is due to the requirement for ayon_core to be imported at runtime.
    I.e. this class will not be imported at startup, but only when the
    AyonOpenAssetIOManagerInterface is `initialize()`d.
    """

    __reference_prefix = "ayon+entity://"

    def __init__(self, settings: InfoDictionary):
        self.__settings = settings
        self.__fileUrlPathConverter = FileUrlPathConverter()

    def createState(self, _host_session: HostSession) -> AyonManagerState:
        default_entity_info = ayon.EntityInfo(
            project_name=self.__settings.get(ayon.PROJECT_NAME_KEY),
            path=self.__settings.get(ayon.PATH_NAME_KEY),
            task_name=self.__settings.get(ayon.TASK_NAME_KEY),
        )

        return AyonManagerState(self.__settings, default_entity_info)

    @staticmethod
    def createChildState(
        parent_state: AyonManagerState, _host_session: HostSession
    ) -> AyonManagerState:
        return parent_state

    @staticmethod
    def managementPolicy(
        trait_sets: List[Set[str]],
        policy_access: access.PolicyAccess,
        _context: openassetio.Context,
        _host_session: openassetio.managerApi.HostSession,
    ) -> List[TraitsData]:  # noqa: E501,N802, N803
        policies = [TraitsData() for _ in trait_sets]

        for trait_set, policy in zip(trait_sets, policies):
            # TODO(DF): We should also disallow resolving/publishing traits
            #  based on the other traits in the trait set (or rather, based on
            #  defined Specifications). At the moment we're saying e.g. that we
            #  can resolve the OCIO colour space of audio, which probably
            #  doesn't make sense.

            if policy_access in (
                access.PolicyAccess.kRead,
                access.PolicyAccess.kWrite,
                access.PolicyAccess.kCreateRelated,
            ):
                if mc_traits.content.LocatableContentTrait.kId in trait_set:
                    mc_traits.content.LocatableContentTrait.imbueTo(policy)

                if mc_traits.color.OCIOColorManagedTrait.kId in trait_set:
                    mc_traits.color.OCIOColorManagedTrait.imbueTo(policy)

                if mc_traits.timeDomain.FrameRangedTrait.kId in trait_set:
                    mc_traits.timeDomain.FrameRangedTrait.imbueTo(policy)

            if policy_access == access.PolicyAccess.kManagerDriven:
                if mc_traits.content.LocatableContentTrait.kId in trait_set:
                    mc_traits.content.LocatableContentTrait.imbueTo(policy)

            # Here we're saying that, regardless of the asset type, if you want
            # to publish it then we need a location for it. This should change
            # if we can update/create other metadata without also updating the
            # location.
            if policy_access == access.PolicyAccess.kRequired:
                if mc_traits.content.LocatableContentTrait.kId in trait_set:
                    mc_traits.content.LocatableContentTrait.imbueTo(policy)

            if policy.traitSet():
                ManagedTrait.imbueTo(policy)

        return policies

    def isEntityReferenceString(self, some_string: str, _host_session: HostSession) -> bool:
        return some_string.startswith(self.__reference_prefix)

    @staticmethod
    def entityExists(
        entity_refs: list[EntityReference],
        _context: Context,
        _host_session: HostSession,
        success_callback,
        _error_callback,
    ) -> None:
        identities = ayon_core_util.query_identity_for_entity_refs(
            [str(ref) for ref in entity_refs]
        )

        for idx, rep in enumerate(identities):
            if rep["entities"]:
                success_callback(idx, True)
            else:
                success_callback(idx, False)

    def resolve(
        self,
        entity_references: list[EntityReference],
        trait_set: set[str],
        resolve_access: access.ResolveAccess,
        context: Context,
        host_session: HostSession,
        success_callback,
        error_callback,
    ) -> None:
        if resolve_access == access.ResolveAccess.kRead:
            self.__resolve_for_read(
                entity_references,
                trait_set,
                context,
                host_session,
                success_callback,
                error_callback,
            )
        elif resolve_access == access.ResolveAccess.kManagerDriven:
            self.__resolve_for_manager_driven(
                entity_references,
                trait_set,
                context,
                host_session,
                success_callback,
                error_callback,
            )
        else:
            raise NotImplementedError(f"Unexpected resolve() access mode: '{resolve_access}'")

    def __resolve_for_read(
        self,
        entity_references: list[EntityReference],
        trait_set: set[str],
        context: Context,
        host_session: HostSession,
        success_callback,
        error_callback,
    ) -> None:
        entity_identities = ayon_core_util.query_identity_for_entity_refs(
            [str(ref) for ref in entity_references]
        )

        for idx, rep in enumerate(entity_identities):
            entities = rep.get("entities")
            # If there are no entities in response, we were not able to resolve
            # any of the fields in the reference.
            if not entities:
                error_callback(
                    idx,
                    BatchElementError(
                        BatchElementError.ErrorCode.kEntityResolutionError, "Entity not found"
                    ),
                )
                continue

            entity_identity = entities[-1]

            entity_info = ayon.parse_entity_ref(str(entity_references[idx]))

            entity_representation = None
            if representation_id := entity_identity.get("representationId"):
                entity_representation = ayon_api.get_representation_by_id(
                    entity_info.project_name, representation_id
                )

            entity_version = None
            if version_id := entity_identity.get("versionId"):
                entity_version = ayon_api.get_version_by_id(entity_info.project_name, version_id)

            traits_data = TraitsData()

            # Display name:

            if mc_traits.identity.DisplayNameTrait.kId in trait_set:
                display_name_trait = mc_traits.identity.DisplayNameTrait(traits_data)
                leaf_name = ""
                if entity_info.product_name:
                    leaf_name += entity_info.product_name
                if entity_info.task_name:
                    leaf_name += entity_info.task_name
                if entity_info.workfile_name:
                    leaf_name += f"/{entity_info.workfile_name}"
                if entity_info.version_name:
                    leaf_name += f"@{entity_info.version_name}"

                display_name_trait.setName(leaf_name)
                display_name_trait.setQualifiedName(
                    "/".join((entity_info.project_name, entity_info.path, leaf_name))
                )

            # File path:

            if mc_traits.content.LocatableContentTrait.kId in trait_set:
                resolved_uri = None

                # Check if the representation is actually a collection of files. If so, assume this
                # means an ordered list of frames.
                # TODO(DF): Is this assumption correct?
                if entity_representation is not None and len(entity_representation["files"]) > 1:
                    frame_token = self.__create_frame_token(entity_info.project_name, host_session)

                    entity_representation["context"]["frame"] = frame_token

                    # Get root path for current project and site.
                    # TODO(DF): Cache this.
                    project_root = ayon_api.get_project_roots_by_site_id(
                        entity_info.project_name, ayon_api.get_site_id()
                    )

                    wildcard_path = pipeline.get_representation_path(
                        entity_representation, root=project_root
                    )

                    resolved_uri = Path(wildcard_path).as_uri()

                elif file_path := entity_identity.get("filePath"):
                    try:
                        resolved_uri = Path(file_path).as_uri()
                    except ValueError as exc:
                        # E.g. root path not resolved.
                        host_session.logger().error(
                            f"Failed to convert file path '{file_path}' to a URL: {exc}"
                        )

                if resolved_uri is not None:
                    # Only set location if URI was found. Note that if
                    # we don't set the location, the trait will not be
                    # imbued at all.
                    mc_traits.content.LocatableContentTrait(traits_data).setLocation(resolved_uri)

            if entity_version is not None:
                # Frame range:

                if mc_traits.timeDomain.FrameRangedTrait.kId in trait_set:
                    frame_ranged_trait = mc_traits.timeDomain.FrameRangedTrait(traits_data)
                    frame_ranged_trait.setStartFrame(
                        entity_version["attrib"]["frameStart"]
                        - entity_version["attrib"]["handleStart"]
                    )
                    frame_ranged_trait.setEndFrame(
                        entity_version["attrib"]["frameEnd"]
                        + entity_version["attrib"]["handleEnd"]
                    )
                    frame_ranged_trait.setInFrame(entity_version["attrib"]["frameStart"])
                    frame_ranged_trait.setOutFrame(entity_version["attrib"]["frameEnd"])
                    frame_ranged_trait.setFramesPerSecond(entity_version["attrib"]["fps"])

                # Colour space

                if mc_traits.color.OCIOColorManagedTrait.kId in trait_set:
                    if colorspace := entity_version["attrib"]["colorSpace"]:
                        ocio_trait = mc_traits.color.OCIOColorManagedTrait(traits_data)
                        ocio_trait.setColorspace(colorspace)

            if traits_data.traitSet():
                # Add entity info to context for use in UI pre-population, etc.
                context.managerState.most_recent_resolved_entity_info = entity_info

            success_callback(idx, traits_data)

    def __resolve_for_manager_driven(
        self,
        entity_references: list[EntityReference],
        trait_set: set[str],
        _context: Context,
        host_session: HostSession,
        success_callback,
        error_callback,
    ) -> None:
        entity_identities = ayon_core_util.query_identity_for_entity_refs(
            [str(ref) for ref in entity_references]
        )

        # Currently, we only support driving LocatableContentTrait for publishing.
        if mc_traits.content.LocatableContentTrait.kId not in trait_set:
            for idx in range(len(entity_references)):
                success_callback(idx, TraitsData())
            return

        for idx, entity_ref in enumerate(entity_references):
            entity_info = ayon.parse_entity_ref(str(entity_ref))

            if entity_info.preflight_data is None:
                error_callback(
                    idx,
                    BatchElementError(
                        BatchElementError.ErrorCode.kMalformedEntityReference,
                        "Entity reference does not contain preflight metadata."
                        " A working reference returned from preflight() is required.",
                    ),
                )
                continue

            resolved_traits = TraitsData()

            if entity_info.workfile_name is not None:
                # In-progress workfile.
                resolved_path = ayon_core_util.query_workfile_path(
                    entity_info, entity_identities[idx]["entities"][-1]
                )
                if resolved_path is None:
                    success_callback(idx, TraitsData())
                    continue
                resolved_path = pathlib.Path(resolved_path)

            else:
                # Asset (i.e. representation).
                staging_dir_result = ayon_core_util.query_staging_dir_for_entity(entity_info)
                if staging_dir_result is not None:
                    staging_dir = staging_dir_result.directory
                else:
                    staging_dir = None

                if staging_dir is None:
                    success_callback(idx, TraitsData())
                    continue

                resolved_path = pathlib.Path(staging_dir)

                resolved_filename = entity_info.product_name

                if entity_info.preflight_data.get("frame_ranged"):
                    frame_token = self.__create_frame_token(entity_info.project_name, host_session)
                    resolved_filename += f".{frame_token}"

                # Append colour space to file name, as is OCIO convention, and required for e.g.
                # Katana.
                if colorspace := entity_info.preflight_data.get("colorspace"):
                    resolved_filename += f".{colorspace}"

                resolved_filename += f".{entity_info.representation_name}"

                resolved_path /= resolved_filename

            # TODO(DF): Can/should ayon_core do this for us?
            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            mc_traits.content.LocatableContentTrait(resolved_traits).setLocation(
                resolved_path.as_uri()
            )

            success_callback(idx, resolved_traits)

    @staticmethod
    def preflight(
        target_entity_refs: list[EntityReference],
        traits_hints: list[TraitsData],
        _publishing_access: access.PublishingAccess,
        _context: Context,
        _host_session: HostSession,
        success_callback,
        _error_callback,
    ) -> None:
        for idx, (entity_ref, entity_traits_data) in enumerate(
            zip(target_entity_refs, traits_hints)
        ):
            entity_info = ayon.parse_entity_ref(str(entity_ref))

            # Data to be encoded in the entity reference, for use elsewhere
            # (e.g. resolve() with kManagerDriven access).
            preflight_data = {}

            if entity_info.product_type is None:
                entity_info.product_type = "workfile"

            # If there's no workfile name, then assume a representation, and if
            # there's no product name, derive product name from the available
            # entity fields.
            if entity_info.workfile_name is None and entity_info.product_name is None:
                entity_info.product_name = ayon_core_util.query_product_name_for_entity(
                    entity_info
                )

            if mc_traits.timeDomain.FrameRangedTrait.isImbuedTo(entity_traits_data):
                preflight_data["frame_ranged"] = True

            ocio_color_managed_trait = mc_traits.color.OCIOColorManagedTrait(entity_traits_data)
            if colorspace := ocio_color_managed_trait.getColorspace():
                preflight_data["colorspace"] = colorspace

            entity_info.preflight_data = preflight_data
            entity_info.version_name = None

            preflighted_ref_str = ayon.build_entity_ref(entity_info)
            preflighted_ref = EntityReference(preflighted_ref_str)

            success_callback(idx, preflighted_ref)

    def register(
        self,
        target_entity_refs: list[EntityReference],
        entity_traits_datas: list[TraitsData],
        _publishing_access: access.PublishingAccess,
        _context: Context,
        host_session: HostSession,
        success_callback,
        _error_callback,
    ) -> None:
        entity_identities = ayon_core_util.query_identity_for_entity_refs(
            [str(ref) for ref in target_entity_refs]
        )

        for idx, (entity_ref, entity_traits_data) in enumerate(
            zip(target_entity_refs, entity_traits_datas)
        ):
            entity_info = ayon.parse_entity_ref(str(entity_ref))
            is_workfile = entity_info.representation_name is None
            instance_data = {}

            # Frame range metadata.
            frame_ranged_trait = mc_traits.timeDomain.FrameRangedTrait(entity_traits_data)
            if frame_ranged_trait.isImbued():
                if start_frame := frame_ranged_trait.getStartFrame():
                    instance_data["frameStart"] = start_frame
                    if in_frame := frame_ranged_trait.getInFrame():
                        instance_data["handleStart"] = in_frame - start_frame
                    else:
                        instance_data["handleStart"] = 0

                if end_frame := frame_ranged_trait.getEndFrame():
                    instance_data["frameEnd"] = end_frame
                    if out_frame := frame_ranged_trait.getOutFrame():
                        instance_data["handleEnd"] = end_frame - out_frame
                    else:
                        instance_data["handleEnd"] = 0

            # Colour space metadata.
            ocio_color_managed_trait = mc_traits.color.OCIOColorManagedTrait(entity_traits_data)
            if colorspace := ocio_color_managed_trait.getColorspace():
                instance_data["colorspace"] = colorspace

            # Find all the files.
            file_or_files = []
            if url := mc_traits.content.LocatableContentTrait(entity_traits_data).getLocation():
                # Path to file, or template for a sequence of files.
                path = pathlib.Path(self.__fileUrlPathConverter.pathFromUrl(url))

                if is_workfile:
                    file_or_files = str(path)
                else:
                    # AYON uses "stagingDir" to mean the parent directory that
                    # all the files were written to. This could be the staging
                    # directory supplied by AYON itself (retrieved using
                    # resolve() with a kManagerDriven access mode), but not
                    # necessarily - it's just the directory where the output
                    # artifacts can be found.
                    instance_data["stagingDir"] = str(path.parent)

                    if not frame_ranged_trait.isImbued():
                        file_or_files.append(path.name)
                    else:
                        # If the FrameRangedTrait is imbued, we assume the file
                        # path is a template path that we must fill in with
                        # frame numbers to generate a list of files.
                        # TODO(DF): We further assume that the frame token is
                        #  in the file name(s), rather than in a directory
                        #  name.
                        frame_token = self.__create_frame_token(
                            entity_info.project_name, host_session
                        )
                        if (
                            frame_ranged_trait.getStartFrame() is None
                            or frame_ranged_trait.getEndFrame() is None
                        ):
                            # No frame range is specified, so try a glob of the
                            # file system.
                            glob_path = path.with_name(path.name.replace(frame_token, "*"))
                            file_or_files.extend(
                                f.name for f in glob_path.parent.glob(glob_path.name)
                            )

                        else:
                            # Frame range is specified, so we trust that it's
                            # accurate, and generate a list of files.
                            frame_padding = self.__query_frame_padding(entity_info.project_name)
                            frame_range = range(
                                frame_ranged_trait.getStartFrame(),
                                frame_ranged_trait.getEndFrame() + 1,
                            )

                            file_or_files.extend(
                                path.name.replace(frame_token, f"{frame:0{frame_padding}}")
                                for frame in frame_range
                            )

                    if len(file_or_files) == 1:
                        # AYON will complain if we try to pass a "sequence"
                        # containing a single file. We flag that it's not a
                        # sequence by passing a single string.
                        [file_or_files] = file_or_files

            if not is_workfile:
                # Execute the AYON Pyblish process.
                published_ids = ayon_core_util.publish_representation(
                    entity_info,
                    instance_data,
                    file_or_files,
                    host_session.logger(),
                )
                # Convert IDs to AYON URIs (i.e. entity references).
                uri_response = ayon_api.post(
                    f"projects/{entity_info.project_name}/uris",
                    entityType="representation",
                    ids=published_ids,
                )
                final_entity_ref_str = uri_response.data["uris"][-1]["uri"]
            else:
                # Assume a (in-progress) workfile
                ayon_core_util.publish_workfile(
                    entity_info, entity_identities[idx]["entities"][-1], file_or_files
                )
                entity_info.workfile_name = pathlib.Path(file_or_files).name
                entity_info.representation_name = None
                entity_info.product_name = None
                entity_info.product_type = None
                entity_info.version_name = None
                entity_info.preflight_data = None
                final_entity_ref_str = ayon.build_entity_ref(entity_info)

            success_callback(idx, EntityReference(final_entity_ref_str))

    def getWithRelationship(
        self,
        entity_references: list[EntityReference],
        relationship_traits_data: TraitsData,
        result_trait_set: set[str],
        page_size: int,
        relations_access: access.RelationsAccess,
        context: Context,
        host_session: HostSession,
        success_callback,
        error_callback,
    ) -> None:
        raise NotImplementedError("getWithRelationship is not supported")

    def getWithRelationships(
        self,
        entity_reference: EntityReference,
        relationship_traits_datas: list[TraitsData],
        result_trait_set: set[str],
        page_size: int,
        relations_access: access.RelationsAccess,
        context: Context,
        host_session: HostSession,
        success_callback,
        error_callback,
    ) -> None:
        raise NotImplementedError("getWithRelationships is not supported")

    @staticmethod
    def __query_frame_padding(project_name: str) -> int:
        """
        Get the desired frame padding for the project.
        """
        project_anatomy_response = ayon_api.get(f"projects/{project_name}/anatomy")
        return project_anatomy_response["templates"]["frame_padding"]

    @classmethod
    def __create_frame_token(cls, project_name: str, host_session: HostSession) -> str:
        """
        Construct a frame number wildcard.

        The wildcard should be `{frame}` by default, to satisfy the OpenAssetIO
        standard. But for compatibility, we should check the host application,
        and use the most appropriate token.
        """
        frame_padding = cls.__query_frame_padding(project_name)
        if host_session.host().identifier().startswith("com.foundry"):
            # Nuke/Katana use `#`s (can also use e.g. %04d).
            return "#" * frame_padding
        else:
            # The "OpenAssetIO standard" (subset of fmtlib/Python format strings).
            return f"{{frame:0{frame_padding}}}"
