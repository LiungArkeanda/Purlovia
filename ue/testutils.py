import os.path

import pytest

import ark.asset
import ark.mod
from ue.asset import UAsset
from ue.base import UEBase
from ue.loader import load_file_into_memory
from ue.properties import *
from ue.stream import MemoryStream
from ue.utils import *


def load_asset(assetfile: str):
    assetfile = assetfile.replace('/', '_')
    if not assetfile.lower().endswith('.uasset'): assetfile += '.uasset'
    filename = os.path.join('.', 'testdata', assetfile)
    mem = load_file_into_memory(filename)
    stream = MemoryStream(mem, 0, len(mem))
    asset = UAsset(stream)
    asset.deserialise()
    asset.link()
    exports = list(ark.asset.findComponentExports(asset))
    assert len(exports) == 1
    asset.default_export = exports[0]
    return asset


def parse_colors(props):
    colours = dict()
    for prop in props:
        if str(prop.header.name) != 'ColorSetDefinitions':
            continue

        struct = prop.value
        assert len(struct.values) > 0 and len(struct.values) <= 3

        if len(struct.values) == 1:
            name = None
            assert str(struct.values[0].name) == 'ColorEntryNames' or str(struct.values[0].name) == 'RegionName'
            if str(struct.values[0].name) == 'RegionName':
                assert str(struct.values[0].value) == '****No Effect****'
                array = None
            elif str(struct.values[0].name) == 'ColorEntryNames':
                array = struct.values[0].value
        else:
            assert str(struct.values[0].name) == 'RegionName'
            name = str(struct.values[0].value)
            assert str(struct.values[1].name) == 'ColorEntryNames'
            array = struct.values[1].value
            if len(struct.values) == 3:
                assert (str(struct.values[2].name) == 'RandomWeights')

        values = tuple(str(v) for v in array.values) if array else None
        colours[prop.header.index] = dict(name=name, values=values)

    return colours
