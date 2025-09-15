"""AYON config and utils.

Utilities available without (i.e. prior to) importing the ayon_core library.
"""
from __future__ import annotations

import json
import os
import pathlib
import platform
import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union
from urllib.parse import parse_qs, urlencode, urlparse

import ayon_api
import platformdirs
import requests

if TYPE_CHECKING:
    from ayon_api.typing import BundlesInfoDict

NAME_REGEX = r"^[a-zA-Z0-9_][a-zA-Z0-9_\.\-]*[a-zA-Z0-9_]$"
# Required AYON config.
SERVER_URL_KEY = "AYON_SERVER_URL"
SERVER_API_KEY = "AYON_API_KEY"
SERVER_BUNDLE_NAME_KEY = "AYON_BUNDLE_NAME"  # For project anatomy.
# Optional AYON config.
# For ayon_core library (optional).
CLIENT_LAUNCHER_STORAGE_DIR_KEY = "AYON_LAUNCHER_STORAGE_DIR"
PROJECT_NAME_KEY = "AYON_PROJECT_NAME"
PATH_NAME_KEY = "AYON_PATH_NAME"
TASK_NAME_KEY = "AYON_TASK_NAME"

env_var_settings = [
    SERVER_URL_KEY,
    SERVER_API_KEY,
    SERVER_BUNDLE_NAME_KEY,
    CLIENT_LAUNCHER_STORAGE_DIR_KEY,
    PROJECT_NAME_KEY,
]


def bootstrap_ayon_core(
        bundle_name: str, bundles_info: BundlesInfoDict) -> None:
    """Appends the AYON core addon and dependency directories to sys.path.

    E.g. by default on linux, `~/.local/share/AYON/addons/core_1.3.2` and
    `~/.local/share/AYON/dependency_packages/ayon_2502101346_linux-rocky9.zip/dependencies`.

    This allows us to make use of the utilities in ayon_core, rather than
    reinventing them.

    Args:
        bundle_name (str): The name of the bundle to use.
        bundles_info (BundlesInfoDict): The bundles info dictionary, as
            obtained from the AYON server.

    Raises:
        RuntimeError: If the bundle is not found, or if the required
            directories do not exist.

    """
    ayon_storage_dir = pathlib.Path(
        os.environ.get(
            CLIENT_LAUNCHER_STORAGE_DIR_KEY,
            platformdirs.user_data_dir("AYON", "Ynput")
        )
    )

    bundle = next(
        (
            bundle for bundle in bundles_info["bundles"]
            if bundle["name"] == bundle_name
        ),
        None,
    )
    if bundle is None:
        msg = (f"Bundle '{bundle_name}' not found. "
               "Please check your AYON_BUNDLE_NAME setting.")
        raise RuntimeError(msg)

    ayon_addons_dir = ayon_storage_dir / "addons"
    if not ayon_addons_dir.is_dir():
        msg = (f"AYON addons directory not found at '{ayon_addons_dir}'. "
               "Please ensure you have run the AYON launcher at least once.")
        raise RuntimeError(msg)

    core_addon_dir = ayon_addons_dir / f"core_{bundle['addons']['core']}"
    if not core_addon_dir.is_dir():
        msg = (f"Core addon directory not found at '{core_addon_dir}'. "
               "Please ensure you have run the AYON launcher at least once.")
        raise RuntimeError(msg)

    core_addon_vendor_dir = core_addon_dir / "ayon_core" / "vendor" / "python"

    ayon_dependency_packages_dir = ayon_storage_dir / "dependency_packages"
    if not ayon_dependency_packages_dir.is_dir():
        msg = (f"AYON dependency packages directory not found at "
               f"'{ayon_dependency_packages_dir}'. "
               "Please ensure you have run the AYON launcher at least once.")
        raise RuntimeError(msg)

    ayon_dependency_packages_dir /= bundle["dependencyPackages"][sys.platform]
    ayon_dependency_packages_dir /= "dependencies"
    if not ayon_dependency_packages_dir.is_dir():
        msg = (f"AYON dependency packages for platform '{sys.platform}' "
               f"not found at '{ayon_dependency_packages_dir}'. "
               "Please ensure you have run the AYON launcher at least once.")
        raise RuntimeError(msg)

    # Add the core addon directory to sys.path if not already present
    if str(core_addon_dir) not in sys.path:
        sys.path.append(str(core_addon_dir))

    # Sundry utils for UI delegate usage.
    if str(core_addon_vendor_dir) not in sys.path:
        sys.path.append(str(core_addon_vendor_dir))

    # Add the dependency packages directory to sys.path if not already present.
    if ayon_dependency_packages_dir not in sys.path:
        sys.path.append(ayon_dependency_packages_dir)

    from . import ayon_core_util

    ayon_core_util.bootstrap_pyblish()


def query_site_id() -> str:
    """Returns the AYON site id for the current session.

    The combination of hostname and platform is enough to determine the
    site id.

    Returns:
        str: The site id for the current session.

    Raises:
        ServerError: If the AYON server returns an error.

    """
    hostname = platform.node()
    system_platform = platform.system()

    response = ayon_api.get(
        "system/sites", hostname=hostname, platform=system_platform.lower())
    if response.status_code != requests.codes.ok:
        msg = (f"AYON server returned an error - "
               f"{response.status_code} - {response.text}")
        raise ServerError(msg)

    return response.data[-1]["id"]


@dataclass
class EntityInfo:
    """Identifies an AYON product."""

    uri: str
    project_name: str
    path: Optional[str] = None
    product_name: Optional[str] = None
    product_type: Optional[str] = None
    task_name: Optional[str] = None
    version_name: Optional[str] = None
    representation_name: Optional[str] = None
    workfile_name: Optional[str] = None
    variant_name: Optional[str] = None
    comment: Optional[str] = None
    preflight_data: Union[dict[str, Union[str, int, float, bool]], None] = None


@dataclass
class Relation:
    """The definition of a relationship to other entities.

    The nature of the relation is a traits data dict, accompanied by
    one or more `ProductInfo`.
    """

    traits: dict[str, dict]
    product_infos: list[EntityInfo]


@dataclass
class Representation:
    """Represents an AYON representation.

    TODO: Move and enhance this definition to AYON API
    """

    traits: dict[str, dict]
    relations: list[Relation]


def make_default_settings() -> dict:
    """Returns the default settings for the AYON plugin."""
    return {
        SERVER_URL_KEY: os.getenv(SERVER_URL_KEY, "http://localhost:5000"),
        SERVER_API_KEY: os.getenv(SERVER_API_KEY),
        SERVER_BUNDLE_NAME_KEY: os.getenv(SERVER_BUNDLE_NAME_KEY),
    }


def validate_settings(settings: dict) -> None:
    """Validate the supplied settings.

    Args:
        settings (dict): The settings to validate.

    Raises:
        KeyError: If a required setting is missing.
        KeyError: If an unknown setting is present.

    """
    defaults = make_default_settings()

    if SERVER_API_KEY not in settings:
        msg = (f"Missing AYON API Key in Settings '{SERVER_API_KEY}'")
        raise KeyError(msg)

    if SERVER_URL_KEY not in settings:
        msg = (f"Missing AYON Server URL in Settings '{SERVER_URL_KEY}'")
        raise KeyError(msg)

    if SERVER_BUNDLE_NAME_KEY not in settings:
        msg = (
            "Missing AYON Server Bundle Name "
            f"in Settings '{SERVER_BUNDLE_NAME_KEY}'")
        raise KeyError(msg)

    for key in settings:
        if key not in defaults and key not in env_var_settings:
            mag = f"Unknown setting '{key}'"
            raise KeyError(mag)

'''
def management_policy(trait_set: set[str], access: str, library: dict) -> dict:
    """Returns a management policy for the given trait set and access level.

    Args:
        trait_set (set[str]): The set of traits to match.
        access (str): The access level to match.
        library (dict): The library data.

    Returns:
        dict: The management policy, or an empty dict if no policy is found.
    """
    return {}
'''

def parse_entity_ref(entity_ref: str) -> EntityInfo:  # noqa: C901
    """Parses a URI identifying an AYON entity.

    Args:
        entity_ref (str): The entity reference to parse.

    Returns:
        EntityInfo: The parsed entity information.

    Raises:
        MalformedAyonReferenceError: If the entity reference is malformed.

    """
    project_name: str
    path: Optional[str]
    product_name: Optional[str]
    product_type: Optional[str]
    task_name: Optional[str]
    version_name: Optional[str]
    representation_name: Optional[str]
    workfile_name: Optional[str]
    variant_name: Optional[str]
    comment: Optional[str]

    parsed_uri = urlparse(entity_ref)

    if not parsed_uri.scheme or not parsed_uri.netloc:
        msg = "Missing scheme or project name"
        raise MalformedAyonReferenceError(msg, entity_ref)

    if parsed_uri.scheme not in {"ayon", "ayon+entity"}:
        msg = f"Invalid scheme: {parsed_uri.scheme}"
        raise MalformedAyonReferenceError(msg, entity_ref)

    project_name = parsed_uri.netloc
    name_validator = re.compile(NAME_REGEX)

    if not name_validator.match(project_name):
        msg = f"Invalid project name: {project_name}"
        raise MalformedAyonReferenceError(msg, entity_ref)

    path = parsed_uri.path

    qs: dict[str, Any] = parse_qs(parsed_uri.query)

    product_name = qs.get("product", [None])[0]
    if product_name is not None:
        _validate_name(product_name)

    product_type = qs.get("product_type", [None])[0]
    if product_type is not None:
        _validate_name(product_type)

    task_name = qs.get("task", [None])[0]
    if task_name is not None:
        _validate_name(task_name)

    version_name = qs.get("version", [None])[0]
    if version_name is not None:
        _validate_name(version_name)

    representation_name = qs.get("representation", [None])[0]
    if representation_name is not None:
        _validate_name(representation_name)

    workfile_name = qs.get("workfile", [None])[0]
    if workfile_name is not None:
        _validate_name(workfile_name)

    variant_name = qs.get("variant", [None])[0]
    if workfile_name is not None:
        _validate_name(variant_name)

    comment = qs.get("comment", [None])[0]

    # Data gathered by preflight(), encoded in the working entity
    # reference that it returns.
    preflight_data = qs.get("preflight", [None])[0]
    if preflight_data is not None:
        preflight_data = json.loads(preflight_data)

    return EntityInfo(
        uri=entity_ref,
        project_name=project_name,
        path=path,
        product_name=product_name,
        product_type=product_type,
        task_name=task_name,
        version_name=version_name,
        representation_name=representation_name,
        workfile_name=workfile_name,
        preflight_data=preflight_data,
        variant_name=variant_name,
        comment=comment,
    )


def build_entity_ref(entity_info: EntityInfo) -> str:  # noqa: C901
    """Builds a URI identifying an AYON entity.

    Args:
        entity_info (EntityInfo): The entity information to build the
            reference from.

    Returns:
        str: The built entity reference.

    Raises:
        ValueError: If the entity_info.path is None.

    """
    if entity_info.path is None:
        msg = "EntityInfo.path is required to build a reference"
        raise ValueError(msg)
    path = entity_info.path.lstrip("/")
    ref_string = f"ayon+entity://{entity_info.project_name}/{path}"

    qs = []

    if entity_info.product_name is not None:
        qs.append(f"product={entity_info.product_name}")

    if entity_info.product_type is not None:
        qs.append(f"product_type={entity_info.product_type}")

    if entity_info.task_name is not None:
        qs.append(f"task={entity_info.task_name}")

    if entity_info.workfile_name is not None:
        qs.append(f"workfile={entity_info.workfile_name}")

    if entity_info.representation_name is not None:
        qs.append(f"representation={entity_info.representation_name}")

    if entity_info.version_name is not None:
        qs.append(f"version={entity_info.version_name}")

    if entity_info.variant_name is not None:
        qs.append(f"variant={entity_info.variant_name}")

    if entity_info.preflight_data is not None:
        # Data gathered by preflight(), encoded in the working entity
        # reference that it returns.
        preflight_data = json.dumps(entity_info.preflight_data)
        preflight_data = urlencode({"preflight": preflight_data})
        qs.append(preflight_data)

    if entity_info.comment is not None:
        comment_data = urlencode({"comment": entity_info.comment})
        qs.append(comment_data)

    if qs:
        ref_string += f"?{'&'.join(qs)}"

    return ref_string


def _dict_has_traits(data: dict, traits: dict) -> bool:
    """Finds if the given traits are present in the supplied dict-of-dicts.

    Determines if the supplied dict-of-dicts contains the given traits.
    A match is when all trait ids are present as top level keys in the
    dict, and any set trait properties exist as child keys with the same
    value. Additional keys at either level in the data dict are ignored.

    Args:
        data (dict): The dict-of-dicts to check.
        traits (dict): The traits to check for.

    Returns:
        bool: True if the traits are present, False otherwise.

    """
    for trait_id, trait_data in traits.items():
        if trait_id not in data:
            return False
        for property_key, value in trait_data.items():
            if data[trait_id].get(property_key) != value:
                return False
    return True


def _entity_has_trait_set(
        entity_data: Representation, trait_set: set[str]) -> bool:
    """Determine if the entity has the trait ids within its trait set.

    Args:
        entity_data (Representation): The entity to check.
        trait_set (Set[str]): The trait ids to check for.

    Returns:
        bool: True if the entity has all the traits, False otherwise.

    """
    return all(trait in entity_data.traits for trait in trait_set)


def _validate_name(name: str) -> None:
    if name is None:
        return
    if name == "*":
        return
    name_validator = re.compile(NAME_REGEX)
    if not name_validator.match(name):
        msg = f"Invalid name: {name}"
        raise ValueError(msg)


class UnknownAyonEntityError(RuntimeError):
    """A reference to a non-existent entity in the library.

    Exception raised when an entity reference cannot be resolved.
    """
    def __init__(self, entity_info: EntityInfo):
        """Constructor."""
        super().__init__(f"Entity '{entity_info.uri}' not found")


class MalformedAyonReferenceError(RuntimeError):
    """A malformed entity reference.

    Exception raised when an entity reference is malformed.
    """
    def __init__(self, message: str, reference: str):
        """Constructor."""
        super().__init__(
            f"Malformed entity reference: {message} '{reference}'")


class ServerError(Exception):
    """An error response from the AYON server."""
