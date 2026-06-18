"""Provides access to useful functionality in ayon_core.

Assumes ayon_core is importable, i.e. available on sys.path.
"""
from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING, Any, Optional

import ayon_api
import ayon_core
import pyblish.api
import requests
from ayon_core.host import HostBase
from ayon_core.host.interfaces import ILoadHost, IPublishHost, IWorkfileHost
from ayon_core.pipeline import register_host, registered_host
from ayon_core.pipeline.anatomy.anatomy import Anatomy
from ayon_core.pipeline.create.context import CreateContext
from ayon_core.pipeline.create.creator_plugins import Creator
from ayon_core.settings import get_project_settings
from ayon_core.tools.workfiles.control import BaseWorkfileController
from openassetio.log import LoggerInterface

from . import ayon

if TYPE_CHECKING:
    from ayon_core.pipeline.create import CreatedInstance

_all__ = [
    "bootstrap_pyblish",
    "query_identity_for_entity_refs",
    "query_product_name_for_entity",
    "query_staging_dir_for_entity",
    "publish_representation",
    "publish_workfile",
    "query_workfile_path",
    "OpenAssetIOHost",
]


def bootstrap_pyblish() -> None:
    """Configure pyblish to use the default core AYON publish plugins."""
    # Register the default core pyblish publish plugins.
    plugins_dir = (
            pathlib.Path(ayon_core.__file__).parent / "plugins" / "publish"
    ).resolve()
    pyblish.api.register_plugin_path(str(plugins_dir))
    # Required so that currentFile is added to the context by the
    # CollectCurrentShellFile pyblish plugin, which is required by
    # IntegrateAsset.
    pyblish.api.register_host("shell")


def query_identity_for_entity_refs(  # noqa: C901, PLR0912, PLR0914
        entity_references: list[str]) -> list[dict]:
    """Get identities for the given entity references.

    Query the database IDs of the AYON entities associated with the given
    entity references.

    Typically, this will return IDs for the representation, version,
    product, task and workfile objects associated with each entity,
    depending on the information available within the entity reference.

    Note that multiple sets of IDs may be returned for a single entity
    reference, if there are implicit or explicit wildcards (e.g. if a
    version is not specified, then all versions of the product will be
    returned).

    TODO (antirotor): Refactor this a little bit since the bug
        https://github.com/ynput/ayon-backend/pull/671 is fixed.

    Args:
        entity_references (list[str]): List of AYON entity references.

    Returns:
        list[dict]: List of entity identities, one per entity reference.

    Raises:
        RuntimeError: If the AYON server returns an error.

    """
    workfile_idx_and_refs = []
    non_workfile_idx_and_refs = []

    for idx, ref in enumerate(entity_references):
        ref_str = str(ref)
        if "workfile=" in ref_str:
            workfile_idx_and_refs.append((idx, ref_str))
        else:
            non_workfile_idx_and_refs.append((idx, ref_str))

    result: list[dict[str, Any]] = [{}] * len(entity_references)

    if non_workfile_idx_and_refs:
        non_workfile_idxs, non_workfile_refs = zip(*non_workfile_idx_and_refs)
        # Task and workfile cannot be queried with product and representation -
        # the server will error. However, task may legitimately be encoded in
        # the entity reference for publishing purposes, i.e. to compute a
        # product name. So we must strip it.
        entity_infos = [
            ayon.parse_entity_ref(ref)
            for ref in non_workfile_refs
        ]
        for entity_info in entity_infos:
            entity_info.task_name = None
        non_workfile_refs = [
            ayon.build_entity_ref(entity_info)
            for entity_info in entity_infos
        ]

        response: ayon_api.server_api.RestApiResponse = ayon_api.post(
            "resolve", resolveRoots=True, uris=non_workfile_refs
        )

        if response.status_code != requests.codes.ok:
            msg = (
                f"Failed to resolve entity references {non_workfile_refs} - "
                f"{response.status_code} - {response.text}"
            )

            raise RuntimeError(msg)

        # TODO(DF): data may have an "error" key, which should be handled.
        non_workfile_entity_identities = response.data

        for idx, entity_identity in zip(
                non_workfile_idxs,
                non_workfile_entity_identities,
            ):
            result[idx] = entity_identity

    # Work around URIs for workfiles not being accepted:
    # https://github.com/ynput/ayon-core/issues/1359
    for idx, ref in workfile_idx_and_refs:
        entity_identity = {}
        result[idx] = {"entities": [entity_identity]}
        entity_info = ayon.parse_entity_ref(str(ref))

        folder_data = ayon_api.get_folder_by_path(
            entity_info.project_name, entity_info.path, fields=["id"]
        )
        if folder_data is None:
            continue

        if folder_id := folder_data.get("id"):
            entity_identity["folderId"] = folder_id

            task_data = ayon_api.get_task_by_name(
                entity_info.project_name,
                folder_id,
                entity_info.task_name,
                fields=["id"]
            )
            if task_data is None:
                continue
            if task_id := task_data.get("id"):
                entity_identity["taskId"] = task_id

                workfiles_info = ayon_api.get_workfiles_info(
                    entity_info.project_name,
                    task_ids=[task_id],
                    fields=["id", "name", "path"],
                )

                if entity_info.workfile_name is not None:
                    workfile_info: dict[str, Any] = next(
                        (
                            wf for wf in workfiles_info
                            if wf["name"] == entity_info.workfile_name
                        ),
                        {},
                    )
                else:
                    # If no workfile name is specified,
                    # just take the first one.
                    workfile_info = next(workfiles_info, {})

                if workfile_id := workfile_info.get("id"):
                    entity_identity["workfileId"] = workfile_id

                if workfile_path := workfile_info.get("path"):
                    workfile_path = Anatomy(
                        entity_info.project_name).path_remapper(workfile_path)

                    entity_identity["filePath"] = workfile_path

    # If multiple entities are returned for a single entity reference,
    # and they all have a versionId and representationId (i.e. versioned
    # files), then filter to just the latest version.
    for entity_identity in result:
        entities = entity_identity.get("entities", [])
        if len(entities) > 1:
            if all(
                entity.get("versionId") and entity.get("representationId") for entity in entities
            ):
                version_nums = [
                    ayon_api.get_version_by_id(
                        entity["projectName"], entity["versionId"], fields=["version"]
                    )["version"]
                    for entity in entities
                ]
                latest_version_and_entity = max(zip(version_nums, entities))
                latest_entity = latest_version_and_entity[1]
                entity_identity["entities"] = [latest_entity]

    return result


def query_product_name_for_entity(entity_info: ayon.EntityInfo) -> str:
    """Query the product name for the given entity.

    Args:
        entity_info (ayon.EntityInfo): The entity information.

    Returns:
        str: The product name.

    """
    creator = _creator_for_entity(entity_info)

    project_name = entity_info.project_name
    host_name = creator.create_context.host_name
    folder_entity = ayon_api.get_folder_by_path(project_name, entity_info.path)
    task_entity = (
        folder_entity
        and entity_info.task_name
        and ayon_api.get_task_by_name(
            project_name, folder_entity["id"], entity_info.task_name)
    )

    return creator.get_product_name(
        project_name,
        folder_entity,
        task_entity,
        entity_info.variant_name or creator.default_variant,
        host_name=host_name,
    )


def query_staging_dir_for_entity(entity_info: ayon.EntityInfo) -> str:
    """Query the staging directory for the given entity.

    Args:
        entity_info (ayon.EntityInfo): The entity information.

    Returns:
        str: The staging directory path.

    """
    creator = _creator_for_entity(entity_info)

    created_instance = creator.create(
        entity_info.product_name,
        {
            "folderPath": entity_info.path,
            "task": entity_info.task_name,
            "variant": entity_info.variant_name or creator.default_variant,
        },
        {},
    )

    return creator.get_staging_dir(created_instance).directory


def publish_representation(
    entity_info: ayon.EntityInfo,
    instance_data: dict,
    file_or_files: str | list[str],
    logger: LoggerInterface,
) -> list[str]:
    """Execute AYON's pyblish publishing process.

    Use the default core AYON pyblish plugins running against
    a temporary "host" created only for this publish.

    Args:
        entity_info (ayon.EntityInfo): The entity information.
        instance_data (dict): The instance data for the representation
            to publish.
        file_or_files (str | list[str]): List of file paths to include
            in the representation, or a single file path.
        logger (LoggerInterface): Logger to use for logging.

    Returns:
        list[str]: List of published representation IDs.

    Raises:
        RuntimeError: If the publish process fails.

    """
    pyblish_ctx = pyblish.api.Context()

    pyblish_ctx.data["projectName"] = entity_info.project_name

    optional_representation_data_keys = [
        # TODO(DF): representation frame range vs. instance.data
        #   (version) frame range?
        "frameStart",
        "frameEnd",
        "stagingDir",
    ]
    representation_data: dict[str, Any] = {
        "tags": [],
        "name": entity_info.representation_name,
        "ext": entity_info.representation_name,
        "files": file_or_files,
    }
    for key in optional_representation_data_keys:
        if key in instance_data:
            representation_data[key] = instance_data[key]

    if "colorspace" in instance_data:
        representation_data["colorspaceData"] = {
            "colorspace": instance_data["colorspace"]
        }

    thumbnailSource = file_or_files[0] if isinstance(
        file_or_files, list) else file_or_files
    if stagingDir := representation_data.get("stagingDir"):
        thumbnailSource = os.path.join(stagingDir, thumbnailSource)

    instance = pyblish_ctx.create_instance(entity_info.product_name)
    instance.data.update(
        {
            "publish": True,
            "label": entity_info.product_name,
            "name": entity_info.product_name,
            "folderPath": entity_info.path,
            "task": entity_info.task_name,
            "productName": entity_info.product_name,
            "productType": entity_info.product_type,
            "family": entity_info.product_type,
            "families": [entity_info.product_type],
            "comment": entity_info.comment,
            "representations": [representation_data],
            "thumbnailSource": thumbnailSource,
            "transientData": {},
        }
    )
    optional_instance_data_keys = [
        "frameStart",
        "frameEnd",
        "step",
        "handleEnd",
        "handleStart",
    ]
    for key in optional_instance_data_keys:
        if key in instance_data:
            instance.data[key] = instance_data[key]

    # TODO(DF): This is a blunt instrument to force a colour space
    #  update on the version, which might be naughty.
    if "colorspace" in instance_data:
        instance.data["versionData"] = {
            "colorSpace": instance_data["colorspace"]
        }

    # Temporarily override the registered host object with our temporary
    # host created just for this publish. Host is required by pyblish
    # plugins e.g. get_outdated_containers() called ultimately by
    # ValidateOutdatedContainers.
    prev_host = registered_host()
    register_host(OpenAssetIOHost(entity_info))
    errors = []
    try:
        # Execute the pyblish publish process, which will iterate through
        # all the discovered publish plugins in priority order. Plugins can
        # have implicit dependencies via the mutable context object that is
        # provided to each plugin in turn. Plugins can then have side
        # effects such as moving files, generating thumbnails and updating
        # the database.
        for result in pyblish.util.publish_iter(context=pyblish_ctx):
            if result["error"]:
                error = "Failed {plugin.__name__}: {error}".format(**result)
                logger.warning(error)
                logger.debug(result["error"].formatted_traceback)
                errors.append(error)

        published_instance = pyblish_ctx[0]
        published_representations = published_instance.data.get(
            "published_representations"
        )
        if not published_representations:
            msg = (
                "No representations were published. Ensure that at least one"
                " publish plugin was executed. Errors:\n"
                + (
                    "\n".join(errors)
                    if errors
                    else "No representations published."
                )
            )
            raise RuntimeError(msg)

        return list(published_representations.keys())
    finally:
        # Restore the previous host object, if any.
        register_host(prev_host)


def publish_workfile(
    entity_info: ayon.EntityInfo,
    task_id: str,
    workfile_path: str,
    note: str = "",
) -> None:
    """Execute the publish process for a workfile.

    Registers the workfile in AYON, associating it with a project/folder/task.

    Args:
        entity_info (ayon.EntityInfo): The entity information.
        task_id (str): Task to associate with workfile.
        workfile_path (str): The path to the workfile to register.
        note (str): An optional note to associate with the workfile.

    """
    _OpenAssetIOWorkfileController(OpenAssetIOHost(entity_info)).save_workfile_info(
        task_id, workfile_path, comment=note
    )


def query_workfile_path(
    entity_info: ayon.EntityInfo,
    entity_identity: dict[str, str],
    comment: str = "",
    *,
    use_last_version: bool = False,
) -> pathlib.Path:
    """Construct a (new) workfile path for the given entity.

    Args:
        entity_info (ayon.EntityInfo): The entity information.
        entity_identity (dict[str, str]): The entity identity containing at
            least the folderId and taskId.
        use_last_version (bool): Whether to use the last version number in
            the constructed path.
        comment (str): An optional comment to associate with the workfile.

    Returns:
        str: The constructed workfile path.

    Raises:
        ValueError: If the entity info does not contain a workfile name.

    """
    controller = _OpenAssetIOWorkfileController(OpenAssetIOHost(entity_info))
    save_as_data = controller.get_workarea_save_as_data(
        entity_identity["folderId"], entity_identity["taskId"]
    )

    if entity_info.workfile_name is None:
        msg = (
            "Cannot construct workfile path without a workfile name in the"
            " entity info."
        )
        raise ValueError(msg)

    filename, extension = os.path.splitext(entity_info.workfile_name)
    if not extension:
        extension = filename

    workarea_file_path_result = controller.fill_workarea_filepath(
        entity_identity["folderId"],
        entity_identity["taskId"],
        extension,
        use_last_version,
        save_as_data["last_version"],
        comment,
    )
    return workarea_file_path_result.filepath


def _creator_for_entity(entity_info: ayon.EntityInfo) -> Creator:
    """Construct a Creator for the given entity information.

    A bespoke CreateContext and Host is also created for the given entity info
    and associated with the Creator.

    Args:
        entity_info (ayon.EntityInfo): The entity information.

    Returns:
        Creator: The Creator instance.

    Raises:
        ValueError: If the entity info does not contain a product type.

    """
    project_settings = get_project_settings(entity_info.project_name)
    create_context = CreateContext(
        OpenAssetIOHost(entity_info),
        headless=True,
        reset=False,
        discover_publish_plugins=False,
    )
    create_context.reset_current_context()
    if entity_info.product_type is None:
        msg = "Entity info must contain a product type."
        raise ValueError(msg)
    return _OpenAssetIOCreator(
        entity_info.product_type, project_settings,
        create_context, headless=True
    )


class _OpenAssetIOWorkfileController(BaseWorkfileController):
    """Convenience functions for dealing with workfiles in AYON."""
    def __init__(self, host: OpenAssetIOHost):
        super().__init__(host)
        self.reset()  # Copy settings from `host`.


class _OpenAssetIOCreator(Creator):
    """AYON OpenAssetIO Creator.

    A barebones Creator implementation just to surface its handy utilities.
    """
    def __init__(self, product_type: str, *args, **kwargs):  # noqa: ANN002, ANN003
        self.__product_type = product_type
        super().__init__(*args, **kwargs)

    # @override
    @property
    def product_type(self) -> str:
        return self.__product_type

    def create(
        self, product_name: str, instance_data: dict, pre_create_data: dict
    ) -> CreatedInstance:
        return self._create_instance(product_name, instance_data)

    def collect_instances(self) -> list[CreatedInstance]:
        """Collect instances that can be created by this Creator."""
        raise NotImplementedError

    def remove_instances(self, instances: list[CreatedInstance]) -> None:
        """Remove the given instances.

        Args:
            instances (list[CreatedInstance]): Instances to remove.

        """
        raise NotImplementedError

    def update_instances(self, update_list: list[CreatedInstance]) -> None:
        raise NotImplementedError


class OpenAssetIOHost(HostBase, IPublishHost, ILoadHost, IWorkfileHost):
    """AYON OpenAssetIO Host.

    Usually, there is a single Host object per application, abstracting the
    application-specific functionality required by other more generic AYON
    functions/classes. It's analogous to a significantly more developed
    OpenAssetIO `HostInterface`.

    Here, we abuse this mechanism by creating a temporary barebones Host, which
    is associated with a particular entity, whenever we need access to an AYON
    utility that requires a Host in order to function.
    """

    def __init__(self, entity_info: ayon.EntityInfo):
        """Constructor."""
        super().__init__()
        self.__entity_info = entity_info

    @property
    def name(self) -> str:
        """Name of the host application."""
        return "OpenAssetIO"

    def get_current_project_name(self) -> str:
        """Get the current project name.

        Returns:
            str: The current project name.

        """
        return self.__entity_info.project_name

    def get_current_folder_path(self) -> str:
        """Get the current folder path.

        Returns:
            str: The current folder path.
        """
        return self.__entity_info.path or ""

    def get_current_task_name(self) -> str:
        """Get the current task name.

        Returns:
            str: The current task name.

        """
        return self.__entity_info.task_name or ""

    def get_context_data(self) -> dict[str, Any]:
        """Get context data for the current context.

        Returns:
            dict[str, Any]: The context data.

        """
        return {}

    def update_context_data(self, data: dict, changes: dict) -> None:
        """Update the context data.

        Args:
            data (dict): The context data to update.
            changes (dict): The changes to apply to the context data.

        """
        raise NotImplementedError

    def get_containers(self) -> list:
        """Get the containers in the current scene.

        Required by  get_outdated_containers() called ultimately by
        `ValidateOutdatedContainers`.

        Returns:
            list: The containers in the current scene.

        """
        return []

    def get_workfile_extensions(self) -> list[str]:
        """Get the workfile extensions for the current application.

        Returns:
            list[str]: The workfile extensions.

        """
        if self.__entity_info.workfile_name is None:
            # TODO(DF): Currently just a dummy to prevent exceptions. Perhaps
            #  default list should be an exhaustive list?
            return [".unknown"]
        filename, extension = os.path.splitext(
            self.__entity_info.workfile_name)
        if not extension:
            extension = filename
        if not extension.startswith("."):
            extension = f".{extension}"
        return [extension]

    def save_workfile(self, dst_path: Optional[str] = None) -> None:
        """Save the current workfile to the given path.

        Args:
            dst_path (Optional[str]): The destination path to save
                the workfile to.

        """
        raise NotImplementedError

    def open_workfile(self, filepath: str) -> None:
        """Open the given workfile."""
        raise NotImplementedError

    def get_current_workfile(self) -> Optional[str]:
        """Get the current workfile path.

        E.g. required by CreateContext.reset_current_context()

        Returns:
            Optional[str]: The current workfile path.

        """
        return None
