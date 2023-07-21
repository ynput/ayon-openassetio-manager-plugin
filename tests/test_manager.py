import os
from .conftest import ProjectInfo
import openassetio


def test_manager_discovery(plugin_path_env, manager_factory, printer):
    printer(
        "testing if plugin can be discovered "
        f"in {os.getenv('OPENASSETIO_PLUGIN_PATH')}")
    managers = manager_factory.availableManagers()
    assert "io.ynput.ayon.openassetio.manager" in managers.keys()


def test_manager_creation(manager, printer):
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


def test_entity_reference_exists(project, manager, printer):

    project: ProjectInfo
    result = manager.entityExists(
        [
            f"ayon+entity://{project.project_name}/{project.folder.name}?product={project.product.name}&version={project.version.name}&representation={project.representation.name}",
            f"ayon+entity://{project.project_name}/{project.folder.name}?product={project.product.name}&version={project.version.name}&representation=NOT_EXISTING",
        ], None)
    printer(result)
    assert result[0] is True
    assert result[1] is False


def test_resolve(project, manager, printer):
    project: ProjectInfo
    context = manager.createContext()
    context.access = openassetio.hostApi.AccessMode.kRead
    context.retention = openassetio.hostApi.RetentionMode.kTemporary

    result = manager.resolve(
        [
            f"ayon+entity://{project.project_name}/{project.folder.name}?product={project.product.name}&version={project.version.name}&representation={project.representation.name}",
        ],
        context=context)
    # {project[code]}_{folder[name]}_{product[name]}_v{version:0>3}<_{output}><.{frame:0>4}><_{udim}>.{ext}"
    assert result[0] == f"C:/projects/{project.project_name}/{project.folder.name}/publish/render/"\
                        f"{project.product.name}/{project.version.name}/"\
                        f"{project.project_code}_{project.folder.name}_{project.product.name}_{project.version.name}.exr"
