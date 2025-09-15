"""Ayon OpenAssetIO Manager Interface.

TODO(anyone): Replace RuntimeError with a custom error type.

"""

from __future__ import annotations

import os
from typing import Any, Callable, Union

import ayon_api
import openassetio
from openassetio import Context, EntityReference, access, constants
from openassetio.errors import BatchElementError
from openassetio.managerApi import (
    HostSession,
    ManagerInterface,
    ManagerStateBase,
)
from openassetio.trait import TraitsData

from . import ayon

__all__ = [
    "AyonOpenAssetIOManagerInterface",
]

InfoDictionary = dict[str, Union[str, float, int, bool]]


class AyonOpenAssetIOManagerInterface(ManagerInterface):
    """Exposes AYON as a OpenAssetIO ManagerInterface.

    Instances of this class are created by the OpenAssetIO plugin system.

    This class acts as a proxy to the AyonOpenAssetIOManagerInterfaceCore class,
    which contains the actual implementation. Certain methods (identifier,
    displayName, info, settings, hasCapability) must be callable before
    initialize() is called, and so are implemented in this class.
    """

    __reference_prefix = "ayon+entity://"

    def __init__(self):
        """Constructor."""
        super().__init__()
        self.__settings = None
        self.__core = None

    def identifier(self) -> str:
        """The unique identifier for this manager implementation.

        Returns:
            str: The unique identifier for this manager implementation.

        """
        return "io.ynput.ayon.openassetio.manager.interface"

    def displayName(self) -> str:  # noqa: N802
        """The human-readable name for this manager implementation.

        Returns:
            str: The human-readable name for this manager implementation.

        """
        return "AYON OpenAssetIO Manager"

    def info(self) -> InfoDictionary:
        """Information about this manager implementation.

        Returns:
            InfoDictionary: Information about this manager implementation.

        """
        return {
            constants.kInfoKey_EntityReferencesMatchPrefix: self.__reference_prefix  # noqa: E501
        }

    def settings(
            self, hostSession: HostSession) -> InfoDictionary:    # noqa: N803
        """The settings supported by this manager implementation.

        At this point, the manager has not yet been initialized, so
        this method should return the default settings.

        Args:
            hostSession (HostSession): The host session.

        Returns:
            InfoDictionary: The settings supported by this manager
                implementation.

        """
        return {} if self.__settings is None else self.__settings.copy()

    def initialize(
            self,
            managerSettings: InfoDictionary,  # noqa: N803
            hostSession: HostSession) -> None:  # noqa: N803
        """Initializes the manager with the provided settings.

        Args:
            managerSettings (InfoDictionary): The settings to initialize
                the manager with.
            hostSession (HostSession): The host session.

        """
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

    def hasCapability(  # noqa: N802
            self, capability: ManagerInterface.Capability) -> bool:
        """Whether this manager implementation supports the given capability.

        Args:
            capability (ManagerInterface.Capability): The capability to check.

        Returns:
            bool: True if the capability is supported, False otherwise.

        """
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

    def createState(  # noqa: N802
            self,
            hostSession: HostSession  # noqa: N803
    ) -> ManagerStateBase:
        """Create a new ManagerStateBase instance.

        A manager state can be used to hold stateful information
        across multiple calls to the manager interface.

        Args:
            hostSession (HostSession): The host session.

        Returns:
            ManagerStateBase: A new manager state instance

        Raises:
            RuntimeError: If the manager has not been initialized
            .
        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)

        return self.__core.createState(hostSession)

    def createChildState(  # noqa: N802
        self,
        parentState: ManagerStateBase,  # noqa: N803
        hostSession: HostSession,  # noqa: N803
    ) -> ManagerStateBase:
        """Create a new ManagerStateBase instance as a child of another.

        Args:
            parentState (ManagerStateBase): The parent state.
            hostSession (HostSession): The host session.

        Returns:
            ManagerStateBase: A new manager state instance.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.createChildState(parentState, hostSession)

    def managementPolicy(  # noqa: N802
        self,
        traitSets: list[set[str]],  # noqa: N803
        policyAccess: access.PolicyAccess,  # noqa: N803
        context: openassetio.Context,
        hostSession: openassetio.managerApi.HostSession,  # noqa: N803
    ) -> list[TraitsData]:
        """Query the management policy for the given trait sets.

        Args:
            traitSets (list[set[str]]): The trait sets to query the policy for.
            policyAccess (access.PolicyAccess): The access level for the policy
                query.
            context (Context): The context for the policy query.
            hostSession (HostSession): The host session.

        Returns:
            list[TraitsData]: The management policy for the given trait sets.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.managementPolicy(
            traitSets, policyAccess, context, hostSession)

    def isEntityReferenceString(  # noqa: N802
            self,
            someString: str,  # noqa: N803
            hostSession: HostSession  # noqa: N803
    ) -> bool:
        """Check if the given string is a valid entity reference.

        Args:
            someString (str): The string to check.
            hostSession (HostSession): The host session.

        Returns:
            bool: True if the string is a valid entity reference, False
                otherwise.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.isEntityReferenceString(someString, hostSession)

    def entityExists(  # noqa: N802
        self,
        entityRefs: list[EntityReference],  # noqa: N803
        context: Context,
        hostSession: HostSession,  # noqa: N803
        successCallback: Callable[[int, list[EntityReference]], Any],  # noqa: N803
        errorCallback: Callable[[int, BatchElementError], Any],  # noqa: N803
    ) -> None:
        """Check if the given entity reference exist.

        Args:
            entityRefs (list[EntityReference]): The entity references to check.
            context (Context): The context for the existence check.
            hostSession (HostSession): The host session.
            successCallback (Callable[[int, list[EntityReference]], Any]):
                The callback to call on success.
            errorCallback (Callable[[int, BatchElementError], Any]):
                The callback to call on error.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.entityExists(
            entityRefs, context, hostSession, successCallback, errorCallback
        )

    def resolve(  # noqa: PLR0913, PLR0917
        self,
        entityReferences: list[EntityReference],  # noqa: N803
        traitSet: set[str],  # noqa: N803
        resolveAccess: access.ResolveAccess,  # noqa: N803
        context: Context,
        hostSession: HostSession,  # noqa: N803
        successCallback: Callable[[int, TraitsData], Any],  # noqa: N803
        errorCallback: Callable[[int, BatchElementError], Any],  # noqa: N803
    ) -> None:
        """Resolve the given entity references to the given trait set.

        Args:
            entityReferences (list[EntityReference]): The entity references to
                resolve.
            traitSet (set[str]): The trait set to resolve to.
            resolveAccess (access.ResolveAccess): The access level for the
                resolution.
            context (Context): The context for the resolution.
            hostSession (HostSession): The host session.
            successCallback (Callable[[int, TraitsData], Any]): The callback to
                call on success.
            errorCallback (Callable[[int, BatchElementError], Any]): The
                callback to call on error.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.resolve(
            entityReferences,
            traitSet,
            resolveAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def preflight(  # noqa: PLR0913, PLR0917
        self,
        targetEntityRefs: list[EntityReference],  # noqa: N803
        traitsHints: list[TraitsData],  # noqa: N803
        publishingAccess: access.PublishingAccess,  # noqa: N803
        context: Context,
        hostSession: HostSession,  # noqa: N803
        successCallback: Callable[[int, TraitsData], Any],  # noqa: N803
        errorCallback: Callable[[int, BatchElementError], Any],  # noqa: N803
    ) -> None:
        """Preflight the given entity references for registration.

        Args:
            targetEntityRefs (list[EntityReference]): The entity references to
                preflight.
            traitsHints (list[TraitsData]): The trait hints for the
                preflight.
            publishingAccess (access.PublishingAccess): The access level for
                the preflight.
            context (Context): The context for the preflight.
            hostSession (HostSession): The host session.
            successCallback (Callable[[int, TraitsData], Any]): The callback
                to call on success.
            errorCallback (Callable[[int, BatchElementError], Any]): The
                callback to call on error.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.preflight(
            targetEntityRefs,
            traitsHints,
            publishingAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def register(  # noqa: PLR0913, PLR0917
        self,
        targetEntityRefs: list[EntityReference],  # noqa: N803
        entityTraitsDatas: list[TraitsData],  # noqa: N803
        publishingAccess: access.PublishingAccess,  # noqa: N803
        context: Context,
        hostSession: HostSession,  # noqa: N803
        successCallback: Callable[[int, TraitsData], Any],  # noqa: N803
        errorCallback: Callable[[int, BatchElementError], Any],  # noqa: N803
    ) -> None:
        """Register the given entity references with the given traits data.

        Args:
            targetEntityRefs (list[EntityReference]): The entity references to
                register.
            entityTraitsDatas (list[TraitsData]): The traits data for the
                registration.
            publishingAccess (access.PublishingAccess): The access level for
                the registration.
            context (Context): The context for the registration.
            hostSession (HostSession): The host session.
            successCallback (Callable[[int, TraitsData], Any]): The callback
                to call on success.
            errorCallback (Callable[[int, BatchElementError], Any]): The
                callback to call on error.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
        return self.__core.register(
            targetEntityRefs,
            entityTraitsDatas,
            publishingAccess,
            context,
            hostSession,
            successCallback,
            errorCallback,
        )

    def getWithRelationship(  # noqa: PLR0913, PLR0917
        self,
        entityReferences: list[EntityReference],  # noqa: N803
        relationshipTraitsData: TraitsData,  # noqa: N803
        resultTraitSet: set[str],  # noqa: N803
        pageSize: int,  # noqa: N803
        relationsAccess: access.RelationsAccess,  # noqa: N803
        context: Context,
        hostSession: HostSession,  # noqa: N803
        successCallback: Callable[[int, TraitsData], Any],  # noqa: N803
        errorCallback: Callable[[int, BatchElementError], Any],  # noqa: N803
    ) -> None:
        """Get entities related to the given entity references.

        Args:
            entityReferences (list[EntityReference]): The entity references to
                get related entities for.
            relationshipTraitsData (TraitsData): The traits data for the
                relationship.
            resultTraitSet (set[str]): The trait set to return for the related
                entities.
            pageSize (int): The number of related entities to return per page.
            relationsAccess (access.RelationsAccess): The access level for the
                relationship query.
            context (Context): The context for the relationship query.
            hostSession (HostSession): The host session.
            successCallback (Callable[[int, TraitsData], Any]): The callback
                to call on success.
            errorCallback (Callable[[int, BatchElementError], Any]): The
                callback to call on error.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
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

    def getWithRelationships(  # noqa: PLR0913, PLR0917
        self,
        entityReference: EntityReference,  # noqa: N803
        relationshipTraitsDatas: list[TraitsData],  # noqa: N803
        resultTraitSet: set[str],  # noqa: N803
        pageSize: int,  # noqa: N803
        relationsAccess: access.RelationsAccess,  # noqa: N803
        context: Context,
        hostSession: HostSession,  # noqa: N803
        successCallback: Callable[[int, TraitsData], Any],  # noqa: N803
        errorCallback: Callable[[int, BatchElementError], Any],  # noqa: N803
    ) -> None:
        """Get entities related to the given entity reference.

        Given an entity reference, fetch entities related to it by any of
        the specified relationship traits.

        Args:
            entityReference (EntityReference): The entity reference to get
                related entities for.
            relationshipTraitsDatas (list[TraitsData]): The traits data for the
                relationships.
            resultTraitSet (set[str]): The trait set to return for the related
                entities.
            pageSize (int): The number of related entities to return per page.
            relationsAccess (access.RelationsAccess): The access level for the
                relationship query.
            context (Context): The context for the relationship query.
            hostSession (HostSession): The host session.
            successCallback (Callable[[int, TraitsData], Any]): The callback
                to call on success.
            errorCallback (Callable[[int, BatchElementError], Any]): The
                callback to call on error.

        Raises:
            RuntimeError: If the manager has not been initialized.

        """
        if self.__core is None:
            msg = "Manager not initialized"
            raise RuntimeError(msg)
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
