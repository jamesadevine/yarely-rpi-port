#!/usr/bin/env python3.2

# Standard library imports
import logging
import urllib.request
from urllib.error import URLError

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes import PullHandler, HandlerError
from yarely.frontend.core.helpers.execution import application_loop

log = logging.getLogger(__name__)

HANDLER_DESCRIPTION = "Handler for HTTP-sourced subscriptions"


class HTTPHandlerError(HandlerError):
    """Base class for HTTP handler errors."""
    pass


class HTTPHandler(PullHandler):
    """The HTTPHandler class provides a handler for HTTP-sourced
    subscriptions.

    """

    def __init__(self):
        super().__init__(HANDLER_DESCRIPTION)

    def _handle_reply_params(self, msg_root, msg_elem):
        super()._handle_reply_params(msg_root, msg_elem)
        self.uri = self.params['uri']

    def read(self):
        # Pull the XML from the URI
        try:
            with urllib.request.urlopen(self.uri) as http_handle:
                xml = http_handle.read().strip()
        except URLError as e:
            self._fail('Error reading HTTP source')
            return

        # Send XML to the manager
        try:
            # FIXME - Ultimately we don't want to send the URI back
            # The manager should know which URI we're handling?
            # (Although this would change again when handlers do >1 URI)
            etree = self._encapsulate_request(
                self._generate_subscription_update(self.uri, xml)
            )
            self.zmq_request_queue.put_nowait(etree)
        except Exception as e:
            self._fail('Error writing update event: {e}'.format(e=e))
            return

        self._success()

    def start(self):
        super().start()
        log.info('HTTP Handler Launched')


if __name__ == "__main__":
    application_loop(HTTPHandler)
