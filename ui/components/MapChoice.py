"""
This module exposes widgets that are intended to display the list of maps.
That list is given as an argument for the MapChoice widget.

Each map can be selected, while some of its attributes are shown (like the description, and the maximum zoom).
"""

# -*- coding: utf-8 -*-
__author__ = 'peter'

from app.modules.log import logger
from kivy.adapters.listadapter import ListAdapter
from kivy.adapters.models import SelectableDataItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.listview import ListView, ListItemButton, CompositeListItem
from kivy.lang import Builder

kv = '''
[CustomListItem@SelectableView+GridLayout]:
    # size_hint_y: ctx.size_hint_y
    cols: 1
    size_hint_y: None
    height: dp(70) + descr.height + calib_btn.height
    ListItemButton:
        id: btn
        bold: True
        text: ' ' + ctx.name
        markup: True
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1] + dp(16)
        selected: ctx.is_selected
        selected_color:  [0.16, 0.38, 1., 1.]
        background_color: [0.376, 0.49, 0.545, 1]
        # background_color: ctx.init_background_color(ctx.index)
        deselected_color:  [0.376, 0.49, 0.545, 1]
        on_release: ctx.select_change_callback(self.is_selected)

    BoxLayout:
        id: carac2
        ListItemLabel:
            halign: 'right'
            font_size: '11sp'
            text_size: self.width *0.4, None
            markup: True
            text: u'[color=000000]{0}[/color]'.format("Description")
        ListItemLabel:
            id: descr
            font_size: '11sp'
            text_size: self.width, None
            markup: True
            text: u'[color=000000]{0}[/color]'.format(ctx.description)

    BoxLayout:
        id: carac1
        ListItemLabel:
            halign: 'right'
            font_size: '11sp'
            text_size: self.width *0.4, None
            markup: True
            text: u'[color=000000]{0}[/color]'.format("Max zoom")
        ListItemLabel:
            font_size: '11sp'
            text_size: self.width, None
            markup: True
            text: u'[color=000000]{0}[/color]'.format(str(ctx.max_zoom))

    ListItemButton:
        id: calib_btn
        text: 'Calibrate'
        on_release: ctx.calibration_callback()

'''


class MapItem(SelectableDataItem):
    background_color_even = [0.376, 0.49, 0.545, 1]
    selected_color = [0.16, 0.38, 1., 1.]

    def __init__(self, **kwargs):
        super(MapItem, self).__init__(**kwargs)
        self.name = kwargs.get('name', '')
        self.caracteristics = kwargs.get('caracteristics', [])
        self.is_selected = kwargs.get('is_selected', False)
        self.max_zoom = kwargs.get('max_zoom', 1)
        self.description = kwargs.get('description', "")
        self.action = kwargs.get('action', None)
        self.calibration_action = kwargs.get('calibration_action', None)

    def on_selection_change(self, selected):
        if selected and self.action:
            logger.debug("Loading the map : %s" % self.name)
            self.action()
        else:
            logger.debug("Unselecting the map %s. Does nothing for instance." % self.name)

    def on_calibration(self):
        logger.debug("Calibrating the map : %s" % self.name)
        self.calibration_action()


class MapChoice(BoxLayout):
    def __init__(self, **kwargs):
        super(MapChoice, self).__init__(**kwargs)

        self.root = Builder.load_string(kv)
        self.map_items = kwargs.get('map_items', [])

        list_item_args_converter = \
                lambda row_index, selectable: {'name': selectable.name,
                                               'max_zoom': selectable.max_zoom,
                                               'description': selectable.description,
                                               'size_hint_y': None,
                                               'is_selected': selectable.is_selected,
                                               'select_change_callback': selectable.on_selection_change,
                                               'calibration_callback': selectable.on_calibration,
                                               'index': row_index}

        map_list_adapter = \
            ListAdapter(data=self.map_items,
                        args_converter=list_item_args_converter,
                        selection_mode='single',
                        allow_empty_selection=False,
                        template='CustomListItem')

        list_view = ListView(adapter=map_list_adapter)

        # map_list_adapter.bind(on_selection_change=self.callback_function)

        self.add_widget(list_view)

    def callback_function(self, adapter):
        print "The selection changed", adapter.data


if __name__ == '__main__':
    from kivy.base import runTouchApp

    dummy_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore \
    et dolore magna aliqua"
    mapChoice = MapChoice(width=800, map_items=[
        MapItem(name='name1', description=dummy_text),
        MapItem(name='name2', description=dummy_text)])
    runTouchApp(mapChoice)
