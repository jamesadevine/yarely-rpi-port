#!/usr/bin/env python
# -*- coding: utf8 -*-

# __author__ = "Viktor Petersson"
# __copyright__ = "Copyright 2012, WireLoad Inc"
# __license__ = "Dual License: GPLv2 and Commercial License"
# __version__ = "0.1"
# __email__ = "vpetersson@wireload.net"

import logging
import os
from subprocess import check_output
import re
from threading import Thread
from yarely.frontend.linux.shutter.shutter import Shutter

# Initiate logging
log = logging.getLogger(__name__)


class Renderers():
    def __init__(self):
        self.resolution = re.search(
            '(\d{3,4}x\d{3,4}) @',
            str(check_output(['tvservice', '-s']).strip())
        ).group(1)

        self.shutter=Shutter()

        #cursor variable to keep track of on/off state
        self.cursor=True

        #switch cursor off
        self.toggle_cursor()

        #clear the terminal of any messages from the setup stage.
        self.clear_terminal()


    def clear_terminal(self):
        #clear terminal
        #print('CLEAR')
        #self.cursor
        os.system('cls' if os.name == 'nt' else 'clear')

    def toggle_cursor(self):
        #a method which toggles the system cursor.
        if not self.cursor:
            os.system('setterm -cursor on')
        else:
            os.system('setterm -cursor off')

    def stop(self):
        # TODO: stop the renderers here somehow
        pass

