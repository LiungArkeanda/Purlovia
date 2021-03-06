import pytest

from ue.context import ue_parsing_context
from ue.loader import AssetLoader

from .common import *  # noqa: F401,F403  # needed to pick up all fixtures
from .common import TEST_PGD_PKG


@pytest.mark.requires_game
def test_defaults(loader: AssetLoader):
    loader.wipe_cache()
    asset = loader[TEST_PGD_PKG]
    assert asset.is_linked
    assert asset.has_properties
    assert not asset.has_bulk_data

    loader.wipe_cache()
    with ue_parsing_context():
        asset = loader[TEST_PGD_PKG]
        assert asset.is_linked
        assert asset.has_properties
        assert not asset.has_bulk_data


@pytest.mark.requires_game
def test_linking(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False):
        asset = loader[TEST_PGD_PKG]
        assert not asset.is_linked

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(link=True):
            asset = loader[TEST_PGD_PKG]
            assert asset.is_linked

    loader.wipe_cache()
    with ue_parsing_context(link=True):
        asset = loader[TEST_PGD_PKG]
        assert asset.is_linked


@pytest.mark.requires_game
def test_properties(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(properties=False):
        asset = loader[TEST_PGD_PKG]
        assert not asset.has_properties

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(properties=True):
            asset = loader[TEST_PGD_PKG]
            assert asset.has_properties

    loader.wipe_cache()
    with ue_parsing_context(properties=True):
        asset = loader[TEST_PGD_PKG]
        assert asset.has_properties


@pytest.mark.requires_game
def test_no_properties_without_link(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False, properties=True):
        asset = loader[TEST_PGD_PKG]
        assert not asset.has_properties


@pytest.mark.requires_game
def test_bulk_data(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(bulk_data=False):
        asset = loader[TEST_PGD_PKG]
        assert not asset.has_bulk_data

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(bulk_data=True):
            asset = loader[TEST_PGD_PKG]
            assert asset.has_bulk_data

    loader.wipe_cache()
    with ue_parsing_context(bulk_data=True):
        asset = loader[TEST_PGD_PKG]
        assert asset.has_bulk_data
