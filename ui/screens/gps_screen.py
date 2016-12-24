__author__ = 'pol'

from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.properties import StringProperty
from kivy.app import App


class GPXStart(Button):
    def on_release(self):
        App.get_running_app().gps_module.set_gps_daemon_recording(True)


class GPXStop(Button):
    def on_release(self):
        App.get_running_app().gps_module.set_gps_daemon_recording(False)


class GPXStatus(Image):
    recording_image = StringProperty()
    not_recording_image = StringProperty()
