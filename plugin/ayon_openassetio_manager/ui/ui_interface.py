"""
Entry point for the AYON OpenAssetIO UI delegate.

Provides a proxy class that calls out to the actual implementation, which must
be imported at runtime.
"""
from openassetio import Context
from openassetio.managerApi import HostSession
from openassetio.trait import TraitsData

from openassetio.ui import access
from openassetio.ui.managerApi import UIDelegateInterface, UIDelegateRequest


class AyonUIDelegateInterface(UIDelegateInterface):
    """
    This class exposes the AYON UI through the OpenAssetIO UIDelegateInterface.

    It acts as a proxy to the AyonOpenAssetIOUIDelegateInterfaceCore class,
    which contains the actual implementation.

    Certain methods (displayName, identifier) must be callable before
    initialize() is called, and so must be implemented in this class.
    """

    def __init__(self):
        UIDelegateInterface.__init__(self)
        self.__core = None

    def displayName(self):
        return "AYON OpenAssetIO UI Delegate"

    def identifier(self):
        return "io.ynput.ayon.openassetio.manager.interface"

    def initialize(self, managerSettings, hostSession):
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
            raise RuntimeError("UI delegate not initialized")
        return self.__core.uiPolicy(uiTraits, uiAccess, context, hostSession)

    def populateUI(
        self,
        uiTraits: TraitsData,
        uiAccess: access.UIAccess,
        uiDelegateRequest: UIDelegateRequest,
        context: Context,
        hostSession: HostSession,
    ):
        if self.__core is None:
            raise RuntimeError("UI delegate not initialized")
        return self.__core.populateUI(uiTraits, uiAccess, uiDelegateRequest, context, hostSession)
