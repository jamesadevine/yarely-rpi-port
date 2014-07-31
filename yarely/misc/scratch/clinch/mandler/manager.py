#!/usr/bin/env python3.2
## This will be a manager

import logging

from yarely.frontend.core.helpers.base_classes import ApplicationWithConfig
from yarely.frontend.core.helpers.execution import application_loop

log = logging.getLogger(__name__)

MANAGER_DESCRIPTION = "Demonstrate things working"

class DemoManager(ApplicationWithConfig):
    def __init__(self):
        super().__init__(MANAGER_DESCRIPTION)

    def start(self):
        log.info("Started")

if __name__ == '__main__':
    application_loop(DemoManager)
