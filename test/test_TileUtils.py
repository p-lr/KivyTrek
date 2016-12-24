__author__ = 'pol'

import pytest
from TileUtils import TileCache


@pytest.mark.parametrize("zoom_list,zoom,expected", [
    ([0, 1, 2, 4, 7, 8], 2, [0, 1, 4, 7, 8]),
    ([0, 3, 5, 8], 4, [0, 3, 8]),
    ([8, 9, 10], 9, [8])
])
def test_get_unnecessary_zooms(zoom_list, zoom, expected):
    assert set(TileCache.get_unnecessary_zooms(zoom_list, zoom)) == set(expected)
