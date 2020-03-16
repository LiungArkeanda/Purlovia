from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePosixPath
from typing import *

from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from config import ConfigFile
from ue.base import UEBase
from ue.proxy import UEProxyStructure
from ue.utils import sanitise_output
from utils.strings import get_valid_filename

from .exporter import ExportStage

__all__ = [
    'JsonHierarchyExportStage',
]


class JsonHierarchyExportStage(ExportStage, metaclass=ABCMeta):
    gathered_results: Optional[List[Any]]
    '''
    An intermediate helper class that performs hierarchy discovery for core/mods,
    calls the user's `extract_class` for each of them and handles saving the results.
    '''
    @abstractmethod
    def get_format_version(self) -> str:
        '''Return the a format version identifier.'''
        ...

    def get_field(self) -> str:
        '''Return the name to be used as the top-level container in the output JSON.'''
        return self.get_name()

    @abstractmethod
    def get_use_pretty(self) -> bool:
        '''Return True if the file should be prettified, or False if it should be minified.'''
        ...

    @abstractmethod
    def get_ue_type(self) -> str:
        '''Return the fullname of the UE type to gather.'''
        ...

    def get_core_file_path(self) -> PurePosixPath:
        '''Return the relative path of the core output file that should be generated.'''
        field = self.get_field()
        return PurePosixPath(f'{field}.json')

    def get_mod_file_path(self, modid: str) -> PurePosixPath:
        '''Return the relative path of the expected mod output file that should be generated.'''
        field = self.get_field()
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        return PurePosixPath(f'{modid}-{mod_data["name"]}/{field}.json')

    @abstractmethod
    def extract(self, proxy: UEProxyStructure) -> Any:
        '''Perform extraction on the given proxy and return any JSON-able object.'''
        raise NotImplementedError

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:  # pylint: disable=unused-argument
        '''
        Return any extra dict entries that should be put *before* the main entries.
        The precense or absence of pre-data *is not* considered when deciding if a file should be saved,
        thus pre-data should be used for metadata only.
        Default behaviour is to include the mod's metadata if extracting for a mod.
        '''
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return dict()

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:  # pylint: disable=unused-argument
        '''
        Return any extra dict entries that should be put *after* the main entries.
        If any post-data is present it will stop the file being considered empty and avoid it being removed.
        Has access to results gathered from `extract` in self.gathered_results.
        '''
        ...

    def extract_core(self, path: Path):
        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        filename = self.get_core_file_path()
        proxy_iter = self.manager.iterate_core_exports_of_type(self.get_ue_type())
        self._extract_and_save(version, None, path, filename, proxy_iter)

    def extract_mod(self, path: Path, modid: str):
        # Mod versions are based on the game version and mod change date
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.get_mod_version(modid))  # type: ignore

        filename = self.get_mod_file_path(modid)
        proxy_iter = self.manager.iterate_mod_exports_of_type(self.get_ue_type(), modid)
        self._extract_and_save(version, modid, path, filename, proxy_iter)

    def _extract_and_save(self, version: str, modid: Optional[str], base_path: Path, relative_path: PurePosixPath,
                          proxy_iter: Iterator[UEProxyStructure]):
        # Work out the output path (cleaned)
        clean_relative_path = PurePosixPath('/'.join(get_valid_filename(p) for p in relative_path.parts))
        output_path = Path(base_path / clean_relative_path)

        # Setup the output structure
        results: List[Any] = []
        format_version = self.get_format_version()
        output: Dict[str, Any] = dict(version=version, format=format_version)

        # Pre-data comes before the main items
        pre_data = self.get_pre_data(modid) or dict()
        pre_data = sanitise_output(pre_data)
        output.update(pre_data)

        # Main items array
        output[self.get_field()] = results

        # Do the actual export into the existing `results` list
        for proxy in proxy_iter:
            item_output = self.extract(proxy)
            if item_output:
                item_output = sanitise_output(item_output)
                results.append(item_output)

        # Make the results available to get_post_data
        self.gathered_results = results

        # Post-data comes after the main items
        post_data = self.get_post_data(modid) or {}
        post_data = sanitise_output(post_data)
        output.update(post_data)
        post_data_has_content = post_data and any(post_data.values())

        # Clear gathered data reference
        del self.gathered_results

        # Save if the data changed
        if results or post_data_has_content:
            save_json_if_changed(output, output_path, self.get_use_pretty())
        else:
            # ...but remove an existing one if the output was empty
            if output_path.is_file():
                output_path.unlink()
