#!/usr/bin/env python
# -*- coding: utf8 -*-

# __author__ = "Viktor Petersson"
# __copyright__ = "Copyright 2012, WireLoad Inc"
# __license__ = "Dual License: GPLv2 and Commercial License"
# __version__ = "0.1"
# __email__ = "vpetersson@wireload.net"

import logging
from os import path, getenv, remove, makedirs
from os import stat as os_stat, utime
from subprocess import check_output
from yarely.frontend.linux.shutter.shutter import Shutter
from yarely.frontend.linux.content.rendering.handlers.browser import Browser
import re
from threading import Thread

# Initiate logging
log = logging.getLogger(__name__)

def watchdog():
    """
    Notify the watchdog file to be used with the watchdog-device.
    """

    watchdog = '/tmp/screenly.watchdog'
    if not path.isfile(watchdog):
        open(watchdog, 'w').close()
    else:
        utime(watchdog,None)

class Renderers():
    def __init__(self):
        self.resolution = re.search(
            '(\d{3,4}x\d{3,4}) @',
            str(check_output(['tvservice', '-s']).strip())
        ).group(1)
        self.shutter = Shutter()
    
    def stop(self):
        # TODO: stop the renderers here somehow
        pass

