import os
from .conftest import ProjectInfo
import openassetio_mediacreation.traits as mc_traits
import openassetio


def test_manager_discovery(plugin_path_env, manager_factory, printer):
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
    result = manager.entityExists(
        [
            (
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?product={project.product.name}&"
                f"version={project.version.name}&"
                f"representation={project.representation.name}"
            ),
            (
                f"ayon+entity://{project.project_name}/"
                f"{project.folder.name}?product={project.product.name}&"
                f"version={project.version.name}&"
                f"representation=NOT_EXISTING",
            )
        ], None)

    assert result[0] is True
    assert result[1] is False


def test_resolve(project, manager):
    project: ProjectInfo
    context = manager.createContext()

    result = manager.resolve(entityReferences=[
            openassetio.EntityReference(
                (
                    f"ayon+entity://{project.project_name}/"
                    f"{project.folder.name}?product={project.product.name}&"
                    f"version={project.version.name}&"
                    f"representation={project.representation.name}"
                )),
        ],
        traitSet={mc_traits.content.LocatableContentTrait.kId},
        context=context)

    # result: List[openassetio.TraitsData]
    assert result[0].hasTrait(mc_traits.content.LocatableContentTrait.kId)
    assert result[0].getTraitProperty(
        mc_traits.content.LocatableContentTrait.kId,
        "location") == os.path.normpath(
            f"C:/projects/{project.project_name}/"
            f"{project.folder.name}/publish/render/"
            f"{project.product.name}/{project.version.name}/"
            f"{project.project_code}_{project.folder.name}_"
            f"{project.product.name}_{project.version.name}.exr"
        )
