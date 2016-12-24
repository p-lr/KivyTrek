# -*- coding: utf-8 -*-
__author__ = 'pla'

import logging

logger = logging.getLogger('kivytrek')

# we don't want messages given to KivyTrek's logger be passed to root logger's handlers.
logger.propagate = 0

# TODO : prendre ce paramètre d'un fichier de conf
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(levelname)s][kivytrek] %(message)s')

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
