"""
This is an alternate implementation of MapChoice, using kivy-garden recycleview.
As of writing this module, recycleview was still in alpha stage and i didn't get the same level of functionality of
MapChoice.py

Nevertheless, the module is left as is and will hopefully replace MapChoice when recycleview is fully functional.
"""

# -*- coding: utf-8 -*-
__author__ = 'peter'

import contribs.recycleview
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

KV = """
<MapItem@GridLayout>:
    index: 0
    description: ""
    name: ""
    max_zoom: 0
    spacing: "0dp"
    cols: 1
    size_hint_y: None
    height: 1000

    # canvas.before:
    #     Color:
    #         rgb: (0.2, 0.2, 0.2, 0.1) if root.index % 2 == 0 else (1, 1, 1, 1)
    #     Rectangle:
    #         pos: self.pos
    #         size: self.size

    ToggleButton:
        id: btn
        bold: True
        text: root.name
        markup: True
        size_hint_y: None
        text_size: self.width, None
        height: self.texture_size[1] + dp(16)
        #selected: ctx.is_selected
        selected_color:  [0.,0.5,0.,1.]
        #background_color: [1.,1.,1.,0.2] if ctx.index % 2 == 0 else [1.,1.,1.,0.5]
        # background_color: ctx.init_background_color(ctx.index)
        #deselected_color:  [1.,1.,1.,0.2] if ctx.index % 2 == 0 else [1.,1.,1.,0.5]
        #on_release: ctx.callback(self.is_selected)
        on_press: root.callback(root.index, self.state)

    BoxLayout:
        id: carac1
        Label:
            halign: 'right'
            font_size: "11sp"
            text_size: self.width *0.4, None
            text: "Max zoom"
        Label:
            font_size: '11sp'
            text_size: self.width, None
            text: str(root.max_zoom)
    BoxLayout:
        id: carac2
        Label:
            halign: 'right'
            font_size: '11sp'
            text_size: self.width *0.4, None
            text: "Description"
        Label:
            id: descr
            valign: 'bottom'
            font_size: '11sp'
            size_hint_y: None
            text_size: self.width, None
            height: self.texture_size[1]
            text: root.description

BoxLayout:
    orientation: "vertical"

    RecycleView:
        id: rv
"""

class MapChoice2(BoxLayout):
    def __init__(self, **kwargs):
        super(MapChoice2, self).__init__(**kwargs)

        self.root = Builder.load_string(KV)
        rv = self.root.ids.rv
        rv.key_viewclass = "viewclass"
        rv.key_size = "height"
        self.map_items = kwargs.get('map_items', [])
        self.load_data(self.map_items)
        self.add_widget(self.root)

    def load_data(self, map_items):
        for map_item in map_items:
            map_item["callback"] = self.callback
        self.root.ids.rv.data = map_items
        # self.root.ids.rv.do_layout()

    def callback(self, index, state):
        if state == 'down':
            self.map_items[index]['action']()
        print index, state

if __name__ == '__main__':
    from kivy.base import runTouchApp

    def action():
        print "action"

    dummy_txt = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore \
    et dolore magna aliqua"
    mapChoice = MapChoice2(map_items=[
        {"action": action, "height": 130, "index": 0, "viewclass": "MapItem", 'name': 'nm1', 'description': dummy_txt},
        {"action": action, "height": 130, "index": 1, "viewclass": "MapItem", 'name': 'nm2', 'description': dummy_txt}])

    runTouchApp(mapChoice)
