#!/usr/bin/env python3.2
# This will be a handler..

import logging

from yarely.frontend.core.helpers.base_classes import Handler, HandlerError
from yarely.frontend.core.helpers.execution import application_loop

log = logging.getLogger(__name__)

HANDLER_DESCRIPTION = "Demonstrate things working"

class DemoHandler(Handler):
    def __init__(self):
        super().__init__(HANDLER_DESCRIPTION)

if __name__ == "__main__":
    application_loop(DemoHandler)
