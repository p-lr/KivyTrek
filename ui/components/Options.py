__author__ = 'pol'

from kivy.uix.dropdown import DropDown
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image

'''
Classes used in the option screen of the app.
They are implemented in options.kv
'''


class ReticuleDropDown(DropDown):
    pass


class ImageButton(ButtonBehavior, Image):
    pass


class DropDownButton(ImageButton):
    def __init__(self, **kwargs):
        super(DropDownButton, self).__init__(**kwargs)
        self.dropdown = ReticuleDropDown()
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'source', x))
