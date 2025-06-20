from __future__ import annotations

import os

import openassetio
from openassetio import EntityReference, access, constants, Context
from openassetio.managerApi import ManagerInterface, HostSession, ManagerStateBase

import ayon_api
from openassetio.trait import TraitsData

from . import ayon


__all__ = [
    "AyonOpenAssetIOManagerInterface",
]

InfoDictionary = dict[str, str | float | int | bool]


class AyonOpenAssetIOManagerInterface(ManagerInterface):
    """
    This class exposes AYON as a OpenAssetIO ManagerInterface.

    Instances of this class are created by the OpenAssetIO plugin system.

    This class acts as a proxy to the AyonOpenAssetIOManagerInterfaceCore class,
    which contains the actual implementation. Certain methods (identifier,
    displayName, info, settings, hasCapability) must be callable before
    initialize() is called, and so are implemented in this class.
    """

    __reference_prefix = "ayon+entity://"

    def __init__(self):
        super().__init__()
        self.__settings = None
        self.__core = None

    def identifier(self):
        return "io.ynput.ayon.openassetio.manager.interface"

    def displayName(self):
        return "AYON OpenAssetIO Manager"

    def info(self):
        return {constants.kInfoKey_EntityReferencesMatchPrefix: self.__reference_prefix}

    def settings(self, hostSession: HostSession) -> InfoDictionary:
        if self.__settings is None:
            return {}
        return self.__settings.copy()

    def initialize(self, managerSettings: InfoDictionary, hostSession: HostSession) -> None:
        self.__settings = ayon.make_default_settings()
        self.__settings.update(managerSettings)

        # Update settings for Python API - relies on env vars.
        for key, value in self.__settings.items():
            if key not in ayon.env_var_settings:
                continue
            os.environ[key] = str(value)

        for key in ayon.env_var_settings:
            if value := os.environ.get(key):
                self.__settings[key] = value

        ayon.validate_settings(self.__settings)

        # Add site ID to allow roots of paths to be auto-resolved.
        ayon_api.set_site_id(ayon.query_site_id())

        # Bootstrap ayon_core and create the core implementation
        ayon.bootstrap_ayon_core(
            self.__settings[ayon.SERVER_BUNDLE_NAME_KEY], ayon_api.get_bundles()
        )
        from .manager_core import AyonOpenAssetIOManagerInterfaceCore

        self.__core = AyonOpenAssetIOManagerInterfaceCore(self.__settings)

    def hasCapability(self, capability: ManagerInterface.Capability):
        supported_capabilities = (
            # The following two capabilities are required. See docs for why
            # these need to be advertised (TLDR: future-proofing).
            ManagerInterface.Capability.kEntityReferenceIdentification,
            ManagerInterface.Capability.kManagementPolicyQueries,
            ManagerInterface.Capability.kEntityTraitIntrospection,
            # Optional supported capabilities.
            ManagerInterface.Capability.kExistenceQueries,
            ManagerInterface.Capability.kResolution,
            ManagerInterface.Capability.kStatefulContexts,
        )
        return capability in supported_capabilities

    def createState(self, hostSession: HostSession) -> ManagerStateBase:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")

        return self.__core.createState(hostSession)

    def createChildState(
        self, parentState: ManagerStateBase, hostSession: HostSession
    ) -> ManagerStateBase:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.createChildState(parentState, hostSession)

    def managementPolicy(
        self,
        traitSets: list[set[str]],
        policyAccess: access.PolicyAccess,
        context: openassetio.Context,
        hostSession: openassetio.managerApi.HostSession,
    ) -> list[TraitsData]:  # noqa: E501,N802, N803
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.managementPolicy(traitSets, policyAccess, context, hostSession)

    def isEntityReferenceString(self, someString: str, hostSession: HostSession) -> bool:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.isEntityReferenceString(someString, hostSession)

    def entityExists(
        self,
        entityRefs: list[EntityReference],
        context: Context,
        hostSession: HostSession,
        successCallback,
        errorCallback,
    ):
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.entityExists(
            entityRefs, context, hostSession, successCallback, errorCallback
        )

    def resolve(
        self,
        entityReferences: list[EntityReference],
        traitSet: set[str],
        resolveAccess: access.ResolveAccess,
        context: Context,
        hostSession: HostSession,
        successCallback,
        errorCallback,
    ) -> None:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.resolve(
            entityReferences,
            traitSet,
            resolveAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def preflight(
        self,
        targetEntityRefs: list[EntityReference],
        traitsHints: list[TraitsData],
        publishingAccess: access.PublishingAccess,
        context: Context,
        hostSession: HostSession,
        successCallback,
        errorCallback,
    ) -> None:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.preflight(
            targetEntityRefs,
            traitsHints,
            publishingAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def register(
        self,
        targetEntityRefs: list[EntityReference],
        entityTraitsDatas: list[TraitsData],
        publishingAccess: access.PublishingAccess,
        context: Context,
        hostSession: HostSession,
        successCallback,
        errorCallback,
    ) -> None:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.register(
            targetEntityRefs,
            entityTraitsDatas,
            publishingAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def getWithRelationship(
        self,
        entityReferences: list[EntityReference],
        relationshipTraitsData: TraitsData,
        resultTraitSet: set[str],
        pageSize: int,
        relationsAccess: access.RelationsAccess,
        context: Context,
        hostSession: HostSession,
        successCallback,
        errorCallback,
    ) -> None:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.getWithRelationship(
            entityReferences,
            relationshipTraitsData,
            resultTraitSet,
            pageSize,
            relationsAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def getWithRelationships(
        self,
        entityReference: EntityReference,
        relationshipTraitsDatas: list[TraitsData],
        resultTraitSet: set[str],
        pageSize: int,
        relationsAccess: access.RelationsAccess,
        context: Context,
        hostSession: HostSession,
        successCallback,
        errorCallback,
    ) -> None:
        if self.__core is None:
            raise RuntimeError("Manager not initialized")
        return self.__core.getWithRelationships(
            entityReference,
            relationshipTraitsDatas,
            resultTraitSet,
            pageSize,
            relationsAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )
