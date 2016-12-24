# -*- coding: utf-8 -*-
__author__ = 'peter'

from os import walk
from os.path import isfile, join
from ConfigParser import RawConfigParser
from LocalMap import LocalMapImageTyler, LocalMapVips
from app.modules.log import logger
from app.modules.config import config
from Map import MAP_INFOS_SECTION

CALIBRATION_FILE_NAME = "calibration.ini"


class MapLoader(object):
    IMAGE_TYLER = 'ImageTyler.py'
    VIPS = 'VIPS'
    providers = {IMAGE_TYLER: LocalMapImageTyler, VIPS: LocalMapVips}
    map_list = []

    @staticmethod
    def get_map_cls(provider):
        return MapLoader.providers.get(provider)

    @staticmethod
    def generate_maps():
        MapLoader.map_list = []

        config_parser = RawConfigParser()

        for path in config.get_map_paths():
            for subdir in [x[0] for x in walk(path)]:
                calib_file_path = join(subdir, CALIBRATION_FILE_NAME)
                if isfile(calib_file_path):
                    config_parser.read(calib_file_path)
                    map_generator = config_parser.get(MAP_INFOS_SECTION, "generated_by")
                    print map_generator, MapLoader.get_map_cls(map_generator)
                    cls = MapLoader.get_map_cls(map_generator)
                    if cls.__name__ == LocalMapImageTyler.__name__:
                        MapLoader.map_list.append(LocalMapImageTyler(subdir, calib_file_path))
                    elif cls.__name__ == LocalMapVips.__name__:
                        MapLoader.map_list.append(LocalMapVips(subdir, calib_file_path))
                    else:
                        logger.error("No generator found for this map")

    @staticmethod
    def get_former_map():
        map_calib_path = config.get_last_map_path()
        for map_ in MapLoader.map_list:
            if map_.calibration_file_path == map_calib_path:
                return map_
        return None


if __name__ == '__main__':
    print MapLoader.generate_maps()