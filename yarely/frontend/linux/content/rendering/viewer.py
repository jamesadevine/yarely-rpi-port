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

# Initiate logging
log = logging.getLogger(__name__)


class Renderers():
    def __init__(self):
        self.resolution = re.search(
            '(\d{3,4}x\d{3,4}) @',
            str(check_output(['tvservice', '-s']).strip())
        ).group(1)
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def stop(self):
        # TODO: stop the renderers here somehow
        pass

