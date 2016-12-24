# -*- coding: utf-8 -*-
__author__ = 'pla'

# Tweak to have the modules.myplyer module importable.
if __name__ == "__main__" and __package__ is None:
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from time import sleep
from kivy.lib import osc
from modules.myplyer import gps
from service.gpxrecorder import GPXRecorder

kivytrek_port = 3001
service = 3000

gpx_record = None


def record_gpx(message, *args):
    """Here we process a request from KivyTrek which asks for start or stop the GPX record.
    We also ensure that we only create a new GPXRecorder instance when none exists, ie when
    this is the first recording or when the previous one was stopped.
    """
    print "got a message! :", message
    if message[1] == ',i' and len(message) > 2:
        global gpx_record
        # TODO : définir précisément le format attendu pour 'message'
        if message[2]:
            if gpx_record is None:
                # create and start GPX recording
                gpx_record = GPXRecorder()
            gpx_record.start()
        else:
            if gpx_record is not None:
                gpx_record.stop()
            gpx_record = None


def on_location(**kwargs):
    lat = kwargs.get('lat')
    lon = kwargs.get('lon')
    alt = kwargs.get('altitude')
    speed = kwargs.get('speed')
    bearing = kwargs.get('bearing')

    osc.sendMsg('/gps_pos', [lat, lon, alt, speed, bearing], port=kivytrek_port)

    if gpx_record is not None:
        gpx_record.add_point(lat, lon, alt)


def on_status(stype, status):
    osc.sendMsg('/gps_status', [stype, status], port=kivytrek_port)


def send_gpx_rec_status():
    """Sends the service status is_recording. That way, even if KivyTrek is stopped, upon
    restart of the application we are aware that the service is recording the gps position.
    Then, KivyTrek's interface can display that information accordingly.
    """
    if gpx_record is not None:
        rec_status = gpx_record.is_recording()
    else:
        rec_status = False
    osc.sendMsg('/gpx_status', dataArray=[rec_status], port=kivytrek_port)


if __name__ == '__main__':
    # Initialisation and configuration of OSC communication
    osc.init()
    oscid = osc.listen(ipAddr='127.0.0.1', port=service)
    osc.bind(oscid, record_gpx, '/gpx_cmd')

    # Configure and launch the gps module from plyer
    try:
        gps.configure(on_location=on_location, on_status=on_status)
    except NotImplementedError:
        import traceback
        traceback.print_exc()
        quit()

    gps.start()

    while True:
        osc.readQueue(oscid)
        sleep(1)
        send_gpx_rec_status()
