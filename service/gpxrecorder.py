# -*- coding: utf-8 -*-
__author__ = 'pla'

from gpxpy import gpx
from time import strftime
from os import makedirs
from os.path import join, exists
import media_scanner

# Don't use '/sdcard/kivytrek/gpxrecords' instead, or media_scanner won't work
GPX_RECORDS_DIR = '/storage/emulated/0/kivytrek/gpxrecords'


class GPXRecorder(object):
    def __init__(self):
        self.gpx_file = gpx.GPX()
        self.current_track = None
        self.current_segment = None
        self._is_started = False

    def start(self):
        if self._is_started:  # prevent multiple starts
            return
        self._is_started = True

        # Create a new track
        self.create_track()

        # Create a segment in our track:
        self.create_segment()

    def stop(self):
        """ Actions triggered when we stop a gpx record :
          - set the GPXReorder as stopped
          - write the content of gpx_file to a file
        """
        self._is_started = False

        date_formatted = strftime("%d-%m-%Y_%Hh%Mm%Ss")

        file_path = join(GPX_RECORDS_DIR, date_formatted + '.xml')

        # Preliminary check
        if not exists(GPX_RECORDS_DIR):
            makedirs(GPX_RECORDS_DIR)

        with open(file_path, 'w') as f:
            f.write(self.gpx_file.to_xml())

        # see media_scanner module for explanation
        media_scanner.scan_file(file_path)

    def is_recording(self):
        return self._is_started

    def create_track(self):
        self.current_track = gpx.GPXTrack()
        self.gpx_file.tracks.append(self.current_track)

    def create_segment(self):
        self.current_segment = gpx.GPXTrackSegment()
        self.current_track.segments.append(self.current_segment)

    def add_point(self, lat, lon, altitude):
        if self._is_started:
            point = gpx.GPXTrackPoint(lat, lon, elevation=altitude)
            self.current_segment.points.append(point)
