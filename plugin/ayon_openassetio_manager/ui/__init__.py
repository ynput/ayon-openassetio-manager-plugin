"""Ayon OpenAssetIO UI Delegate Plugin Module."""
from openassetio.ui.pluginSystem import PythonPluginSystemUIDelegatePlugin


class AyonUIPlugin(PythonPluginSystemUIDelegatePlugin):
    """Ayon OpenAssetIO UI Delegate Plugin.

    The PythonPluginSystemUIDelegatePlugin is responsible for constructing
    instances of the uiDelegate's implementation of the OpenAssetIO
    interfaces and returning them to the host.
    """

    @classmethod
    def identifier(cls) -> str:
        """The unique identifier for this plugin.

        Returns:
            str: The unique identifier for this plugin.
        """
        return "io.ynput.ayon.openassetio.manager"

    @classmethod
    def interface(cls):
        from .ui_interface import AyonUIDelegateInterface

        return AyonUIDelegateInterface()


openassetioUIPlugin = AyonUIPlugin
