__author__ = 'pla'

'''
This part is specific to Android.
It is meant to address the following issue : newly created files by eg GPXRecorder are not visible from a PC using
MTP protocol. They are still accessible from the smartphone with apps like ES Explorer.

The trick is to use the Android API, by giving newly created files's path to the MediaScanner.
An independent app called SD Scanner uses that same principle but more extensively. And it works. Just make SD Scanner
scan the path /storage/emulated/0/kivytrek, and all GPX recordings will be accessible from MTP.
To avoid the need of using an external app just to retrieve GPX records from a PC, i created this module.

N.B : I found that it worked with paths like '/storage/emulated/0/kivytrek/gpxrecords/an_xml_file.xml', but not with
files like '/sdcard/kivytrek/gpxrecords/an_xml_file.xml'. I don't know why.
'''

from modules.myplyer.platforms.android import activity
from jnius import autoclass, java_method, PythonJavaClass

MediaScannerConnection = autoclass('android.media.MediaScannerConnection')


class MediaScannerConnectionClient(PythonJavaClass):
    __javainterfaces__ = ['android/media/MediaScannerConnection$MediaScannerConnectionClient']

    def __init__(self):
        super(MediaScannerConnectionClient, self).__init__()

    @java_method('()V')
    def onMediaScannerConnected(self):
        pass

    @java_method('(Ljava/lang/String;Landroid/net/Uri;)V')
    def onScanCompleted(self, path, uri):
        print "scan completed for ", path

# @see http://developer.android.com/reference/android/media/MediaScannerConnection.html
mediaScannerConnectionClient = MediaScannerConnectionClient()
mediaScannerConnection = MediaScannerConnection(activity.getApplicationContext(), mediaScannerConnectionClient)
mediaScannerConnection.connect()

def scan_file(file_path):
    if MediaScannerConnection.isConnected():
        mediaScannerConnection.scanFile(file_path, "application/xml")
    else:
        print "MediaScanner is not connected"

