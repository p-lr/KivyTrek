__author__ = 'pla'
from kivy.event import EventDispatcher
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty
from modules.myplyer import rotation
from kivy.animation import Animation

class Compass(EventDispatcher):
    azimuth = NumericProperty(0)
    compass_status = StringProperty("Start compass")
    NOT_IMPLEMENTED = "Rotation is not implemented for your platform"

    def __init__(self):
        self._anim = None
        self.sensorEnabled = False
        self.drift = 0
        self._azimuth_old = 0

    def toggle_state(self):
        try:
            if not self.sensorEnabled:
                rotation.enable()
                Clock.schedule_interval(self.get_readings, 1 / 20.)

                self.sensorEnabled = True
                self.compass_status = "Stop compass"
            else:
                rotation.disable()
                Clock.unschedule(self.get_readings)

                self.sensorEnabled = False
                self.compass_status = "Start compass"
        except NotImplementedError:
            import traceback

            traceback.print_exc()
            self.compass_status = self.NOT_IMPLEMENTED

    def get_readings(self, dt):
        val = rotation.rotation

        azimuth = val[0]
        if azimuth - self._azimuth_old > 180:
            self.drift -= 360
        elif azimuth - self._azimuth_old < -180:
            self.drift += 360
        self._azimuth_old = azimuth
        azimuth += self.drift

        # animate the compass
        if self._anim:
            self._anim.stop(self)
        self._anim = Animation(azimuth=azimuth, d=0.3, t='linear')
        self._anim.start(self)

    def start(self):
        try:
            rotation.enable()
        except NotImplementedError:
            print self.NOT_IMPLEMENTED

    def stop(self):
        try:
            rotation.disable()
        except NotImplementedError:
            print self.NOT_IMPLEMENTED

