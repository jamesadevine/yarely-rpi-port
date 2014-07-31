#!/usr/bin/env python3.2

# Standard library imports
import os.path

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes import ApplicationError,\
        URIManager
from yarely.frontend.core.helpers.execution import application_loop


CACHE_MODULE_ROOT = '/Users/sarah/Documents/\
yarely/frontend/core/content/caching'


class CacheManagerError(ApplicationError):
    """Base class for cache manager errors"""
    pass


class CacheManager(URIManager):
    """Manages caching"""

    def __init__(self):
        """Default constructor - Creates a new CacheManager."""
        description = "Manage Yarely content caching"

        # The parent constructor provides config and logging and gets a
        # starting set of handlers using this classes _init_handlers() method.
        super().__init__(description)

    def _handle_arguments(self, args):
        """Handle arguments received from the argument parser."""
        super()._handle_arguments(args)

        # The file_store_path is a path to a local directory in which
        # cached files can be stored.
        self.file_store_path = self.config.get('CacheFileStorage',
                                                 'CacheLocation')
        try:
            os.mkdir(self.file_store_path)
        except OSError as e:
            if not os.path.isdir(self.file_store_path):
                raise CacheManagerError from e

    def _handle_request_cachefile(self, msg_root, msg_elem):
        sources = msg_elem.find('sources')
        hashes = msg_elem.find('hashes')
        for hash in hashes:
            file_path = self.lookup_hash(hash)
            if file_path is not None:
                break
        if file_path is None:
            # FIXME
            # We'll assume for now that the handler is always going to be
            # successful
            uri = sources.find('uri').text
            handler = self.get_uri_handler_stub(uri)
            self.start_handler(handler)

    def _init_handlers(self):
        # The _registered_handlers dictionary is keyed by addressing scheme,
        # current keys are:
        #     'http'  => A remote file to be fetched over http
        http_handler = 'python3.2 {path}'.format(path=os.path.join(
            CACHE_MODULE_ROOT, 'handlers/http.py'
        ))
        self.add_handler('http', http_handler)

    def start(self):
        super().start()

    def lookup_hash(self, hash):
        return None

if __name__ == "__main__":
    application_loop(CacheManager)
