__author__ = 'pol'

import kivy

kivy.require('1.8.0')
from kivy.loader import Loader
from os.path import join, isfile
from Map import Map


class LocalMapImageTyler(Map):
    """
    Implementation of a local map created with ImageTiler python script.
    """

    def __init__(self, _map_dir, _ini_file_path):
        super(LocalMapImageTyler, self).__init__(_ini_file_path)
        self.map_dir = _map_dir

    def get_tile(self, zoom, x, y):
        """x, y : indexes"""
        y = pow(2, zoom) - y - 1
        ext = self.ext
        tile_name = "tile-%(zoom)s-%(x)s-%(y)s.%(ext)s" % locals()
        path = join(self.map_dir, tile_name)
        if isfile(path):
            return Loader.image(path, nocache=True)
        else:
            return None


class LocalMapVips(Map):
    """
    Implementation of a local map created with LibVips library, dzsave function.
    """

    def __init__(self, _map_dir, _ini_file_path):
        super(LocalMapVips, self).__init__(_ini_file_path)
        self.map_dir = _map_dir

    def get_tile(self, zoom, x, y):
        """x, y : indexes"""
        y = pow(2, zoom) - y - 1
        path = join(self.map_dir, str(zoom), str(y), "%s.%s" % (x, self.ext))
        if isfile(path):
            return Loader.image(path, nocache=True)
        else:
            return None
