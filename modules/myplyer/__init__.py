__author__ = 'pla'

__all__ = ('rotation', 'gps',)

from modules.myplyer import facades
from modules.myplyer.utils import Proxy

#: Rotation proxy to :class:`plyer.facades.Rotation`
rotation = Proxy('rotation', facades.Rotation)

#: GPS proxy to :class:`plyer.facades.GPS`
gps = Proxy('gps', facades.GPS)
