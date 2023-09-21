import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set, Union
from urllib.parse import parse_qs, urlparse

NAME_REGEX = r"^[a-zA-Z0-9_][a-zA-Z0-9_\.\-]*[a-zA-Z0-9_]$"
SERVER_URL_KEY = "AYON_SERVER_URL"
SERVER_API_KEY = "AYON_API_KEY"


@dataclass
class EntityInfo:
    """Identifies an AYON product."""

    uri: str
    project_name: str
    path: Union[str, None]
    product_name: Union[str, None]
    task_name: Union[str, None]
    version_name: Union[str, None]
    representation_name: Union[str, None]
    workfile_name: Union[str, None]


@dataclass
class Relation:
    """The definition of a relationship to other entities. The nature of
    the relation is a traits data dict, accompanied by one or more
    `ProductInfo`.
    """

    traits: Dict[str, Dict]
    product_infos: List[EntityInfo]


@dataclass
class Representation:
    """Represents an AYON representation.

    TODO: Move and enhance this definition to AYON API
    """

    traits: Dict[str, dict]
    relations: List[Relation]


def make_default_settings() -> dict:
    """Returns the default settings for the AYON plugin."""
    return {
        SERVER_URL_KEY: os.getenv("AYON_SERVER_URL", "https://localhost:5000"),
        SERVER_API_KEY: os.getenv("AYON_API_KEY")
    }


def validate_settings(settings: dict):
    """Validate the supplied settings.

    Args:
        settings (dict): The settings to validate.

    Raises:
        KeyError: If a required setting is missing.
        KeyError: If an unknown setting is present.
    """

    defaults = make_default_settings()

    if SERVER_API_KEY not in settings:
        raise KeyError(f"Missing AYON API Key in Settings '{SERVER_API_KEY}'")

    if SERVER_URL_KEY not in settings:
        raise KeyError(
            f"Missing AYON Server URL in Settings '{SERVER_URL_KEY}'")

    for key in settings:
        if key not in defaults:
            raise KeyError(f"Unknown setting '{key}'")


def management_policy(trait_set: Set[str], access: str, library: dict) -> dict:
    return {}


def parse_entity_ref(entity_ref: str) -> EntityInfo:

    project_name: str
    path: Union[str, None]
    product_name: Union[str, None]
    task_name: Union[str, None]
    version_name: Union[str, None]
    representation_name: Union[str, None]
    workfile_name: Union[str, None]

    parsed_uri = urlparse(entity_ref)
    assert parsed_uri.scheme in [
        "ayon",
        "ayon+entity",
    ], f"Invalid scheme: {parsed_uri.scheme}"

    project_name = parsed_uri.netloc
    name_validator = re.compile(NAME_REGEX)
    assert name_validator.match(
        project_name), f"Invalid project name: {project_name}"

    path = parsed_uri.path.strip("/") or None

    qs: dict[str, Any] = parse_qs(parsed_uri.query)

    product_name = qs.get("product", [None])[0]
    if product_name is not None:
        _validate_name(product_name)

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

    return EntityInfo(
        uri=entity_ref,
        project_name=project_name,
        path=path,
        product_name=product_name,
        task_name=task_name,
        version_name=version_name,
        representation_name=representation_name,
        workfile_name=workfile_name,
    )


def _dict_has_traits(data: dict, traits: dict) -> bool:
    """
    Determines if the supplied dict-of-dicts contains the given traits.
    A match is when all trait ids are present as top level keys in the
    dict, and any set trait properties exist as child keys with the same
    value. Additional keys at either level in the data dict are ignored.
    """
    for trait_id, trait_data in traits.items():
        if trait_id not in data:
            return False
        for property_key, value in trait_data.items():
            if data[trait_id].get(property_key) != value:
                return False
    return True


def _entity_has_trait_set(
        entity_data: Representation, trait_set: Set[str]) -> bool:
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
        raise ValueError(f"Invalid name: {name}")


class UnknownAyonEntity(RuntimeError):
    """
    An exception raised for a reference to a non-existent entity in the
    library.
    """

    def __init__(self, entity_info: EntityInfo):
        super().__init__(f"Entity '{entity_info.uri}' not found")


class MalformedAyonReference(RuntimeError):
    def __init__(self, message, reference: str):
        super().__init__(
            f"Malformed entity reference: {message} '{reference}'")
