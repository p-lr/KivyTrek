# -*- coding: utf-8 -*-
__author__ = 'pol'

import json
from app.modules.log import logger


class Config(object):
    """
    Class encapsulating the access to a config file.
    It exposes specific methods related to KivyTrek application.
    """
    def __init__(self, config_file):
        self._config_file = config_file
        self.json_data = None
        self.MAP_HEADER = 'maps'
        self.PATH_HEADER = 'paths'
        self.LAST_MAP_HEADER = 'last_map'
        self.load_config_file()

    def load_config_file(self):
        with open(self._config_file, 'r') as inputfile:
            try:
                self.json_data = json.load(inputfile)
            except ValueError:
                logger.error("Decoding json file has failed")
            except KeyError:
                logger.error("Wrong key used to read json file")

    def get_map_paths(self):
        """ Gets maps paths from the config file """
        return self.json_data[self.MAP_HEADER][self.PATH_HEADER]

    def save_map_paths(self, path_list):
        """ Saves loaded maps paths into a json file
        :param path_list: list or tuple of paths
        """

        if isinstance(path_list, (list, tuple)) and len(path_list) > 0:
            # refreshing json data from existing file
            self.load_config_file()

            # modifying data, then write in file
            self.json_data[self.MAP_HEADER][self.PATH_HEADER] = path_list
            self.write_config_file()
        else:
            logger.error("Data is not JSON-serializable")

    def save_last_map_path(self, path):
        """ Saves the path of last loaded map, so that at next application startup,
        this map is automatically loaded.
        :param path: path of the map
        """
        if isinstance(path, (str, unicode)):
            self.load_config_file()
            self.json_data[self.LAST_MAP_HEADER] = path
            self.write_config_file()
        else:
            logger.info("The map could not be saved")

    def get_last_map_path(self):
        return self.json_data[self.LAST_MAP_HEADER]

    def write_config_file(self):
        with open(self._config_file, 'w') as outputfile:
            json.dump(self.json_data, outputfile, sort_keys=True,
                      indent=4, separators=(',', ': '))


config = Config('config.json')

if __name__ == '__main__':
    print config.get_map_paths()
    config.save_map_paths(["map", "/sdcard/kivytrek/maps"])
