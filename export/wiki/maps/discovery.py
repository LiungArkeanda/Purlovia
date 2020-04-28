from typing import Iterable, Iterator

import ue.hierarchy
from ark.overrides import get_overrides_for_map
from config import ConfigFile, get_global_config
from export.wiki.consts import LEVEL_SCRIPT_ACTOR_CLS, WORLD_CLS
from ue.asset import UAsset
from ue.loader import AssetLoader, AssetLoadException
from utils.log import get_logger

logger = get_logger(__name__)


class LevelDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def discover_vanilla_levels(self) -> Iterator[str]:
        config = get_global_config()
        official_modids = set(config.official_mods.ids())
        official_modids -= set(config.settings.SeparateOfficialMods)
        official_mod_prefixes = tuple(f'/Game/Mods/{modid}/' for modid in official_modids)

        all_cls_names = list(ue.hierarchy.find_sub_classes(WORLD_CLS))
        all_cls_names += ue.hierarchy.find_sub_classes(LEVEL_SCRIPT_ACTOR_CLS)

        for cls_name in all_cls_names:
            assetname = cls_name[:cls_name.rfind('.')]

            # Check if this asset is meant to be skipped
            overrides = get_overrides_for_map(assetname, '')
            if overrides.skip_export:
                continue

            # Skip anything in the mods directory that isn't one of the listed official mods
            if assetname.startswith('/Game/Mods') and not any(assetname.startswith(prefix) for prefix in official_mod_prefixes):
                continue

            yield assetname

    def discover_mod_levels(self, modid: str) -> Iterator[str]:
        clean_path = self.loader.clean_asset_name(f'/Game/Mods/{modid}') + '/'

        all_cls_names = list(ue.hierarchy.find_sub_classes(WORLD_CLS))
        all_cls_names += ue.hierarchy.find_sub_classes(LEVEL_SCRIPT_ACTOR_CLS)

        for cls_name in all_cls_names:
            assetname = cls_name[:cls_name.rfind('.')]

            if assetname.startswith(clean_path):
                # Check if this asset is meant to be skipped
                overrides = get_overrides_for_map(assetname, modid)
                if overrides.skip_export:
                    continue

                yield assetname
