# -*- coding: utf-8 -*-

__author__ = 'pol'

from kivy.event import EventDispatcher
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.utils import platform
from kivy.lib import osc
from kivy.clock import Clock

kivytrek_port = 3001
gps_service_port = 3000


class GPS(EventDispatcher):
    """
    Handler for OSC related messages.
    """

    """Stores the position information."""
    pos = ListProperty()

    """Formatted text message, to be shown in the gui."""
    gps_location = StringProperty()

    gps_status = StringProperty('Start or stop gps recording')
    gps_daemon_recording = BooleanProperty(False)

    def __init__(self):
        """The service at the other side of the OSC communication which delivers gps location, etc."""
        self.service = None

        # TODO : emplacement temporaire pour cette méthode
        self.init_osc()

        """Speed acquired from the smartphone's GPS is supposed to be in m/s."""
        self.SPEEDS_CONVERT_FACTORS = {"km/h": 3.6, "mph": 2.23694, "m/s": 1}

        """Default speed unit for display is the first unit of the above dict."""
        self.speed_unit = "km/h"

    # Public

    def start(self):
        self.start_gps_daemon()

    def stop(self):
        if self.service is not None:
            self.service.stop()

    def set_speed_unit(self, unit_text):
        """Change the speed unit."""
        if self.SPEEDS_CONVERT_FACTORS.get(self.speed_unit) is not None:
            self.speed_unit = unit_text

    # Private

    def gps_pos_callback(self, message, *args):
        """Callback called on a new gps location event."""
        print "got a message! :", message
        lat = message[2]
        lon = message[3]
        speed = self._convert_speed(message[5])
        self.pos = [lat, lon]
        self.gps_location = "\n\
            lat=%f\n\
            lon=%f\n\
            altitude=%f\n\
            speed=%f %s\n\
            bearing=%f" % (lat, lon, message[4], speed, self.speed_unit, message[6])

    def gps_daemon_recording_callback(self, message, *args):
        """Callback called on a gpx recording status event."""
        print "got GPX recording status :", message
        self.gps_daemon_recording = message[2]

    def set_gps_daemon_recording(self, record):
        """Send an osc command for start/stop GPX recording.
        :param record: boolean that represents the recording command.
        """
        osc.sendMsg('/gpx_cmd', dataArray=[record], port=gps_service_port)

    def start_gps_daemon(self):
        """For instance, only Android is supported. An android.app.Service is created.
        On iOs, a similar approach may be needed.
        """
        if platform == 'android':
            from android import AndroidService
            service = AndroidService('KivyTrek gps service', 'running')
            service.start('service started')
            self.service = service

    def init_osc(self):
        """Initialisation of the OSC communication.
        Bindings are donne for some kings of messages.
        """
        osc.init()
        oscid = osc.listen(ipAddr='127.0.0.1', port=kivytrek_port)
        osc.bind(oscid, self.gps_pos_callback, '/gps_pos')
        osc.bind(oscid, self.gps_daemon_recording_callback, '/gpx_status')
        Clock.schedule_interval(lambda *x: osc.readQueue(oscid), 0.3)

    def _convert_speed(self, speed_in_meters_per_second):
        """Performs a conversion from a speed in meters per second to a speed in self.speed_unit."""
        speed_factor = self.SPEEDS_CONVERT_FACTORS.get(self.speed_unit)
        if speed_factor is not None:
            return speed_in_meters_per_second * speed_factor
        else:
            return speed_in_meters_per_second


