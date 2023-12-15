import os
import pytest
import secrets

import requests
from openassetio.log import ConsoleLogger, SeverityFilter
from openassetio.hostApi import HostInterface, Manager, ManagerFactory
from openassetio.pluginSystem import (
    PythonPluginSystemManagerImplementationFactory
)

from .utils import create_file_list
from dataclasses import dataclass


AYON_SERVER_URL = "http://localhost:5000"
AYON_API_KEY = "09fc475e3bae4cc6bbe6942c231c17b3"


@dataclass
class IdNamePair(object):
    id: str
    name: str


@dataclass
class ProjectInfo(object):
    project_name: str
    project_code: str
    project_root_folders: dict[str, str]
    folder: IdNamePair
    task: IdNamePair
    product: IdNamePair
    version: IdNamePair
    representation: IdNamePair


class TestHost(HostInterface):

    def identifier(self):
        return "io.ynput.ayon.openassetio.test.host"
    def displayName(self):
        return "Test OpenAssetIO Host for AYON"


@pytest.fixture
def logger():
    return SeverityFilter(ConsoleLogger())


@pytest.fixture
def ayon_connection_env():
    os.environ["AYON_SERVER_URL"] = os.environ.get("AYON_SERVER_URL", AYON_SERVER_URL)
    os.environ["AYON_API_KEY"] = os.environ.get("AYON_API_KEY", AYON_API_KEY)
    return os.environ["AYON_SERVER_URL"], os.environ["AYON_API_KEY"]


@pytest.fixture
def base_dir():
    """
    Provides the path to the base directory.
    """
    return os.path.dirname(os.path.dirname(__file__))


@pytest.fixture
def plugin_path_env(base_dir):
    os.environ["OPENASSETIO_PLUGIN_PATH"] = base_dir
    return os.environ["OPENASSETIO_PLUGIN_PATH"]


@pytest.fixture
def host(base_dir, logger) -> pytest.fixture:
    return TestHost()


@pytest.fixture
def manager_factory(host, logger) -> pytest.fixture:
    factory_impl = PythonPluginSystemManagerImplementationFactory(logger)
    return ManagerFactory(host, factory_impl, logger)


@pytest.fixture
def manager(plugin_path_env, ayon_connection_env, host, manager_factory, logger) -> pytest.fixture:
    return manager_factory.createManager("io.ynput.ayon.openassetio.manager")


@pytest.fixture
def project(printer, ayon_connection_env) -> pytest.fixture:
    server_url, api_key = ayon_connection_env
    _token = secrets.token_hex(5)
    project_name = f"{_token}_test_project"
    project_code = f"TP_{_token[:3]}"
    folder_name = f"t_folder_{secrets.token_hex(3)}"
    product_name = "renderMain"
    version = 1
    task_name = "rendering"
    representation_name = "exr"

    printer(f"creating project {project_name}...")
    session = requests.Session()
    session.headers.update({'x-api-key': api_key})

    project_data = {
      "name": project_name,
      "code": project_code,
      "anatomy": {
        "roots": [
          {
            "name": "work",
            "windows": "C:/projects",
            "linux": "/mnt/share/projects",
            "darwin": "/Volumes/projects"
          }
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
              "file": "{project[code]}_{folder[name]}_{task[name]}_{@version}<_{comment}>.{ext}"
            }
          ],
          "publish": [
            {
              "name": "default",
              "directory": "{root[work]}/{project[name]}/{hierarchy}/{folder[name]}/publish/{product[type]}/{product[name]}/v{version:0>3}",
              "file": "{project[code]}_{folder[name]}_{product[name]}_v{version:0>3}<_{output}><.{frame:0>4}><_{udim}>.{ext}"
            }
          ],
          "hero": [
            {
              "name": "default",
              "directory": "{root[work]}/{project[name]}/{hierarchy}/{folder[name]}/publish/{product[type]}/{product[name]}/hero",
              "file": "{project[code]}_{folder[name]}_{task[name]}_hero<_{comment}>.{ext}"
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
          "tools": []
        },
        "folder_types": [
          {
            "name": "Asset",
            "icon": "folder",
            "original_name": "Asset"
          }
        ],
        "task_types": [
          {
            "name": "rendering",
            "shortName": "rendering",
            "icon": "",
            "original_name": "rendering"
          }
        ],
        "statuses": [
          {
            "name": "not_started",
            "shortName": "not_started",
            "state": "not_started",
            "icon": "",
            "color": "#cacaca",
            "original_name": "string"
          }
        ]
      },
      "library": False
    }
    response = session.post(
        f"{server_url}/api/projects", json=project_data)
    assert response.status_code == 201

    # fill project with some data
    # Create a folder
    printer(f"filling project {project_name} with data...")
    response = session.post(
        f"{server_url}/api/projects/{project_name}/folders", json={
        "name": folder_name,
        "folderType": "Asset",
    })
    assert response.status_code == 201
    folder_id = response.json()["id"]

    # Create a task
    response = session.post(
        f"{server_url}/api/projects/{project_name}/tasks", json={
            "name": task_name,
            "taskType": "rendering",
            "folderId": folder_id,
        })
    assert response.status_code == 201
    task_id = response.json()["id"]

    # Create a product
    response = session.post(
        f"{server_url}/api/projects/{project_name}/products", json={
        "name": product_name,
        "folderId": folder_id,
        "productType": "render",
    })
    assert response.status_code == 201
    product_id = response.json()["id"]

    # Create a version
    response = session.post(
        f"{server_url}/api/projects/{project_name}/versions", json={
        "version": version,
        "productId": product_id,
        "taskId": task_id,
    })
    assert response.status_code == 201
    version_id = response.json()["id"]

    # Create a representation

    context_data = {
        "ext": "exr",
        "root": {
            "work": project_data["anatomy"]["roots"][0]["windows"]
        },
        "task": {
            "name": task_name,
            "type": "Rendering",
            "short": "rnd"
        },
        "user": "Test",
        "folder": {
            "name": folder_name,
        },
        "family": "render",
        "product": {
            "name": product_name,
            "type": "render"
        },
        "project": {
            "code": project_code,
            "name": project_name
        },
        "version": version,
        "username": "Test",
        "hierarchy": "",
        "representation": "exr"
    }

    file_list = create_file_list(project_name, project_code, folder_name,
                                 product_name, version, "exr",
                                 1001, 1050)
    representation_data = {
        "name": representation_name,
        "versionId": version_id,
        "files": file_list,
        "data": {
            "context": context_data
        },
        "attrib": {
            "frameStart": 1001,
            "frameEnd": 1050,
            "template": project_data["anatomy"]["templates"]["publish"][0]["directory"] + "/" + project_data["anatomy"]["templates"]["publish"][0]["file"],  # noqa
        }
    }

    response = session.post(
        f"{server_url}/api/projects/{project_name}/representations",
        json=representation_data)
    assert response.status_code == 201
    representation_id = response.json()["id"]
    printer(
        f"Created representation {representation_name} with "
        f"{len(file_list)} files"
    )

    yield ProjectInfo(
        project_name=project_name,
        project_code=project_code,
        project_root_folders=project_data["anatomy"]["roots"][0],
        folder=IdNamePair(name=folder_name, id=folder_id),
        task=IdNamePair(name=task_name, id=task_id),
        product=IdNamePair(name=product_name, id=product_id),
        version=IdNamePair(name=f"v{version:03d}", id=version_id),
        representation=IdNamePair(
            name=representation_name, id=representation_id),
    )

    # teardown the project
    printer(f"tearing down project {project_name}...")
    response = session.delete(
        f"{server_url}/api/projects/{project_name}")
    assert response.status_code == 204
