from openassetio.pluginSystem import PythonPluginSystemManagerPlugin


class AyonOpenAssetIOManagerPlugin(PythonPluginSystemManagerPlugin):

    @staticmethod
    def identifier():
        return "io.ynput.ayon.openassetio.manager"

    @classmethod
    def interface(cls):
        from .AyonOpenAssetIOManagerInterface import (
            AyonOpenAssetIOManagerInterface
        )

        return AyonOpenAssetIOManagerInterface()


plugin = AyonOpenAssetIOManagerPlugin
