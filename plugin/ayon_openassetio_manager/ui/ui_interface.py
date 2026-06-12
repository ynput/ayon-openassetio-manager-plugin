"""Entry point for the AYON OpenAssetIO UI delegate.

Provides a proxy class that calls out to the actual implementation, which must
be imported at runtime.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from openassetio import Context
from openassetio.managerApi import HostSession
from openassetio.trait import TraitsData
from openassetio.ui import access
from openassetio.ui.managerApi import UIDelegateInterface, UIDelegateRequest

if TYPE_CHECKING:
    from .ui_core import AyonUIDelegateState


class AyonUIDelegateInterface(UIDelegateInterface):
    """Ayon OpenAssetIO UI Delegate Interface.

    This class exposes the AYON UI through the OpenAssetIO UIDelegateInterface.

    It acts as a proxy to the AyonOpenAssetIOUIDelegateInterfaceCore class,
    which contains the actual implementation.

    Certain methods (displayName, identifier) must be callable before
    initialize() is called, and so must be implemented in this class.
    """
    def __init__(self):
        """Constructor."""
        UIDelegateInterface.__init__(self)
        self.__core = None

    def displayName(self) -> str:
        """The display name of this UI delegate.

        Returns:
            str: The display name of this UI delegate.

        """
        return "AYON OpenAssetIO UI Delegate"

    def identifier(self) -> str:
        """The unique identifier for this UI delegate.

        Returns:
            str: The unique identifier for this UI delegate.

        """
        return "io.ynput.ayon.openassetio.manager.interface"

    def initialize(self, managerSettings, hostSession) -> None:
        """Initializes the UI delegate."""
        from .ui_core import AyonOpenAssetIOUIDelegateInterfaceCore

        self.__core = AyonOpenAssetIOUIDelegateInterfaceCore()

    def uiPolicy(
        self,
        uiTraits: set[str],
        uiAccess: access.UIAccess,
        context: Context,
        hostSession: HostSession,
    ):
        if self.__core is None:
            msg = "UI delegate not initialized"
            raise RuntimeError(msg)
        return self.__core.uiPolicy(uiTraits, uiAccess, context, hostSession)

    def populateUI(
        self,
        uiTraits: TraitsData,
        uiAccess: access.UIAccess,
        uiDelegateRequest: UIDelegateRequest,
        context: Context,
        hostSession: HostSession,
    ) -> AyonUIDelegateState | None:
        """Populate the UI for the given traits and access.

        Args:
            uiTraits (TraitsData): The traits data to populate the UI for.
            uiAccess (access.UIAccess): The access level for the UI.
            uiDelegateRequest (UIDelegateRequest): The UI delegate request.
            context (Context): The context for the UI.
            hostSession (HostSession): The host session.

        Returns:
            AyonUIDelegateState | None: The populated UI state, or None if
                the UI could not be populated.

        Raises:
            RuntimeError: If the UI delegate has not been initialized.

        """
        if self.__core is None:
            msg = "UI delegate not initialized"
            raise RuntimeError(msg)
        return self.__core.populateUI(
            uiTraits, uiAccess, uiDelegateRequest, context, hostSession)
