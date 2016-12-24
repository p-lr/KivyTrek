# -*- coding: utf-8 -*-
__author__ = 'peter'

from kivy.core.window import Window
from kivy.vector import Vector
from kivy.graphics.transformation import Matrix
from kivy.uix.scatter import ScatterPlane, Scatter
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.properties import NumericProperty, StringProperty, AliasProperty, ObjectProperty
from kivy.animation import Animation
from kivy.metrics import dp
from app.loader.Map import Map
from app.modules.log import logger
from app.modules.config import config
from kivy.clock import Clock
from TileUtils import TileCache, Tile, TILES_MAX_NUMBER
from kivy.graphics import Rectangle, Line, Color, InstructionGroup
from kivy.lang import Builder
from math import log

from functools import partial

from kivy.loader import Loader

Loader.max_upload_per_frame = 4
UPDATE_DELAY = 0.5
CLEANUP_DELAY = 5

Builder.load_string("""
<OrientationArrow>:
    azimuth: root.azimuth
    size: self.texture_size
    source: 'data/orientation-arrow.png'
    canvas.before:
        PushMatrix
        Rotate:
            angle: self.azimuth
            axis: 0, 0, 1
            origin: self.center
    canvas.after:
        PopMatrix

<CompassButton>:
    background_normal: 'data/buttons/compass/compass_button_up.png'
    background_down: 'data/buttons/compass/compass_button_down.png'
    size: 156, 156
    x: 5
    y: 5
    on_press: app.toggle_compass_view()

<CenterPosButton>:
    background_normal: 'data/buttons/centerpos/center_on_pos_button_up.png'
    background_down: 'data/buttons/centerpos/center_on_pos_button_down.png'
    background_lock: 'data/buttons/centerpos/center_on_pos_button_down_lock.png'
    size: 156, 156
    x: 166
    y: 5

<PathButton>:
    background_normal: 'data/buttons/path/path_button_up.png'
    background_down: 'data/buttons/path/path_button_down.png'
    size: 156, 156
    x: 327
    y: 5

<DistanceLabel>:
    background_color: (1, 1, 1, 0.7)
    size: self.texture_size
    canvas.before:
        Color:
            rgba: self.background_color
        Rectangle:
            pos: self.x - dp(3), self.y - dp(1)
            size: self.texture_size[0] + dp(6), self.texture_size[1] + dp(2)

<DistToCenterButton>:
    background_normal: 'data/buttons/distcenter/dist_to_center_button_up.png'
    background_down: 'data/buttons/distcenter/dist_to_center_button_down.png'
    size: 156, 156
    x: 488
    y: 5
""")


class OrientationArrow(Image):
    azimuth = NumericProperty(0)


class CompassButton(ToggleButton):
    pass


class PathButton(ToggleButton):
    pass


class CenterPosButton(Button):
    background_lock = StringProperty()
    background_down_orig = 'data/buttons/centerpos/center_on_pos_button_down.png'

    def __init__(self, **kwargs):
        self.register_event_type('on_lock')
        self.register_event_type('on_unlock')
        self.register_event_type('on_center_on_last_pos')
        super(CenterPosButton, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if not self.collide_point(touch.x, touch.y):
            return False
        if touch.is_double_tap:
            self.state = 'down'
            self.background_down = self.background_lock
            self.dispatch('on_lock')
            return True
        else:
            if self.background_down == self.background_lock:
                self.background_down = self.background_down_orig
                self.dispatch('on_unlock')
            else:
                self.background_down = self.background_down_orig
                self.dispatch('on_center_on_last_pos')

        return super(CenterPosButton, self).on_touch_down(touch)

    def on_lock(self):
        pass

    def on_unlock(self):
        pass

    def on_center_on_last_pos(self):
        pass


class DistanceLabel(Label):
    pass


class DistToCenterWidget(Scatter):
    def __init__(self, **kwargs):
        kwargs.setdefault('do_rotation', False)
        kwargs.setdefault('do_scale', False)
        kwargs.setdefault('do_translation_x', False)
        kwargs.setdefault('do_translation_y', False)
        super(DistToCenterWidget, self).__init__(**kwargs)

        self.image = Image(source='data/reticules/distcenter/dist_to_center_reticule.png')
        self.image.size = self.image.texture_size
        self.add_widget(self.image)

        self.label = DistanceLabel()
        self.label.markup = True
        self.label.pos = self.image.width + dp(5), self.image.height / 2 - dp(8)
        self.add_widget(self.label)

        self.pos = Window.size[0] / 2 - self.image.width / 2, Window.size[1] / 2 - self.image.height / 2

    def set_distance(self, value):
        """
        :param value: distance in meters
        """
        if value > 1000:
            text = str(round(value / 1000, 3)) + ' km'
        elif value == -1:
            text = '∞'
        else:
            text = str(int(value)) + ' m'
        self.label.text = '[color=2962ff]%s[/color]' % text


class DistToCenterButton(ToggleButton):
    pass


class RepositionExecutor(object):
    """A container for tasks relative to updating the position of some widgets."""
    def __init__(self, dt=0.1):
        self.task_list_delayed = []
        self.task_list = []
        self.dt = dt

    # Public api
    def execute(self):
        self._task_list_exec()
        if self.task_list_delayed:
            Clock.schedule_once(self._task_list_delayed_exec, self.dt)

    def add_delayed_reposition_task(self, callable_):
        self.task_list_delayed.append(callable_)

    def add_reposition_task(self, callable_):
        self.task_list.append(callable_)

    # Private api
    def _task_list_delayed_exec(self, dt):
        for task in self.task_list:
            task()

    def _task_list_exec(self):
        for task in self.task_list:
            task()


class MapViewer(ScatterPlane):
    def __init__(self, **kwargs):
        kwargs.setdefault('do_rotation', False)
        kwargs.setdefault('show_border', False)
        kwargs.setdefault('close_on_idle', False)
        kwargs.setdefault('scale_min', 1)
        super(MapViewer, self).__init__(**kwargs)  # init ScatterPlane with above parameters

        self.map = None

        self.tilesize = (0, 0)
        self.tileCache = TileCache()

        self._zoom = 0  # intern var managed by a property
        self.reticule = None
        self.show_arrow = False
        self.arrow = type('DefaultArrow', (), {'azimuth': 0})  # creation a a default object, so azimth can still be set

        self.idle = True  # used by self.update

        # variable contenant la dernière position gps
        self.last_pos = (0, 0)
        self.last_pos_wgs84 = (0, 0)

        self.locked_on_pos = False

        # The path
        self.path = None
        self.path_width = 5.0
        self.tracking_path = False
        self._path_zoom = 0  # intern var to track a zoom change

        # Layers
        self.map_layer = None
        self.path_layer = None

        # Variables relative to layers
        self.map_cleanup_scheduled = False

        # Reposition tasks
        self.reposition_executor = None

        # Finally, as every user action implies a change of x and/or y value,
        # we bind those properties change on the update
        self.bind(x=self.update, y=self.update)

    def view_map(self, _map):
        # Prepare the map
        self._prepare_map(_map)

        # Set the last pos in map coord if possible
        self._init_last_pos(_map)

        # Adding the map layer
        self.map_layer = InstructionGroup()
        self.canvas.add(self.map_layer)

        # Adding the path layer
        self.path_layer = InstructionGroup()
        self.path_layer.add(Color(1, 0, 0, 0.5))
        self.path = Line(width=self.path_width)
        self.path_layer.add(self.path)
        self.canvas.add(self.path_layer)

        # Creation of the reposition task executor
        # Update the reticule and if needed the arrow position
        self.reposition_executor = RepositionExecutor(0.1)
        if self.reticule is not None:
            self.reposition_executor.add_reposition_task(lambda: self.set_reticule_pos(*self.last_pos))
        self.reposition_executor.add_reposition_task(lambda: self.set_arrow_pos())

        # The first time we view a map we have to trigger the first tile drawing and reposition the reticule
        Clock.schedule_once(self.update_map, 0)
        self.reposition_executor.execute()

    def view_map_for_calibration(self, _map):
        # Prepare the map
        self._prepare_map(_map)

        # Adding the map layer
        self.map_layer = InstructionGroup()
        self.canvas.add(self.map_layer)

        # Creation of the reposition task executor
        self.reposition_executor = RepositionExecutor(0.1)

        # The first time we view a map we have to trigger the first tile drawing and reposition the reticule
        Clock.schedule_once(self.update_map, 0)

    def _prepare_map(self, _map):
        # Cleanup the canvas, reinitialize variables
        self.canvas.clear()
        self.idle = True
        self.scale = 1
        self.pos = 0, 0
        self.tileCache.__init__()

        self.map = _map
        self.tilesize = _map.get_tile_size()

        # Here we set the maximum scale of the Scatter, information retrieved from max_zoom in calibration.ini
        self.scale_max = pow(2, _map.get_max_zoom())

        # Save the path of the map's calibration file in application settings
        config.save_last_map_path(_map.calibration_file_path)

    def update(self, obj, value, delay=UPDATE_DELAY):
        """
        To prevent overuse of update_map, each change of position triggers an update of the map after UPDATE_DELAY sec.
        For instance, the position of the reticule has to be updated.
        """
        if self.map is None:
            return

        # Pause the Loader, to prevent ui blocking
        Loader.pause()

        # Reposition widgets that need to be repositioned
        self.reposition_executor.execute()

        # Trigger the map update
        if self.idle:
            self.idle = False
        else:
            Clock.unschedule(self.update_map)
        Clock.schedule_once(self.update_map, delay)

        # Resume the Loader after a short time
        Clock.schedule_once(MapViewer.resume_loading, 0.1)

    def update_map(self, dt):
        # First, we get the current area covered on the ScatterPlane
        area = self.get_covered_area()
        map_area = (0, 0, self.tilesize[0], self.tilesize[1])

        # Then, we make the list of tiles corresponding to that area
        tile_list = self.generate_tile_list(self.zoom, map_area, area)

        # Before drawing the tiles, we may have to perform a cleanup of the map layer
        if self.map_cleanup_scheduled:
            self.map_layer.clear()
            self.tileCache.__init__()
            self.map_cleanup_scheduled = False

        # Tiles drawing
        self.draw_tiles(tile_list)

        # We schedule a cleanup, which will be done if the app is inactive at the time of the callback execution
        Clock.schedule_once(partial(self.cleanup, tile_list), CLEANUP_DELAY)

        self.idle = True
        # logger.debug("container : %s" % self.tileCache.container.values())

        # If we are showing the path, we update its view (adjust the thickness)
        if self.tracking_path:
            self.format_path()

    @staticmethod
    def resume_loading(dt):
        Loader.resume()

    @property
    def zoom(self):
        """Get zoom from current scale"""
        # At each zoom step forward, we cover an area twice as small as the former area
        self._zoom = log(self.scale, 2)
        return self._zoom

    def get_covered_area(self):
        parent = self.parent
        xmin = parent.x
        xmax = parent.x + parent.width
        ymin = parent.y
        ymax = parent.y + parent.height

        # Coordinates in ScatterPlane
        # Here, local and window coordinates are the same because ScatterPlane's origin
        # corresponds to the windows's origin
        xmin, ymin = self.to_local(xmin, ymin)  # (x,y) coord of the bottom left corner
        xmax, ymax = self.to_local(xmax, ymax)  # (x,y) coord of the top right corner

        return xmin, ymin, xmax, ymax

    def out_of_scope(self):
        logger.debug("OUT OF SCOPE")
        return []

    @staticmethod
    def extend_tile_view(tab, maxindex):
        if len(tab):
            if tab[0] > 0:
                tab.insert(0, tab[0] - 1)
            if tab[-1] < maxindex - 1:
                tab.append(tab[-1] + 1)

    def generate_tile_list(self, zoom, map_area, area):
        """ Generates the list of tiles that should be visible for the given zoom level
         and the area visible on the scatterPlane """
        xmin0, ymin0, xmax0, ymax0 = map_area  # area for zoom=0, one unique tile
        xmin, ymin, xmax, ymax = area

        # Overlap test
        if xmax <= xmin0 or xmin >= xmax0 or ymin >= ymax0 or ymax <= ymin0:
            return self.out_of_scope()

        # coordinates of the intersection between map_area and area
        xmin_inter = max(xmin0, xmin)
        xmax_inter = min(xmax0, xmax)
        ymin_inter = max(ymin0, ymin)
        ymax_inter = min(ymax0, ymax)

        # If the current zoom is already an integer, we take its value.
        # Otherwise, we take its superior int value because we want to
        # identify which tiles of the next zoom level have to be displayed
        zoom_int = int(zoom if zoom == int(zoom) else int(zoom) + 1)
        targeted_scale = pow(2, zoom_int)
        tile_width = (xmax0 - xmin0) / float(targeted_scale)

        startx_index = int(xmin_inter / tile_width)
        endx_index = int(xmax_inter / tile_width)

        # Calculation of the indexes on x axis
        x_indexes = []
        append = x_indexes.append
        for x in range(startx_index, endx_index + 1):
            append(x)
        MapViewer.extend_tile_view(x_indexes, targeted_scale)

        starty_index = int(ymin_inter / tile_width)
        endy_index = int(ymax_inter / tile_width)

        # Calculation of the indexes on y axis
        y_indexes = []
        append = y_indexes.append
        for y in range(starty_index, endy_index + 1):
            append(y)
        MapViewer.extend_tile_view(y_indexes, targeted_scale)

        tile_list = []
        append = tile_list.append
        for x in x_indexes:
            for y in y_indexes:
                tile = Tile()
                # tile.canvas = self.canvas
                tile.pos = Vector(x, y) * tile_width
                tile.size = (tile_width, tile_width)
                tile.x = x
                tile.y = y
                tile.zoom = zoom_int
                append(tile)

        return tile_list

    # The good damn right way to do it
    def draw_tile(self, proxy):
        if proxy.image.texture:
            self.map_layer.add(
                Rectangle(pos=proxy.pos, size=proxy.size, texture=proxy.image.texture, group=proxy.zoom))

    def draw_tiles(self, tile_list):
        for tile in tile_list:
            image_id = tile.get_id()
            if self.tileCache.add_tile(tile.zoom, image_id):
                image = self.map.get_tile(tile.zoom, tile.x, tile.y)
                if image is None:
                    continue
                image.create_property("pos", tile.pos)
                image.create_property("size", tile.size)
                image.create_property("zoom", str(int(tile.zoom)))
                image.bind(on_load=self.draw_tile)
                # if image.loaded:    # only useful when Loader actually caches images
                #     image.dispatch("on_load")

    def cleanup(self, tile_list, *largs):
        """
        Cleanup is achieved when the app is considered inactive, ie when self.idle = True.
        """
        if not self.idle:
            return
        zoom = self.zoom
        zoom_int = int(zoom if zoom == int(zoom) else int(zoom) + 1)

        print "debut cleanup, conserve zoom", zoom_int
        for _zoom in TileCache.get_unnecessary_zooms(self.tileCache.container.keys(), zoom_int):
            try:
                print "suppr zoom", _zoom
                self.map_layer.remove_group(str(_zoom))
                self.tileCache.remove_tiles_for_zoom(_zoom)
            except:
                logger.debug("the canvas doesn't contains the zoom %s" % _zoom)

        if self.tileCache.is_tile_overfull(zoom_int):
            self.map_cleanup_scheduled = True

        # logger.debug("cleanup done, container : %s" % self.tileCache.container.values())

    def set_reticule(self, reticule):
        self.reticule = reticule

    def set_reticule_pos(self, x, y):
        """
        :param x: x position on the map in the range [0,tile_width]
        :param y: y position on the map in the range [0,tile_height]
        :return:
        """
        # TODO : remplacer cette méthode par set_movable_widget_pos ? (cf plus bas)
        self.reticule.set_center_x(self.x + x * self.scale)
        self.reticule.set_center_y(self.y + y * self.scale)

    def set_movable_widget_pos(self, widget, x, y):
        """
        Position a widget given the local coordinates of its center.
        :param x: x position on the map in the range [0,tile_width]
        :param y: y position on the map in the range [0,tile_height]
        """
        if widget:
            widget.set_center_x(self.x + x * self.scale)
            widget.set_center_y(self.y + y * self.scale)

    def add_movable_widget(self, widget):
        """Actions done when a movable widget is added to the MapViewer."""

        # Add a reposition task
        self.reposition_executor.add_reposition_task(lambda: self.set_movable_widget_pos(
            widget, *widget.pos_local))

    def set_arrow_pos(self):
        """Must be called after set_reticule_pos"""
        if self.show_arrow:
            self.arrow.set_center_x(self.reticule.get_center_x())
            self.arrow.set_center_y(self.reticule.get_center_y())

    def set_orientation_arrow(self, arrow):
        self.show_arrow = True
        self.arrow = arrow

    def update_azimuth(self, instance, angle):
        self.arrow.azimuth = -angle

    def _init_last_pos(self, _map):
        """Initialize the last position in the _map projection coordinates, given the last known wgs84 position.
        This is used in view_map method.
        """
        if self.last_pos_wgs84 is not None:
            self.last_pos = _map.get_map_coord(*self.last_pos_wgs84)
        else:
            self.last_pos = (0, 0)

    def update_pos(self, instance, value):
        # Remember the position, even if there is no map
        self.last_pos_wgs84 = value

        # If there is no map, no need to go further
        if self.map is None:
            return

        # Conversion from wgs84 coord to map coord
        x, y = self.map.get_map_coord(*value)

        # Remember this position too
        self.last_pos = x, y

        # Update the reticule pos
        self.set_reticule_pos(x, y)

        # Update the orientation arrow pos if necessary
        if self.show_arrow:
            self.set_arrow_pos()

        # Update the path
        if self.tracking_path:
            self.update_path(x, y)

        # If we are locked on pos, we center the view on the last known position
        if self.locked_on_pos:
            self.center_on_last_pos()

    def update_path(self, x, y):
        self.path.points += x, y

    def toggle_tracking_path(self, obj):
        if self.tracking_path:
            self.tracking_path = False
            # Creation of a new path
            self.path = Line(width=self.path_width)
        else:
            self.tracking_path = True

    def format_path(self, *args):
        """This updates the width of the path to be consistent with the scale.
        """
        if self._path_zoom != self.zoom:
            self.path.width = self.path_width / self.scale
            self._path_zoom = self.zoom

    def center_on_last_pos(self, *args):
        scale = self.scale
        new_x = Window.size[0]/2 - self.last_pos[0]*scale
        new_y = Window.size[1]/2 - self.last_pos[1]*scale
        Animation.cancel_all(self)
        anim = Animation(x=new_x, y=new_y, t='in_out_quad', duration=0.5)
        anim.start(self)

    def get_dist_to_center(self):
        """
        :return: The distance in meters between the last known position and the position represented by the middle
        of the screen. If no distance can be calculated, it returns -1.
        """
        if self.map is None:
            return -1
        try:
            merc_x, merc_y = self.map.map_coord_to_map_projection(*self.to_local(Window.size[0]/2, Window.size[1]/2))
        except ZeroDivisionError:
            return -1
        lat, lon = Map.to_geographic(merc_x, merc_y)
        lat_last, lon_last = self.last_pos_wgs84
        dist = Map.distance(lat_last, lon_last, lat, lon)
        return dist

    def transform_with_touch(self, touch):
        if self.locked_on_pos:
            if len(self._touches) == 1:
                return False

            changed = False
            # We have more than one touch... list of last known pos
            points = [Vector(self._last_touch_pos[t]) for t in self._touches
                      if t is not touch]
            # Add current touch last
            points.append(Vector(touch.pos))

            # We only want to transform if the touch is part of the two touches
            # farthest apart! So first we find anchor, the point to transform
            # around as another touch farthest away from current touch's pos
            anchor_ = max(points[:-1], key=lambda p: p.distance(touch.pos))

            # Now we find the touch farthest away from anchor, if its not the
            # same as touch. Touch is not one of the two touches used to transform
            farthest = max(points, key=anchor_.distance)
            if farthest is not points[-1]:
                return changed

            # Ok, so we have touch, and anchor, so we can actually compute the
            # transformation
            old_line = Vector(*touch.ppos) - anchor_
            new_line = Vector(*touch.pos) - anchor_
            if not old_line.length():   # div by zero
                return changed

            # pol : we don't want rotation here
            # angle = radians(new_line.angle(old_line)) * self.do_rotation
            # self.apply_transform(Matrix().rotate(angle, 0, 0, 1), anchor=anchor)

            # pol : trick -> change the origin!!
            anchor = Vector(self.to_parent(*self.last_pos))
            if self.do_scale:
                scale = new_line.length() / old_line.length()
                new_scale = scale * self.scale
                if new_scale < self.scale_min:
                    scale = self.scale_min / self.scale
                elif new_scale > self.scale_max:
                    scale = self.scale_max / self.scale
                self.apply_transform(Matrix().scale(scale, scale, scale),
                                     anchor=anchor)
                changed = True
            return changed

        super(MapViewer, self).transform_with_touch(touch)


class MapBoard(Widget):
    def __init__(self, default_reticule, **kwargs):
        super(MapBoard, self).__init__(**kwargs)

        # Create the map viewer
        self.mapviewer = MapViewer(**kwargs)
        self.add_widget(self.mapviewer)

        # Load the reticule
        self.load_reticule(default_reticule)

        # Create compass button
        self.compass_button = CompassButton()
        self.add_widget(self.compass_button)

        # Add a reticule for calibration
        self.reticule_calib = Builder.load_file('ui/ScatterReticule.kv')

        # Create center_on_pos button
        self.load_center_on_pos()

        # Create path button
        path_button = PathButton()
        path_button.bind(on_press=self.mapviewer.toggle_tracking_path)
        self.add_widget(path_button)

        # Create the distance to center button
        self.dist_to_center_widget = None
        self.dist_to_center_visible =False
        self._dist_to_center_update_trigger = Clock.create_trigger(
            lambda x: self.dist_to_center_widget.set_distance(self.mapviewer.get_dist_to_center()), timeout=0.1)
        self.load_dist_to_center_button()

    def on_pos_update(self, instance, value):
        # The position is given to the mapviewer
        self.mapviewer.update_pos(instance, value)

        # If necessary, we update the widget that shows the distance to the center
        if self.dist_to_center_visible:
            self._dist_to_center_update_trigger()

    def load_reticule(self, img_source):
        # If a reticule already exists, delete it
        if self.mapviewer.reticule is not None:
            self.remove_widget(self.mapviewer.reticule)

        reticule = Image(source=img_source)
        self.mapviewer.set_reticule(reticule)
        self.add_widget(reticule)

        # Set the position to the former position
        self.mapviewer.set_reticule_pos(*self.mapviewer.last_pos)

    def load_center_on_pos(self):
        center_on_pos_button = CenterPosButton()
        center_on_pos_button.bind(on_lock=self.lock_view)
        center_on_pos_button.bind(on_unlock=self.unlock_view)
        center_on_pos_button.bind(on_center_on_last_pos=self.mapviewer.center_on_last_pos)
        self.add_widget(center_on_pos_button)

    def load_distance_to_center(self):
        dist_to_center_widget = DistToCenterWidget()
        self.add_widget(dist_to_center_widget)

    def lock_view(self, *args):
        self.mapviewer.do_translation = (False, False)
        self.mapviewer.locked_on_pos = True

    def unlock_view(self, *args):
        self.mapviewer.do_translation = (True, True)
        self.mapviewer.locked_on_pos = False

    def show_orientation_arrow(self):
        # Create an arrow if it doesn't exist
        if type(self.mapviewer.arrow) != 'Widget':
            self.mapviewer.set_orientation_arrow(OrientationArrow())
        if self.mapviewer.arrow not in self.children:
            self.add_widget(self.mapviewer.arrow)

        # Set the position to the former position
        self.mapviewer.set_arrow_pos()

    def hide_orientation_arrow(self):
        if self.mapviewer.arrow is not None:
            self.mapviewer.show_arrow = False
            self.remove_widget(self.mapviewer.arrow)

    def load_dist_to_center_button(self):
        dist_center = DistToCenterButton()
        dist_center.bind(on_press=self.toggle_distance_to_center)
        self.add_widget(dist_center)

    def toggle_distance_to_center(self, *args):
        if self.dist_to_center_visible:
            self.remove_widget(self.dist_to_center_widget)
            self.dist_to_center_visible = False
            self.mapviewer.unbind(pos=self._dist_to_center_update_trigger)
        else:
            if self.dist_to_center_widget is None:
                self.dist_to_center_widget = DistToCenterWidget()
            self.add_widget(self.dist_to_center_widget)
            self.dist_to_center_visible = True
            self.mapviewer.bind(pos=self._dist_to_center_update_trigger)
            self._dist_to_center_update_trigger()  # Force first update

    def getCalibrationCoord(self, *p):
        logger.debug("pos du clic (relatif) (%s, %s)" % self.mapviewer.to_local(*p))
        logger.debug(
            "pos du centre du reticule (relatif): (%s, %s)" % self.mapviewer.to_local(*self.reticule_calib.center))
