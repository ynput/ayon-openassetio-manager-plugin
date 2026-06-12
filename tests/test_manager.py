"""Tests for the Ayon OpenAssetIO Manager implementation."""
import json
import operator
import os
import pathlib
import platform
import urllib.parse

import openassetio
import openassetio.access
import openassetio_mediacreation.specifications as mc_specs
import openassetio_mediacreation.traits as mc_traits
from openassetio import access
from openassetio.errors import BatchElementError
from openassetio.hostApi import Manager
from openassetio.trait import TraitsData
from openassetio.utils import FileUrlPathConverter

from .conftest import ProjectInfo


def test_manager_discovery(
        plugin_path_env,
        ayon_connection_env,
        manager_factory,
        printer) -> None:
    """Test that the Ayon OpenAssetIO Manager plugin can be discovered."""
    printer(
        "testing if plugin can be discovered "
        f"in {os.getenv('OPENASSETIO_PLUGIN_PATH')}")

    managers = manager_factory.availableManagers()
    assert "io.ynput.ayon.openassetio.manager" in managers


def test_manager_creation(manager) -> None:
    """Test that the Ayon OpenAssetIO Manager can be created."""
    assert manager is not None


def test_manager_identity(manager) -> None:
    """Test that the Ayon OpenAssetIO Manager has the correct identity."""
    assert manager.identifier() == "io.ynput.ayon.openassetio.manager.interface"


def test_entity_reference_valid(manager, printer) -> None:
    printer("testing if entity reference is valid based on prefix")
    # manager: openassetio.hostApi.Manager
    assert manager.isEntityReferenceString("ayon+entity://asset/1234")
    assert not manager.isEntityReferenceString("ayon://foo/bar/baz")
    assert not manager.isEntityReferenceString("http://foo.bar.baz")


class TestManagementPolicy:
    """Tests for the Ayon OpenAssetIO Manager managementPolicy method."""
    def test_when_read_unsupported_then_not_managed(
            self, project: ProjectInfo, manager: Manager) -> None:
        context = manager.createContext()
        trait_set = {
            mc_traits.threeDimensional.IESProfileTrait.kId,
        }

        policy_traits_data = manager.managementPolicy(
            trait_set, access.PolicyAccess.kRead, context
        )

        assert policy_traits_data.traitSet() == set()

    def test_when_read_supported_then_managed(
            self, project: ProjectInfo, manager: Manager) -> None:
        context = manager.createContext()
        trait_set = {
            mc_traits.content.LocatableContentTrait.kId,
            mc_traits.timeDomain.FrameRangedTrait.kId,
            mc_traits.color.OCIOColorManagedTrait.kId,
            # Arbitrary unsupported trait with potential properties:
            mc_traits.threeDimensional.IESProfileTrait.kId,
        }

        policy_traits_data = manager.managementPolicy(
            trait_set, access.PolicyAccess.kRead, context
        )

        assert policy_traits_data.traitSet() == {
            mc_traits.content.LocatableContentTrait.kId,
            mc_traits.timeDomain.FrameRangedTrait.kId,
            mc_traits.color.OCIOColorManagedTrait.kId,
            mc_traits.managementPolicy.ManagedTrait.kId,
        }

    def test_when_manager_driven_unsupported_then_not_managed(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()
        trait_set = {
            mc_traits.timeDomain.FrameRangedTrait.kId,
        }

        policy_traits_data = manager.managementPolicy(
            trait_set, access.PolicyAccess.kManagerDriven, context
        )

        assert policy_traits_data.traitSet() == set()

    def test_when_manager_driven_supported_then_managed(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()
        trait_set = {
            mc_traits.content.LocatableContentTrait.kId,
        }

        policy_traits_data = manager.managementPolicy(
            trait_set, access.PolicyAccess.kManagerDriven, context
        )

        assert policy_traits_data.traitSet() == {
            mc_traits.content.LocatableContentTrait.kId,
            mc_traits.managementPolicy.ManagedTrait.kId,
        }

    def test_when_required_for_publishing_unsupported_then_not_managed(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()
        trait_set = {
            mc_traits.timeDomain.FrameRangedTrait.kId,
        }

        policy_traits_data = manager.managementPolicy(
            trait_set, access.PolicyAccess.kRequired, context
        )

        assert policy_traits_data.traitSet() == set()

    def test_when_required_for_publishing_supported_then_managed(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()
        trait_set = {
            mc_traits.content.LocatableContentTrait.kId,
        }

        policy_traits_data = manager.managementPolicy(
            trait_set, access.PolicyAccess.kRequired, context
        )

        assert policy_traits_data.traitSet() == {
            mc_traits.content.LocatableContentTrait.kId,
            mc_traits.managementPolicy.ManagedTrait.kId,
        }


def test_entity_reference_exists(project, manager) -> None:
    project: ProjectInfo
    context = manager.createContext()

    # TODO(DF): OpenAssetIO beta.1 is lacking convenience overloads for
    #  entityExists, so we must use the lower-level callback-based
    #  signature, for now.

    results = [None, None]

    manager.entityExists(
        [
            manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?product={project.product.name}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?product={project.product.name}&"
                f"version={project.version.name}&"
                f"representation=NOT_EXISTING",
            ),
        ],
        context,
        lambda idx, result: operator.setitem(results, idx, result),
        raise_batch_element_error,
    )

    assert results[0] is True
    assert results[1] is False


class TestResolve:
    """Tests for the Ayon OpenAssetIO Manager resolve method."""
    def test_when_resolving_existing_image_sequence_then_available_fields_returned(
        self, project: ProjectInfo, manager
    ) -> None:
        context = manager.createContext()

        trait_set = {
            mc_traits.content.LocatableContentTrait.kId,
            mc_traits.timeDomain.FrameRangedTrait.kId,
            mc_traits.color.OCIOColorManagedTrait.kId,
            # Arbitrary unsupported trait with potential properties:
            mc_traits.threeDimensional.IESProfileTrait.kId,
        }

        result = manager.resolve(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"product={project.product.name}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            traitSet=trait_set,
            resolveAccess=openassetio.access.ResolveAccess.kRead,
            context=context,
        )

        locatable_content_trait = mc_traits.content.LocatableContentTrait(
            result)
        frame_ranged_trait = mc_traits.timeDomain.FrameRangedTrait(
            result)
        ocio_color_managed_trait = mc_traits.color.OCIOColorManagedTrait(
            result)
        ies_profile_trait = mc_traits.threeDimensional.IESProfileTrait(
            result)

        assert locatable_content_trait.isImbued()
        assert frame_ranged_trait.isImbued()
        assert ocio_color_managed_trait.isImbued()
        assert not ies_profile_trait.isImbued()

        assert (
            frame_ranged_trait.getStartFrame()
            == project.version_attribs["frameStart"] - project.version_attribs["handleStart"]
        )
        assert (
            frame_ranged_trait.getEndFrame()
            == project.version_attribs["frameEnd"] + project.version_attribs["handleEnd"]
        )
        assert frame_ranged_trait.getInFrame() == project.version_attribs["frameStart"]
        assert frame_ranged_trait.getOutFrame() == project.version_attribs["frameEnd"]

        assert ocio_color_managed_trait.getColorspace() == project.version_attribs["colorSpace"]

        project_url_root = project.project_root_folders["work"][platform.system().lower()]
        # Even Windows paths should start with "/" when it comes to `file:`
        # URLs.
        if not project_url_root.startswith("/"):
            project_url_root = f"/{project_url_root}"

        assert locatable_content_trait.getLocation() == (
            f"file://{project_url_root}/"
            f"{project.project_name}/{project.folder.name}/publish/"
            f"{project.product_type}/{project.product.name}/{project.version.name}/"
            f"{project.project_code}_{project.folder.name}_"
            f"{project.product.name}_{project.version.name}."
            "%7Bframe%3A04%7D"  # {frame:04} URL-encoded
            ".exr"
        )

    def test_when_resolving_existing_workfile_then_available_fields_returned(
        self, project: ProjectInfo, manager
    ) -> None:
        context = manager.createContext()

        trait_set = {
            mc_traits.content.LocatableContentTrait.kId,
            # Arbitrary unsupported trait with potential properties:
            mc_traits.timeDomain.FrameRangedTrait.kId,
        }

        result = manager.resolve(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/{project.folder.name}?"
                f"task={project.task.name}&"
                f"workfile={project.workfile.name}"
            ),
            traitSet=trait_set,
            resolveAccess=openassetio.access.ResolveAccess.kRead,
            context=context,
        )

        locatable_content_trait = mc_traits.content.LocatableContentTrait(result)
        frame_ranged_trait = mc_traits.timeDomain.FrameRangedTrait(result)

        assert locatable_content_trait.isImbued()
        assert not frame_ranged_trait.isImbued()

        # Even Windows paths should start with "/" when it comes to `file:`
        # URLs.
        workfile_path = project.workfile_path
        if not workfile_path.startswith("/"):
            workfile_path = f"/{workfile_path}"

        assert locatable_content_trait.getLocation() == f"file://{workfile_path}"


class TestPreflight:
    """Tests for the Ayon OpenAssetIO Manager preflight method."""
    def test_when_publishing_to_representation_then_representation_ref_returned(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()

        traits_hint = (
            mc_specs.twoDimensional.PlanarBitmapImageResourceSpecification.create().traitsData()
        )

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"product={project.product.name}&"
                f"product_type={project.product_type}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        expected_ref = (
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?"
            f"product={project.product.name}&"
            f"product_type={project.product_type}&"
            f"representation={project.representation.name}&"
            "preflight=%7B%7D"  # No encoded data in this case.
        )

        assert str(working_ref) == expected_ref

    def test_when_publishing_with_metadata_to_representation_then_representation_ref_returned(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()

        traits_hint = (
            mc_specs.twoDimensional.PlanarBitmapImageResourceSpecification.create().traitsData()
        )
        mc_traits.timeDomain.FrameRangedTrait.imbueTo(traits_hint)
        expected_color_space = "ACEScg"
        mc_traits.color.OCIOColorManagedTrait(traits_hint).setColorspace(expected_color_space)

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"product={project.product.name}&"
                f"product_type={project.product_type}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        expected_ref_prefix = (
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?"
            f"product={project.product.name}&"
            f"product_type={project.product_type}&"
            f"representation={project.representation.name}&"
            "preflight="
        )

        assert str(working_ref).startswith(expected_ref_prefix)
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(str(working_ref)).query)
        assert qs.get("preflight") is not None
        assert json.loads(qs["preflight"][0]) == {
            "colorspace": expected_color_space,
            "frame_ranged": True,
        }

    def test_when_publishing_to_workfile_then_workfile_ref_returned(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()

        traits_hint = mc_specs.application.WorkfileSpecification.create().traitsData()

        expected_workfile_type = "mytype"

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"task={project.task.name}&"
                f"workfile={expected_workfile_type}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        expected_ref = (
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?"
            f"product_type=workfile&"
            f"task={project.task.name}&"
            f"workfile={expected_workfile_type}&"
            "preflight=%7B%7D"  # No encoded data in this case.
        )

        assert str(working_ref) == expected_ref


class TestResolveForManagerDriven:
    def test_when_publishing_to_existing_representation_then_staging_path_returned(
        self, project: ProjectInfo, manager
    ) -> None:
        # setup

        context = manager.createContext()

        traits_hint = (
            mc_specs.twoDimensional.PlanarBitmapImageResourceSpecification.create().traitsData()
        )
        mc_traits.timeDomain.FrameRangedTrait.imbueTo(traits_hint)

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"product={project.product.name}&"
                f"product_type={project.product_type}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        # action

        result = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        # confirm

        locatable_content = mc_traits.content.LocatableContentTrait(result)

        assert locatable_content.isImbued()

        temp_root = project.project_root_folders["temp"][platform.system().lower()]
        # Even Windows paths should start with "/" when it comes to `file:`
        # URLs.
        if not temp_root.startswith("/"):
            temp_root = f"/{temp_root}"

        assert locatable_content.getLocation() == (
            f"file://{temp_root}/"
            f"{project.project_name}/{project.folder.name}/staging/"
            f"{project.product_type}/{project.product.name}/"
            f"{project.product.name}."
            "%7Bframe%3A04%7D"  # {frame:04} URL-encoded
            ".exr"
        )
        file_path = pathlib.Path(
            FileUrlPathConverter().pathFromUrl(locatable_content.getLocation())
        )
        assert file_path.parent.is_dir()

    def test_when_publishing_to_workfile_then_working_path_returned(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()

        traits_hint = mc_specs.application.WorkfileSpecification.create().traitsData()

        expected_workfile_type = "mytype"

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"task={project.task.name}&"
                f"workfile={expected_workfile_type}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        # action

        result = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        # confirm

        locatable_content = mc_traits.content.LocatableContentTrait(result)

        assert locatable_content.isImbued()

        work_root = project.project_root_folders["work"][platform.system().lower()]
        # Even Windows paths should start with "/" when it comes to `file:`
        # URLs.
        if not work_root.startswith("/"):
            work_root = f"/{work_root}"

        assert locatable_content.getLocation() == (
            f"file://{work_root}/"
            f"{project.project_name}/"
            f"{project.folder.name}/work/"
            f"{project.task_type}/"
            f"{project.project_code}_{project.folder.name}_{project.task_type}_v001"
            f".{expected_workfile_type}"
        )
        file_template_path = pathlib.Path(
            FileUrlPathConverter().pathFromUrl(locatable_content.getLocation())
        )
        assert file_template_path.parent.is_dir()

    def test_when_publishing_to_existing_workfile_type_then_workfile_file_version_updated(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()

        traits_hint = mc_specs.application.WorkfileSpecification.create().traitsData()

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"task={project.task.name}&"
                f"workfile={project.workfile_type}"  # Type rather than name.
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        # action

        result = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        # confirm

        locatable_content = mc_traits.content.LocatableContentTrait(result)

        assert locatable_content.isImbued()

        file_path = FileUrlPathConverter().pathFromUrl(locatable_content.getLocation())
        assert file_path == project.workfile_path.replace("v001", "v002")

    def test_when_publishing_to_existing_workfile_then_workfile_name_file_version_updated(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        context = manager.createContext()

        traits_hint = mc_specs.application.WorkfileSpecification.create().traitsData()

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"task={project.task.name}&"
                # Name rather than type. Note: only extension is used - file
                # name is generated from a template.
                f"workfile={project.workfile.name}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        # action

        result = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        # confirm

        locatable_content = mc_traits.content.LocatableContentTrait(result)

        assert locatable_content.isImbued()

        file_path = FileUrlPathConverter().pathFromUrl(locatable_content.getLocation())
        assert file_path == project.workfile_path.replace("v001", "v002")


class TestRegister:
    """Tests for the Ayon OpenAssetIO Manager register method."""
    def test_when_publishing_to_existing_representation_then_creates_new_version(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        # setup

        context = manager.createContext()

        traits_hint = (
            mc_specs.twoDimensional.PlanarBitmapImageResourceSpecification.create().traitsData()
        )
        mc_traits.timeDomain.FrameRangedTrait.imbueTo(traits_hint)

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"product={project.product.name}&"
                f"product_type={project.product_type}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        manager_driven_traits_data = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        manager_driven_locatable_content_trait = mc_traits.content.LocatableContentTrait(
            manager_driven_traits_data
        )

        asset_template_path = FileUrlPathConverter().pathFromUrl(
            manager_driven_locatable_content_trait.getLocation()
        )

        asset_path = asset_template_path.format(frame=1)
        pathlib.Path(asset_path).touch()
        asset_path = asset_template_path.format(frame=2)
        pathlib.Path(asset_path).touch()

        traits_data = TraitsData(traits_hint)
        mc_traits.content.LocatableContentTrait(traits_data).setLocation(
            manager_driven_locatable_content_trait.getLocation()
        )

        # action

        final_ref = manager.register(
            entityReference=working_ref,
            entityTraitsData=traits_data,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        #  confirm
        expected_final_ref = manager.createEntityReference(
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?product={project.product.name}&"
            f"version=v002&"
            f"representation={project.representation.name}"
        )

        assert final_ref == expected_final_ref

    def test_when_publishing_to_entirely_new_representation_then_creates_new_hierarchy(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        # setup

        context = manager.createContext()

        traits_hint = (
            mc_specs.twoDimensional.PlanarBitmapImageResourceSpecification.create().traitsData()
        )
        mc_traits.timeDomain.FrameRangedTrait.imbueTo(traits_hint)

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                "product=plateMain&"
                "product_type=plate&"
                "representation=blah"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        manager_driven_traits_data = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        manager_driven_locatable_content_trait = mc_traits.content.LocatableContentTrait(
            manager_driven_traits_data
        )

        asset_template_path = FileUrlPathConverter().pathFromUrl(
            manager_driven_locatable_content_trait.getLocation()
        )

        asset_path = asset_template_path.format(frame=1)
        pathlib.Path(asset_path).touch()
        asset_path = asset_template_path.format(frame=2)
        pathlib.Path(asset_path).touch()

        traits_data = TraitsData(traits_hint)
        mc_traits.content.LocatableContentTrait(traits_data).setLocation(
            manager_driven_locatable_content_trait.getLocation()
        )

        # action

        final_ref = manager.register(
            entityReference=working_ref,
            entityTraitsData=traits_data,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        #  confirm

        expected_final_ref = manager.createEntityReference(
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?"
            "product=plateMain&"
            "version=v001&"
            "representation=blah"
        )

        assert final_ref == expected_final_ref

        final_traits_data = manager.resolve(
            expected_final_ref,
            {mc_traits.content.LocatableContentTrait.kId},
            access.ResolveAccess.kRead,
            context,
        )

        final_uri = mc_traits.content.LocatableContentTrait(final_traits_data).getLocation()

        final_path = FileUrlPathConverter().pathFromUrl(final_uri)
        assert pathlib.Path(final_path).parent.is_dir()
        assert pathlib.Path(final_path.format(frame=1)).is_file()
        assert pathlib.Path(final_path.format(frame=2)).is_file()
        assert pathlib.Path(final_path.format(frame=1)) != pathlib.Path(final_path.format(frame=2))

    def test_when_publishing_to_new_workfile_then_creates_new_workfile_entry(
        self, project: ProjectInfo, manager: Manager
    ) -> None:
        # setup
        context = manager.createContext()

        traits_hint = mc_specs.application.WorkfileSpecification.create().traitsData()

        workfile_type = "mytype"

        working_ref = manager.preflight(
            entityReference=manager.createEntityReference(
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?"
                f"task={project.task.name}&"
                f"product_type=workfile&"
                f"workfile={workfile_type}"
            ),
            traitsHint=traits_hint,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        manager_driven_traits_data = manager.resolve(
            entityReference=working_ref,
            traitSet={mc_traits.content.LocatableContentTrait.kId},
            resolveAccess=openassetio.access.ResolveAccess.kManagerDriven,
            context=context,
        )

        manager_driven_locatable_content_trait = mc_traits.content.LocatableContentTrait(
            manager_driven_traits_data
        )
        manager_driven_url = manager_driven_locatable_content_trait.getLocation()
        manager_driven_path = FileUrlPathConverter().pathFromUrl(manager_driven_url)
        pathlib.Path(manager_driven_path).touch()

        # action

        traits_data = TraitsData(traits_hint)
        mc_traits.content.LocatableContentTrait(traits_data).setLocation(
            manager_driven_locatable_content_trait.getLocation()
        )

        final_ref = manager.register(
            entityReference=working_ref,
            entityTraitsData=traits_data,
            publishAccess=access.PublishingAccess.kWrite,
            context=context,
        )

        # confirm

        expected_final_ref = manager.createEntityReference(
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?"
            f"task={project.task.name}&"
            f"workfile={project.project_code}_{project.folder.name}_{project.task_type}_v001"
            f".{workfile_type}"
        )

        assert final_ref == expected_final_ref

        final_traits_data = manager.resolve(
            final_ref,
            {mc_traits.content.LocatableContentTrait.kId},
            access.ResolveAccess.kRead,
            context,
        )

        final_url = mc_traits.content.LocatableContentTrait(final_traits_data).getLocation()

        # For workfiles, register() just registers the existing path, it
        # doesn't move the files out of the workfile directory.
        assert final_url == manager_driven_url


def raise_batch_element_error(idx: int, error: BatchElementError) -> None:
    """Raise the given BatchElementError.

    Utility to work around current lack of exception-throwing
    convenience signatures in some OpenAssetIO methods.

    Args:
        idx (int): The index of the element that caused the error.
        error (BatchElementError): The error to raise.

    """
    raise error
