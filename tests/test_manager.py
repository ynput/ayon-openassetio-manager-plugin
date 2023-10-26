import operator
import os
import platform

from .conftest import ProjectInfo
import openassetio_mediacreation.traits as mc_traits
import openassetio
import openassetio.access


def test_manager_discovery(plugin_path_env, ayon_connection_env, manager_factory, printer):
    printer(
        "testing if plugin can be discovered "
        f"in {os.getenv('OPENASSETIO_PLUGIN_PATH')}")
    managers = manager_factory.availableManagers()
    assert "io.ynput.ayon.openassetio.manager" in managers.keys()


def test_manager_creation(manager):
    assert manager is not None


def test_manager_identity(manager):
    assert manager.identifier() == \
           "io.ynput.ayon.openassetio.manager.interface"


def test_entity_reference_valid(manager, printer):
    printer("testing if entity reference is valid based on prefix")
    # manager: openassetio.hostApi.Manager
    assert manager.isEntityReferenceString(
        "ayon+entity://asset/1234")
    assert not manager.isEntityReferenceString(
        "ayon://foo/bar/baz")
    assert not manager.isEntityReferenceString(
        "http://foo.bar.baz")


def test_entity_reference_exists(project, manager):
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
            )
        ],
        context,
        lambda idx, result: operator.setitem(results, idx, result),
        raise_batch_element_error)

    assert results[0] is True
    assert results[1] is False


def test_resolve(project, manager):
    project: ProjectInfo
    context = manager.createContext()

    result = manager.resolve(
        entityReference=manager.createEntityReference(
            f"ayon+entity://{project.project_name}/"
            f"{project.folder.name}?product={project.product.name}&"
            f"version={project.version.name}&"
            f"representation={project.representation.name}"
        ),
        traitSet={mc_traits.content.LocatableContentTrait.kId},
        resolveAccess=openassetio.access.ResolveAccess.kRead,
        context=context)

    locatable_content = mc_traits.content.LocatableContentTrait(result)

    assert locatable_content.isImbued()

    project_url_root = project.project_root_folders[platform.system().lower()]
    # Even Windows paths should start with "/" when it comes to `file:`
    # URLs.
    if not project_url_root.startswith("/"):
        project_url_root = f"/{project_url_root}"

    assert locatable_content.getLocation() == (
            f"file://{project_url_root}/"
            f"{project.project_name}/{project.folder.name}/publish/render/"
            f"{project.product.name}/{project.version.name}/"
            f"{project.project_code}_{project.folder.name}_"
            f"{project.product.name}_{project.version.name}.exr"
        )


def raise_batch_element_error(idx: int, error: openassetio.BatchElementError):
    """
    Utility to work around current lack of exception-throwing
    convenience signatures in some OpenAssetIO methods.
    """
    raise openassetio.BatchElementException(idx, error)