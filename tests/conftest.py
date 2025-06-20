import os
import pathlib
import uuid

import ayon_api
import pytest
import secrets

import requests
from ayon_api.operations import OperationsSession
from openassetio.log import ConsoleLogger, SeverityFilter
from openassetio.hostApi import HostInterface, Manager, ManagerFactory
from openassetio.pluginSystem import PythonPluginSystemManagerImplementationFactory

from .utils import create_file_list
from dataclasses import dataclass


AYON_SERVER_URL = "http://localhost:5000"
AYON_API_KEY = ""
AYON_BUNDLE_NAME = ""


@dataclass
class IdNamePair(object):
    id: str
    name: str


@dataclass
class ProjectInfo(object):
    project_name: str
    project_code: str
    project_root_folders: dict[str, dict[str, str]]
    folder: IdNamePair
    task: IdNamePair
    task_type: str
    product: IdNamePair
    product_type: str
    version: IdNamePair
    version_attribs: dict[str, str | int]
    representation: IdNamePair
    workfile: IdNamePair
    workfile_type: str
    workfile_path: str


class TestHost(HostInterface):

    def identifier(self):
        return "io.ynput.ayon.openassetio.test.host"

    def displayName(self):
        return "Test OpenAssetIO Host for AYON"


@pytest.fixture(scope="session")
def logger():
    return SeverityFilter(ConsoleLogger())


@pytest.fixture(scope="session")
def ayon_connection_env():
    os.environ["AYON_SERVER_URL"] = os.environ.get("AYON_SERVER_URL", AYON_SERVER_URL)
    os.environ["AYON_API_KEY"] = os.environ.get("AYON_API_KEY", AYON_API_KEY)
    os.environ["AYON_BUNDLE_NAME"] = os.environ.get("AYON_BUNDLE_NAME", AYON_BUNDLE_NAME)

    if not os.environ["AYON_BUNDLE_NAME"]:
        bundles = ayon_api.get_bundles()
        os.environ["AYON_BUNDLE_NAME"] = bundles.get(
            "productionBundle", bundles.get("stagingBundle", bundles["bundles"][0])
        )

    return os.environ["AYON_SERVER_URL"], os.environ["AYON_API_KEY"]


@pytest.fixture(scope="session")
def base_dir():
    """
    Provides the path to the base directory.
    """
    return os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def plugin_path_env(base_dir):
    os.environ["OPENASSETIO_PLUGIN_PATH"] = os.path.join(base_dir, "plugin")
    return os.environ["OPENASSETIO_PLUGIN_PATH"]


@pytest.fixture(scope="session")
def host(base_dir, logger) -> pytest.fixture:
    return TestHost()


@pytest.fixture(scope="session")
def manager_factory(host, logger) -> pytest.fixture:
    factory_impl = PythonPluginSystemManagerImplementationFactory(logger)
    return ManagerFactory(host, factory_impl, logger)


@pytest.fixture(scope="session")
def manager(plugin_path_env, ayon_connection_env, host, manager_factory, logger) -> pytest.fixture:
    instance: Manager = manager_factory.createManager("io.ynput.ayon.openassetio.manager")
    instance.initialize({})  # Settings will be loaded from environment variables.
    return instance


@pytest.fixture(scope="session")
def project(tmp_path_factory, printer_session, ayon_connection_env) -> pytest.fixture:
    server_url, api_key = ayon_connection_env
    _token = secrets.token_hex(5)
    project_name = f"{_token}_test_project"
    project_code = f"TP_{_token[:3]}"
    folder_name = f"t_folder_{secrets.token_hex(3)}"
    product_name = "renderMain"
    version = 1
    task_name = "rendering"
    representation_name = "exr"

    printer_session(f"creating project {project_name}...")
    session = requests.Session()
    session.headers.update({"x-api-key": api_key})

    base_root_dir = str(tmp_path_factory.getbasetemp())

    project_data = {
        "name": project_name,
        "code": project_code,
        "anatomy": {
            "roots": [
                {
                    "name": "work",
                    "windows": f"{base_root_dir}/work",
                    "linux": f"{base_root_dir}/work",
                    "darwin": f"{base_root_dir}/work",
                },
                {
                    "name": "temp",
                    "windows": f"{base_root_dir}/temp",
                    "linux": f"{base_root_dir}/temp",
                    "darwin": f"{base_root_dir}/temp",
                },
            ],
            "templates": {
                "version_padding": 3,
                "version": "v{version:0>{@version_padding}}",
                "frame_padding": 4,
                "frame": "{frame:0>{@frame_padding}}",
                "work": [
                    {
                        "name": "default",
                        "directory": "{root[work]}/{project[name]}/{hierarchy}/{folder[name]}/work/{task[name]}",
                        "file": "{project[code]}_{folder[name]}_{task[name]}_{@version}<_{comment}>.{ext}",
                    }
                ],
                "publish": [
                    {
                        "name": "default",
                        "directory": "{root[work]}/{project[name]}/{hierarchy}/{folder[name]}/publish/{product[type]}/{product[name]}/v{version:0>3}",
                        "file": "{project[code]}_{folder[name]}_{product[name]}_v{version:0>3}<_{output}><.{frame:0>4}><_{udim}>.{ext}",
                    },
                    {
                        "name": "render",
                        "directory": "{root[work]}/{project[name]}/{hierarchy}/{folder[name]}/publish/{product[type]}/{product[name]}/v{version:0>3}",
                        "file": "{project[code]}_{folder[name]}_{product[name]}_v{version:0>3}<_{output}><.{frame:0>4}><_{udim}>.{ext}",
                    },
                ],
                "hero": [
                    {
                        "name": "default",
                        "directory": "{root[work]}/{project[name]}/{hierarchy}/{folder[name]}/publish/{product[type]}/{product[name]}/hero",
                        "file": "{project[code]}_{folder[name]}_{task[name]}_hero<_{comment}>.{ext}",
                    }
                ],
                "staging": [
                    {
                        "name": "publish",
                        "directory": "{root[temp]}/{project[name]}/{hierarchy}/{folder[name]}/staging/{product[type]}/{product[name]}",
                    }
                ],
            },
            "attributes": {
                "fps": 25,
                "resolutionWidth": 1920,
                "resolutionHeight": 1080,
                "pixelAspect": 1,
                "clipIn": 1,
                "clipOut": 1,
                "frameStart": 1001,
                "frameEnd": 1050,
                "handleStart": 0,
                "handleEnd": 0,
                "startDate": "2021-01-01T00:00:00+00:00",
                "endDate": "2021-01-01T00:00:00+00:00",
                "description": "A very nice entity",
                "applications": [],
                "tools": [],
            },
            "folder_types": [{"name": "Asset", "icon": "folder", "original_name": "Asset"}],
            "task_types": [
                {
                    "name": "rendering",
                    "shortName": "rendering",
                    "icon": "",
                    "original_name": "rendering",
                }
            ],
            "statuses": [
                {
                    "name": "not_started",
                    "shortName": "not_started",
                    "state": "not_started",
                    "icon": "",
                    "color": "#cacaca",
                    "original_name": "string",
                }
            ],
        },
        "library": False,
    }
    response = session.post(f"{server_url}/api/projects", json=project_data)
    assert response.status_code == 201

    # Configure staging directory, for resolve()ing with kManagerDriven.
    custom_staging_dir_profiles = [
        {
            "active": True,
            "custom_staging_dir_persistent": False,
            "hosts": [],
            "product_names": [],
            "product_types": ["render", "plate"],
            "task_names": [],
            "task_types": [],
            "template_name": "publish",
        }
    ]

    # Get version of the core addon, for use in REST path.
    bundle_settings = ayon_api.get_bundle_settings(
        bundle_name=os.environ["AYON_BUNDLE_NAME"], project_name=project_name
    )
    bundle_settings_addon_core = next(
        addon for addon in bundle_settings["addons"] if addon["name"] == "core"
    )
    core_addon_version = bundle_settings_addon_core["version"]

    # Fetch and mutate the core addon settings to include the custom
    # staging directory profile.
    project_addons_settings = ayon_api.get_addons_project_settings(project_name)
    core_addon_settings = project_addons_settings["core"]
    core_addon_settings["tools"]["publish"][
        "custom_staging_dir_profiles"
    ] = custom_staging_dir_profiles

    # Update the core addon settings for the project - note that there
    # is currently no equivalent to this in the ayon_api wrapper.
    response = session.post(
        f"{server_url}/api/addons/core/{core_addon_version}/settings/{project_name}",
        json=core_addon_settings,
    )
    assert response.status_code == 204

    # fill project with some data
    # Create a folder
    printer_session(f"filling project {project_name} with data...")
    response = session.post(
        f"{server_url}/api/projects/{project_name}/folders",
        json={
            "name": folder_name,
            "folderType": "Asset",
        },
    )
    assert response.status_code == 201
    folder_id = response.json()["id"]

    # Create a task
    task_type = "rendering"
    response = session.post(
        f"{server_url}/api/projects/{project_name}/tasks",
        json={
            "name": task_name,
            "taskType": task_type,
            "folderId": folder_id,
        },
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    product_type = "render"

    # Create a product
    response = session.post(
        f"{server_url}/api/projects/{project_name}/products",
        json={
            "name": product_name,
            "folderId": folder_id,
            "productType": product_type,
        },
    )
    assert response.status_code == 201
    product_id = response.json()["id"]

    # Create a version

    version_attribs = {
        "frameStart": 1001,
        "frameEnd": 1050,
        "handleStart": 10,
        "handleEnd": 20,
        "colorSpace": "ACEScg",
    }
    response = session.post(
        f"{server_url}/api/projects/{project_name}/versions",
        json={
            "version": version,
            "productId": product_id,
            "taskId": task_id,
            "attrib": version_attribs,
        },
    )
    assert response.status_code == 201
    version_id = response.json()["id"]

    # Create a representation

    context_data = {
        "ext": "exr",
        "root": {"work": project_data["anatomy"]["roots"][0]["windows"]},
        "task": {"name": task_name, "type": "Rendering", "short": "rnd"},
        "user": "Test",
        "folder": {
            "name": folder_name,
        },
        "family": "render",
        "product": {"name": product_name, "type": "render"},
        "project": {"code": project_code, "name": project_name},
        "version": version,
        "username": "Test",
        "hierarchy": "",
        "representation": "exr",
        "frame": "1001",
    }

    file_list = create_file_list(
        project_name, project_code, folder_name, product_name, version, "exr", 1001, 1050
    )

    representation_data = {
        "name": representation_name,
        "versionId": version_id,
        "files": file_list,
        "data": {"context": context_data},
        "attrib": {
            "template": project_data["anatomy"]["templates"]["publish"][0]["directory"]
            + "/"
            + project_data["anatomy"]["templates"]["publish"][0]["file"],  # noqa
        },
    }

    response = session.post(
        f"{server_url}/api/projects/{project_name}/representations", json=representation_data
    )
    assert response.status_code == 201
    representation_id = response.json()["id"]
    printer_session(
        f"Created representation {representation_name} with " f"{len(file_list)} files"
    )

    # Create a workfile

    op_session = OperationsSession()
    workfile_type = "nk"
    workfile_name = f"{project_code}_{folder_name}_{task_type}_v001.{workfile_type}"
    workfile_path = (
        f"{base_root_dir}/work/{project_name}/{folder_name}/work/{task_type}/"
        f"{workfile_name}"
    )
    pathlib.Path(workfile_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(workfile_path).touch()

    workfile_info = {
        "id": uuid.uuid4().hex,
        "path": workfile_path,
        "taskId": task_id,
        "attrib": {"extension": "nk", "description": "A test workfile"},
    }
    op_session.create_entity(project_name, "workfile", workfile_info)
    op_session.commit()

    yield ProjectInfo(
        project_name=project_name,
        project_code=project_code,
        project_root_folders={r["name"]: r for r in project_data["anatomy"]["roots"]},
        folder=IdNamePair(name=folder_name, id=folder_id),
        task=IdNamePair(name=task_name, id=task_id),
        task_type=task_type,
        product=IdNamePair(name=product_name, id=product_id),
        product_type=product_type,
        version=IdNamePair(name=f"v{version:03d}", id=version_id),
        version_attribs=version_attribs,
        representation=IdNamePair(name=representation_name, id=representation_id),
        workfile=IdNamePair(name=workfile_name, id=workfile_info["id"]),
        workfile_type=workfile_type,
        workfile_path=workfile_path,
    )

    # teardown the project
    printer_session(f"tearing down project {project_name}...")
    response = session.delete(f"{server_url}/api/projects/{project_name}")
    assert response.status_code == 204
