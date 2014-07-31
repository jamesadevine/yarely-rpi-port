# Standard library imports
import copy
import urllib.parse

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes import Manager


class URIManager(Manager):
    """A base class for managers which launch handlers in response to URIs."""

    def __init__(self, zmq_req_port, description):
        super().__init__(zmq_req_port, description)

    def _lookup_executing_handler_with_uri(self, uri):
        with self._lock:
            for handler in self._executing_handlers.values():
                if handler.handler_params['uri'] == uri:
                    return handler
        return None

    def get_uri_handler_stub(self, uri):
        """Get the handler associated with the addressing scheme for
        the specified URI.

        """
        splitresult = urllib.parse.urlsplit(uri)
        handler = copy.deepcopy(self.get_handler_stub(splitresult.scheme))
        handler.params_over_zmq = {'uri': uri}
        return handler
