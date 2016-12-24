# -*- coding: utf-8 -*-
__author__ = 'peter'

from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.lang import Builder
from app.core.MapBoard import MapViewer
from app.modules.log import logger

Builder.load_string("""
<CalibrationPointChooser>:
    delta: app.root.ids.actbar.height
    ToggleButton:
        pos: root.window_size[0] - 136 * 2 - 10, root.window_size[1] - 136 - root.delta - 5
        size: 136, 136
        background_normal: 'data/reticules/calibration/ret1_calib_up.png'
        background_down: 'data/reticules/calibration/ret1_calib_down.png'
    ToggleButton:
        pos: root.window_size[0] - 136 - 5, root.window_size[1] - 136 - root.delta - 5
        size: 136, 136
        background_normal: 'data/reticules/calibration/ret2_calib_up.png'
        background_down: 'data/reticules/calibration/ret2_calib_down.png'
""")


class ReticuleCalib(Scatter):
    # The widget shouldn't be rotated nor scaled
    do_rotation = False
    do_scale = False

    # The local position of the reticule in the MapViewer
    pos_local = 0, 0

    def __init__(self, **kwargs):
        super(ReticuleCalib, self).__init__(**kwargs)
        self.image = Image(source='data/reticules/calibration/reticule_calib_lock.png')
        self.image.size = self.image.texture_size
        self.add_widget(self.image)

        self.x_value = TextInput()
        self.x_value.background_color = (1, 1, 1, 0.7)
        self.add_widget(self.x_value)

        # TODO : petit souci de design. Le positionnement du réticule de calib se fait par set du center du widget. Or,
        # si on étend sa taille au delà de celle de l'image du réticule, le positionnement ne sera pas bon.
        self.size = self.image.texture_size

    def on_touch_down(self, touch):
        super(ReticuleCalib, self).on_touch_down(touch)
        if self.collide_point(*touch.pos):
            self.parent.getCalibrationCoord(self, *touch.pos)
            return True
        return False

    def on_touch_up(self, touch):
        super(ReticuleCalib, self).on_touch_up(touch)
        if self.collide_point(*touch.pos):
            self.pos_local = self.parent.mapviewer.to_local(*self.center)
            return True
        return False


class CalibrationPointChooser(Widget):
    window_size = Window.size


class MapCalibrator(Widget):
    def __init__(self, **kwargs):
        super(MapCalibrator, self).__init__(**kwargs)

        # Create the map viewer
        self.mapviewer = MapViewer(**kwargs)
        self.add_widget(self.mapviewer)

        # Create and add calibration reticules
        self.reticule1 = ReticuleCalib()
        self.reticule2 = ReticuleCalib()
        self.add_widget(self.reticule1)
        self.add_widget(self.reticule2)

        # Create the calibration point chooser:
        self.calib_point_chooser = CalibrationPointChooser()
        self.add_widget(self.calib_point_chooser)

    def load_map(self, _map):
        """Loads the map for calibration.
        Depending on the number of reticules, the MapViewer object is configured accordingly.
        """
        self.mapviewer.view_map_for_calibration(_map)
        self.mapviewer.add_movable_widget(self.reticule1)
        self.mapviewer.add_movable_widget(self.reticule2)

        # Position the reticule n°1 at the top left corner
        top_right = (0, _map.get_tile_size()[1])
        self.mapviewer.set_movable_widget_pos(self.reticule1, *top_right)
        self.reticule1.pos_local = top_right  # update the local position

        # Position the reticule n°2 at the bottom right corner
        bottom_left = (_map.get_tile_size()[0], 0)
        self.mapviewer.set_movable_widget_pos(self.reticule2, *bottom_left)
        self.reticule2.pos_local = bottom_left  # update the local position

    def getCalibrationCoord(self, widget, *p):
        logger.debug("pos du clic (relatif) (%s, %s)" % self.mapviewer.to_local(*p))
        logger.debug(
            "pos du centre du reticule (relatif): (%s, %s)" % self.mapviewer.to_local(*widget.center))
