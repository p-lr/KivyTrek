# -*- coding: utf-8 -*-
__author__ = 'peter'

import ConfigParser
from math import fabs, atan, log, exp, floor, sin, cos, atan2, sqrt, pi
import codecs

'''
KivyTrek has his own representation of tile order. Given that in kivy the window coordinate system places (0,0) at the
bottom left corner of the window, with x-axis oriented to the right and y-axis to the top, tiles are internally
reffered in that coordinate system.
So, if the tiles of the map are indexed in a different coordinate system, a Map object has to do the conversion.
That way, while KivyTrek's coordinate system remains the same, Map objects allow us to interface with different
sources of tiles.
'''

CALIBRATION_SECTION = 'Calibration points'
SETTINGS_SECTION = 'Map settings'
MAP_INFOS_SECTION = 'Map infos'


class Map(object):
    """
    Base class for all Map objects.
    """

    def __init__(self, _ini_file_path):
        # The tile size is retreived from the calibration.ini file
        self.tile_size = None
        self.max_zoom = None
        self.configParser = ConfigParser.RawConfigParser()
        self.calibration_file_path = _ini_file_path

        # For instance, we have two calibration points
        self.x1, self.y1, self.x2, self.y2 = 0, 0, 0, 0
        self.mercator_x1, self.mercator_y1, self.mercator_x2, self.mercator_y2 = 0, 0, 0, 0

        # Coefficients for mercator to map coordinates function
        self.x_coeff, self.y_coeff = 0, 0

        # Map settings section
        self.name = None
        self.description = None

        # Map infos section
        self.ext = None

        self.read_calib_file()
        self.calibrate()

    def read_calib_file(self):
        with codecs.open(self.calibration_file_path, 'r', encoding='utf-8') as f:
            self.configParser.readfp(f)
        self.x1 = self.configParser.getfloat(CALIBRATION_SECTION, 'x1')
        self.y1 = self.configParser.getfloat(CALIBRATION_SECTION, 'y1')
        self.mercator_x1 = self.configParser.getfloat(CALIBRATION_SECTION, 'mercator_x1')
        self.mercator_y1 = self.configParser.getfloat(CALIBRATION_SECTION, 'mercator_y1')
        self.x2 = self.configParser.getfloat(CALIBRATION_SECTION, 'x2')
        self.y2 = self.configParser.getfloat(CALIBRATION_SECTION, 'y2')
        self.mercator_x2 = self.configParser.getfloat(CALIBRATION_SECTION, 'mercator_x2')
        self.mercator_y2 = self.configParser.getfloat(CALIBRATION_SECTION, 'mercator_y2')

        # Map settings section
        tile_size_x = self.configParser.getint(SETTINGS_SECTION, 'tile_size_width')
        tile_size_y = self.configParser.getint(SETTINGS_SECTION, 'tile_size_height')
        self.tile_size = [tile_size_x, tile_size_y]
        self.max_zoom = self.configParser.getint(SETTINGS_SECTION, 'max_zoom')
        self.name = self.configParser.get(SETTINGS_SECTION, 'name')
        self.description = self.configParser.get(SETTINGS_SECTION, 'description')

        # Map infos section
        self.ext = self.configParser.get(MAP_INFOS_SECTION, 'ext')

    def calibrate(self):
        try:
            self.x_coeff = fabs((self.x1 - self.x2) / (self.mercator_x1 - self.mercator_x2))
            self.y_coeff = fabs((self.y1 - self.y2) / (self.mercator_y1 - self.mercator_y2))
        except ZeroDivisionError:
            print "Zero division"

    def write_calib_file(self):
        self.configParser.set(CALIBRATION_SECTION, 'x1', self.x1)
        self.configParser.set(CALIBRATION_SECTION, 'y1', self.y1)
        self.configParser.set(CALIBRATION_SECTION, 'mercator_x1', self.mercator_x1)
        self.configParser.set(CALIBRATION_SECTION, 'mercator_y1', self.mercator_y1)
        self.configParser.set(CALIBRATION_SECTION, 'x2', self.x2)
        self.configParser.set(CALIBRATION_SECTION, 'y2', self.y2)
        self.configParser.set(CALIBRATION_SECTION, 'mercator_x2', self.mercator_x2)
        self.configParser.set(CALIBRATION_SECTION, 'mercator_y2', self.mercator_y2)

        with open(self.calibration_file_path, 'wb') as configfile:
            self.configParser.write(configfile)

    def get_tile(self, zoom, x, y):
        """ Returns a ProxyImage if the corresponding image is found, otherwise returns None."""
        raise NotImplementedError

    def get_tile_size(self):
        return self.tile_size

    def get_max_zoom(self):
        if self.max_zoom is not None:
            return self.max_zoom
        else:
            return 66

    def get_map_coord(self, lat, lon):
        """
        Given the wgs84 coordinates, a Map object can return the coordinates on the map.
        :param lat: latitude
        :param lon: longitude
        :return: coordiantes in pixels
        """
        merc_x, merc_y = Map.to_web_mercator(lat, lon)
        return self._map_projection_to_map_coord(merc_x, merc_y)

    def _map_projection_to_map_coord(self, merc_x, merc_y):
        x = self.x_coeff * (merc_x - self.mercator_x2) + self.x2
        y = self.y_coeff * (merc_y - self.mercator_y2) + self.y2
        return x, y

    def map_coord_to_map_projection(self, x, y):
        merc_x = (x - self.x2) / self.x_coeff + self.mercator_x2
        merc_y = (y - self.y2) / self.y_coeff + self.mercator_y2
        return merc_x, merc_y

    @staticmethod
    def to_web_mercator(latitude, longitude):
        """
        Conversion from WGS84 coordinates to ESPG:3857 (Google web mercator).
        :param latitude: latitude in decimal degrees
        :param longitude: longitude in decimal degrees
        :return: (X, Y) ESPG:3857 coordinates
        """
        if fabs(longitude > 180) or fabs(latitude) > 90:
            print "gros boulet"
            return

        num = longitude * 0.017453292519943295  # 2*pi/360
        merc_x = 6378137.0 * num
        a = latitude * 0.017453292519943295
        merc_y = 3189068.5 * log((1.0 + sin(a)) / (1.0 - sin(a)))

        return merc_x, merc_y

    @staticmethod
    def to_geographic(merc_x, merc_y):
        """
        Conversion from ESPG:3857 coordinates to WGS84 (latitude, longitude).
        :param merc_x:  X in meters
        :param merc_y:  Y in meters
        :return: (lat, lon) in decimal degrees
        """
        if fabs(merc_x < 180) and fabs(merc_y) < 90:
            print "mercator coordinates not in permissive range (too small)"
            return
        if fabs(merc_x > 20037508.3427892) or fabs(merc_y) > 20037508.3427892:
            print "mercator coordinates not in permissive range (too high)"
            return

        num3 = merc_x / 6378137.0
        num4 = num3 * 57.295779513082323
        num5 = floor((num4 + 180.0) / 360.0)
        lon = num4 - (num5 * 360.0)
        num6 = 1.5707963267948966 - (2.0 * atan(exp((-1.0 * merc_y) / 6378137.0)))
        lat = num6 * 57.295779513082323

        return lat, lon

    @staticmethod
    def distance(lat1, lon1, lat2, lon2):
        """
        Computes the distance between two points given their latitude and longitude.
        This uses the ‘haversine’ formula to calculate the great-circle distance between the two points – that is,
        the shortest distance over the earth’s surface – giving an ‘as-the-crow-flies’ distance between the points
        (ignoring any hills they fly over, of course!).
        NB : The average radius of earth is 6371 km.
        :param lat1: latitude of the first point, in decimal degrees
        :param lon1: longitude of the first point, in decimal degrees
        :param lat2: latitude of the second point, in decimal degrees
        :param lon2: longitude of the second point, in decimal degrees
        :return: The distance between the two points, in meters
        """
        to_rad = 0.017453292519943295  # 2*pi/360
        a = sin((lat2-lat1) * to_rad / 2)**2 +\
            cos(lat1 * to_rad) * cos(lat2 * to_rad) *\
            sin((lon2-lon1) * to_rad / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return 6371000 * c

    @staticmethod
    def distance_approx(lat1, lon1, lat2, lon2):
        """
        Computes the distance between two points given their latitude and longitude.
        This uses the polar coordinates and the planar law of cosines for computing short distances.
        This method is still valid near poles. Even at 88 degrees latitude, the polar error can be
        as large as 20 meters when the distance between the points is 20 km.
        This method is less precise than the haversine method.
        NB : The average radius of earth is 6371 km.
        :param lat1: latitude of the first point, in decimal degrees
        :param lon1: longitude of the first point, in decimal degrees
        :param lat2: latitude of the second point, in decimal degrees
        :param lon2: longitude of the second point, in decimal degrees
        :return: The distance between the two points, in meters
        """
        to_rad = 0.017453292519943295  # 2*pi/360
        lat1 *= to_rad
        lat2 *= to_rad
        lon1 *= to_rad
        lon2 *= to_rad
        a = pi / 2 - lat1
        b = pi / 2 - lat2
        c = sqrt(a**2 + b**2 - 2 * a * b * cos(lon2 - lon1))
        return 6371000 * c
