import os
from .plugin import AyonOpenAssetIOManagerPlugin


AYON_OPENASSETIO_ROOT = os.path.dirname(os.path.dirname(__file__))
plugin = AyonOpenAssetIOManagerPlugin
