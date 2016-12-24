# -*- coding: utf-8 -*-
__author__ = 'pol'

import kivy
kivy.require('1.8.0')
from kivy.vector import Vector

# TODO : adapter automatiquement à la taille de la fenêtre
TILES_MAX_NUMBER = 48


class TileCache(object):
    def __init__(self):
        self.tile_count = 0
        self.container = dict()

    def add_tile(self, zoom, tile_id):
        if zoom not in self.container:
            self.container[zoom] = []
        if not self.container[zoom].count(tile_id):
            self.container[zoom].append(tile_id)
            self.tile_count += 1
            return True
        return False

    def get_tiles_from_zoom(self, zoom):
        if zoom in self.container:
            return self.container[zoom]
        else:
            return []

    def get_container_size(self):
        size = 0
        for key in self.container:
            if key is not None:
                size += len(self.container[key])
        return size

    def remove_tiles_for_zoom(self, zoom):
        if zoom in self.container:
            if zoom in self.container:
                self.tile_count -= len(self.container[zoom])
            return self.container.pop(zoom)

    @staticmethod
    def get_unnecessary_zooms(zoom_list, zoom):
        """
        :param zoom_list: list of zooms
        :param zoom: current zoom
        :return: list of zooms strictly greater than zoom by a value of 1, and strictly lower than zoom
        """
        return [i for i in zoom_list if i-zoom > 1 or i-zoom < 0]

    def is_tile_overfull(self, zoom):
        return self.tile_count >= TILES_MAX_NUMBER

    def show(self):
        print self.container


class Tile(object):
    zoom = 0
    x = 0
    y = 0
    pos = Vector(0, 0)
    size = (256, 256)   # default value
    texture = None

    def get_id(self):
        return "".join([str(self.zoom), "-", str(self.x), "-", str(self.y)])

if __name__ == '__main__':
    tileCache = TileCache()
    tileCache.add_tile(3, "3-1-1")
    tileCache.add_tile(0, "0-0-0")
    tileCache.add_tile(0, "0-1-1")
    tileCache.add_tile(0, "0-2-1")
    tileCache.add_tile(0, "0-3-1")
    tileCache.add_tile(0, "0-4-1")
    tileCache.add_tile(7, "7-0-1")
    tileCache.add_tile(2, "2-0-1")

    # print tileCache.show(), tileCache.get_size()
    print tileCache.get_tiles_to_trash(0, [])
    print tileCache.show()
