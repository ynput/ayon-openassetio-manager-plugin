from __future__ import annotations

import platform
from pathlib import Path
from timeit import default_timer as timer
# import os
from typing import Any, List, Set

# from . import ayon_traits
import openassetio
import openassetio_mediacreation.traits as mc_traits
import requests
from openassetio import (
    BatchElementError,
    EntityReference,
    TraitsData,
    constants
)
from openassetio.exceptions import PluginError
from openassetio.managerApi import ManagerInterface
from openassetio_mediacreation.traits.managementPolicy import ManagedTrait
from openassetio.access import ResolveAccess, PolicyAccess

from . import ayon

__all__ = [
    "AyonOpenAssetIOManagerInterface",
]


class AyonOpenAssetIOManagerInterface(ManagerInterface):
    """
    This class exposes the Basic Asset Library through the OpenAssetIO
    ManagerInterface.
    """

    __reference_prefix = "ayon+entity://"

    def __init__(self):
        super().__init__()
        self.__settings = ayon.make_default_settings()
        self.__session = requests.Session()
        self.__session.headers.update({'x-api-key': self.__settings[ayon.SERVER_API_KEY]})
        self.__session.headers.update({'x-ayon-site-id': self._get_site_id()})

    def _get_site_id(self) -> str:
        """Returns the AYON site id for the current session.

        The combination of hostname and platform is enough to determine the
        site id.

        Returns:
            str: The site id for the current session.
        """
        hostname = platform.node()
        system_platform = platform.system()

        response = self.__session.get((
            f"{self.__settings[ayon.SERVER_URL_KEY]}/api/system/sites?"
            f"hostname={hostname}&platform={system_platform.lower()}")
        )
        return response.json()[0]["id"]

    def identifier(self):
        return "io.ynput.ayon.openassetio.manager.interface"

    def displayName(self):
        # Deliberately includes unicode chars to test string handling
        return "AYON OpenAssetIO Manager"

    def info(self):
        return {constants.kField_EntityReferencesMatchPrefix: self.__reference_prefix}  # noqa: E400

    def settings(self, host_session: Any) -> dict:
        return self.__settings.copy()

    def initialize(self, managerSettings, hostSession) -> None:
        self.__settings.update(managerSettings)
        ayon.validate_settings(self.__settings)

        # add headers with the site id to the session
        self.__session.headers.update({'x-ayon-site-id': self._get_site_id()})

    def managementPolicy(self,
                         traitSets: List[Set[str]],
                         access,
                         context: openassetio.Context,
                         hostSession: openassetio.managerApi.HostSession) -> List[openassetio.TraitsData]:  # noqa: E501,N802, N803
        policies = []
        for trait_set in traitSets:
            traits_data = TraitsData()
            if context.isForRead() and mc_traits.content.LocatableContentTrait.kId in trait_set:  # noqa: E501
                ManagedTrait.imbueTo(traits_data)
                mc_traits.content.LocatableContentTrait.imbueTo(traits_data)
            policies.append(traits_data)
        return policies

    def isEntityReferenceString(self, some_string, host_session):
        return some_string.startswith(self.__reference_prefix)

    def entityExists(self, entityRefs, context, hostSession):
        try:
            start = timer()
            response = self.__session.post(
                f"{self.__settings[ayon.SERVER_URL_KEY]}/api/resolve",
                json={"uris": entityRefs})
            end = timer()
            hostSession.logger().debug(
                f"entityExists took {end - start} seconds.")

        except requests.exceptions.RequestException as err:
            raise PluginError("Failed to connect to AYON server") from err

        if response.status_code != 200:
            raise PluginError(f"AYON server returned an error - {response.status_code} - {response.text}")  # noqa: E501

        result = []
        for rep in response.json():
            if rep["entities"]:
                result.append(True)
            else:
                result.append(False)
        return result

    def resolve(
        self, entityReferences: List[openassetio._openassetio.EntityReference],
            traitSet: Set[str],
            resolveAccess,
            context,
            hostSession,
            successCallback,
            errorCallback
    ) -> List[TraitsData] | None:
        # if there is no LocatableContentTrait (path), bail out.
        if mc_traits.content.LocatableContentTrait.kId not in traitSet:
            hostSession.logger().debug("no locatable content trait")
            for idx in range(len(entityReferences)):
                successCallback(idx, TraitsData())
            return

        payload = {
            "resolveRoots": True,
            "uris": [str(e) for e in entityReferences]
        }

        try:
            start = timer()
            response = self.__session.post(
                f"{self.__settings[ayon.SERVER_URL_KEY]}/api/resolve",
                json=payload)
            end = timer()
            hostSession.logger().debug(
                f"resolve request took {end - start} seconds.")

        except requests.exceptions.RequestException as err:
            raise PluginError("Failed to connect to AYON server") from err

        if response.status_code != 200:
            raise PluginError(f"AYON server returned an error - {response.status_code} - {response.text}")  # noqa: E501

        for idx, rep in enumerate(response.json()):
            # if there are entities in response, we were able to resolve
            # something.
            if rep["entities"]:
                traits_data = TraitsData()
                trait = mc_traits.content.LocatableContentTrait(traits_data)
                resolved_uri = Path(rep["entities"][0]["filePath"]).as_uri()
                trait.setLocation(resolved_uri)
                hostSession.logger().debug(f"location: {resolved_uri}")
                successCallback(idx, traits_data)
            else:
                errorCallback(idx, BatchElementError(
                    BatchElementError.ErrorCode.kEntityResolutionError,
                    "Entity not found"))

    def preflight(
        self, targetEntityRefs, traitsDatas, access,
        context,hostSession, successCallback, errorCallback
    ):
        raise NotImplementedError("preflight is not supported")

    def register(
        self,
        targetEntityRefs,
        entityTraitsDatas,
        context,
        hostSession,
        successCallback,
        errorCallback,
    ):
        raise NotImplementedError("Registering entities is not supported")

    def getWithRelationship(
        self,
        entityReferences,
        relationshipTraitsData,
        resultTraitSet,
        context,
        hostSession,
        successCallback,
        errorCallback,
    ):
        raise NotImplementedError("getWithRelationship is not supported")

    def getWithRelationships(
        self,
        entityReference,
        relationshipTraitsDatas,
        resultTraitSet,
        context,
        hostSession,
        successCallback,
        errorCallback,
    ):
        raise NotImplementedError("getWithRelationships is not supported")

    def getRelatedReferences(self, entityRefs, relationshipTraitsDatas,
                             context, hostSession, resultTraitSet=None):
        raise NotImplementedError("getRelatedReferences is not supported")

    def __build_entity_ref(
            self, entity_info: ayon.EntityInfo) -> EntityReference:
        """Builds an openassetio EntityReference from an AYON EntityInfo.
            Args:
                entity_info: The AYON EntityInfo to build the
                    EntityReference from.

            Returns:
                EntityReference: The built EntityReference.

        """
        ref_string = (f"ayon+entity://{entity_info.project_name}/"
                      f"{entity_info.path}?"
                      f"product={entity_info.product_name}&"
                      f"version={entity_info.version_name}&"
                      f"representation={entity_info.representation_name}")
        return self._createEntityReference(ref_string)
