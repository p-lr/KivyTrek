# -*- coding: utf-8 -*-
__author__ = 'peter'
__version__ = '1.0.0'

import kivy
kivy.require('1.9.0')

# Make double-tap easy on a smartphone
from kivy.config import Config
Config.set('postproc', 'double_tap_time', '800')

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from ui.components.Options import ImageButton, ReticuleDropDown
from ui.screens.gps_screen import GPXStart, GPXStop, GPXStatus
from app.modules.gps import GPS
from instruments.compass import Compass
from app.core.MapBoard import MapBoard
from app.core.MapCalibrator import MapCalibrator
from app.loader.MapLoader import MapLoader
from os.path import dirname, join
from ui.components.MapChoice import MapChoice, MapItem
# from ui.components.MapChoice2 import MapChoice2
from functools import partial
from ui.components.settings import CustomSettingItem, CategoryTitle


class ShowcaseScreen(Screen):
    fullscreen = BooleanProperty(False)
    scroll_y = BooleanProperty(False)

    def add_widget(self, *args):
        if 'content' in self.ids:
            return self.ids.content.add_widget(*args)
        return super(ShowcaseScreen, self).add_widget(*args)

    def remove_widget(self, widget):
        super(ShowcaseScreen, self).remove_widget(widget)


class KivyTrekApp(App):
    MAP_SCREEN_ID = 'MAP_SCREEN'
    OPTIONS_SCREEN_ID = 'OPTIONS_SCREEN'
    GPS_SCREEN_ID = 'GPS_SCREEN'
    MAP_CHOICE_ID = 'MAP_CHOICE'
    COMPASS_SCREEN_ID = 'COMPASS_SCREEN'
    CALIBRATION_SCREEN_ID = 'CALIB_SCREEN'

    DEFAULT_RETICULE = 'data/reticule_blue_cross.png'

    def build(self):
        self.screens = {}
        '''Dict of screens. E.g, the 'MAP_SCREEN' key identifies the screen-map.
        '''

        self.map_board = MapBoard(KivyTrekApp.DEFAULT_RETICULE)

        self.map_calibrator = None

        self.gps_module = GPS()
        self.gps_module.start()

        self.compass_module = Compass()

        # Update the list of maps, and load the former map if available.
        MapLoader.generate_maps()
        self.load_former_map()

        # We bind the event of localisation with MapBoard.on_pos_update which then,
        # among other things, calls the map's localisation update callback.
        self.gps_module.bind(pos=self.map_board.on_pos_update)

        # Orientation event bind.
        self.compass_module.bind(azimuth=self.map_board.mapviewer.update_azimuth)

    def show_screen(self, screen_name, create_action):
        """Shows a screen and creates it if it doesn't exists."""
        if screen_name not in self.screens:
            create_action()
        if self.root.ids.sm.current != screen_name:
            self.root.ids.sm.switch_to(self.screens[screen_name], direction='left')

    def load_former_map(self):
        """Loads the map viewed in the last session of KivyTrek."""
        map_ = MapLoader.get_former_map()
        if map_ is not None:
            self.map_board.mapviewer.view_map(map_)

    def show_map_choices(self):
        """Shows the list of maps."""
        # Generation of the model for the map choice view.
        map_list = MapLoader.map_list
        map_items = []
        for map_ in map_list:
            map_items.append(MapItem(
                name=map_.name,
                action=partial(self.map_board.mapviewer.view_map, map_),
                calibration_action=partial(self.show_calibration, map_),
                max_zoom=map_.max_zoom,
                description=map_.description
                )
            )

        # The commented code below is the building of the data for a Recycleview (MapChoice2 implementation). See the
        # doc of MapChoice2 for explanation.
        # index = 0
        # for map_ in map_list:
        #     map_items.append({
        #         "name": map_.name,
        #         "description": map_.description,
        #         "max_zoom": map_.max_zoom,
        #         "action": partial(self.map_board.mapviewer.view_map, map_),
        #         "height": 130,
        #         "index": index,
        #         "viewclass": "MapItem"
        #     })
        #     index += 1

        screen = ShowcaseScreen(name=KivyTrekApp.MAP_CHOICE_ID)
        screen.add_widget(MapChoice(width=800, map_items=map_items))
        # screen.add_widget(MapChoice2(map_items=map_items))
        screen.fullscreen = True
        screen.scroll_y = True      # important
        self.screens[KivyTrekApp.MAP_CHOICE_ID] = screen

    def load_map(self):
        """Only called once, when the 'Map' button in the menu is pressed."""
        screen = ShowcaseScreen(name=KivyTrekApp.MAP_SCREEN_ID)
        screen.add_widget(self.map_board)
        screen.fullscreen = True
        self.screens[KivyTrekApp.MAP_SCREEN_ID] = screen

    def load_options(self):
        """Loads the options screen."""
        screen = self.load_screen('options.kv')
        screen.ids.ddbtn.dropdown.bind(on_select=lambda instance, x: self.map_board.load_reticule(x))
        screen.ids.gps_units_id.content.bind(text=lambda instance, x: self.gps_module.set_speed_unit(x))
        screen.name = KivyTrekApp.OPTIONS_SCREEN_ID
        screen.scroll_y = True
        screen.fullscreen = False
        self.screens[screen.name] = screen

    def load_gps_info(self):
        screen = self.load_screen('gps_screen.kv')
        screen.name = KivyTrekApp.GPS_SCREEN_ID
        self.screens[screen.name] = screen

    def load_compass(self):
        """Loads the compass instrument."""
        screen = self.load_screen('compass.kv')
        screen.name = KivyTrekApp.COMPASS_SCREEN_ID
        screen.fullscreen = True
        self.screens[screen.name] = screen

    def load_calibration(self):
        """Loads the calibration screen. Provides an interface to calibrate a map."""
        screen = ShowcaseScreen(name=KivyTrekApp.CALIBRATION_SCREEN_ID)
        self.map_calibrator = MapCalibrator()
        screen.add_widget(self.map_calibrator)
        screen.fullscreen = True
        self.screens[KivyTrekApp.CALIBRATION_SCREEN_ID] = screen

    def show_calibration(self, map):
        self.show_screen(KivyTrekApp.CALIBRATION_SCREEN_ID, self.load_calibration)
        self.map_calibrator.load_map(map)

    # TODO : virer cette méthode quand MapCalibrator est fonctionnel.
    def toggle_calib_ret(self, value):
        if value:
            self.map_board.add_widget(self.map_board.reticule_calib)
        else:
            self.map_board.remove_widget(self.map_board.reticule_calib)

    @staticmethod
    def load_screen(screen_file):
        curdir = dirname(__file__)
        screen = Builder.load_file(join(curdir, 'ui', 'screens', screen_file.lower()))
        return screen

    def should_stop_gps_daemon(self):
        return not self.gps_module.gps_daemon_recording

    def on_pause(self):
        if self.should_stop_gps_daemon():
            self.gps_module.stop()
        self.compass_module.stop()
        return True

    def on_resume(self):
        self.gps_module.start()
        if self.compass_module.sensorEnabled:
            self.compass_module.start()

    def toggle_compass_view(self):
        self.compass_module.toggle_state()
        if self.compass_module.sensorEnabled:
            self.map_board.show_orientation_arrow()
        else:
            self.map_board.hide_orientation_arrow()


if __name__ in ('__android__', '__main__'):
    KivyTrekApp().run()
