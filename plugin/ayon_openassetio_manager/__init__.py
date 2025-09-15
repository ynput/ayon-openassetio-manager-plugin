"""Ayon OpenAssetIO Manager Plugin."""
from __future__ import annotations

from typing import TYPE_CHECKING

from openassetio.pluginSystem import PythonPluginSystemManagerPlugin

if TYPE_CHECKING:
    from .manager_interface import AyonOpenAssetIOManagerInterface


class AyonOpenAssetIOManagerPlugin(PythonPluginSystemManagerPlugin):
    """Ayon OpenAssetIO Manager Plugin."""
    @staticmethod
    def identifier() -> str:
        """The unique identifier for this plugin.

        Returns:
            str: The unique identifier for this plugin.

        """
        return "io.ynput.ayon.openassetio.manager"

    @classmethod
    def interface(cls) -> AyonOpenAssetIOManagerInterface:
        """The interface class for this plugin.

        Returns:
            AyonOpenAssetIOManagerInterface: The interface class for
                this plugin.

        """
        from .manager_interface import AyonOpenAssetIOManagerInterface

        return AyonOpenAssetIOManagerInterface()


openassetioPlugin = AyonOpenAssetIOManagerPlugin  # noqa: N816
