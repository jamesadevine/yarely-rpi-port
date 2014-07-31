"""Yarely execution control module with Cocoa specialisms"""

import logging
import os
import signal

log = logging.getLogger(__name__)

def application_loop(concrete, *args, **kwargs):
    """Main entry point - creates a new Application instance (whose specific
    implementation is provided by concrete) and starts execution. Listens
    for SIGINT and SIGTERM signals, posting a Cocoa termination notification
    when they are received.

    For use by modules containing classes that extend
    yarely.frontend.core.helpers.base_classes.Application that need to use
    the Cocoa event loop system.

    """
    application = concrete(*args, **kwargs)   # Instantiate the concrete class

    def _sigterm(signum, frame):
        """SIGTERM handler, attempt a clean termination."""
        _terminate('SIGTERM')

    def _sigint(signum, frame):
        """SIGINT handler, attempt a clean termination."""
        _terminate('SIGINT')

    def _terminate(cause):
        """Attempt a clean termination logging the cause."""
        log.info('Termination from {cause}'.format(cause=cause))
        application.stop()
        
    signal.signal(signal.SIGTERM, _sigterm)
    signal.signal(signal.SIGINT, _sigint)

    application.process_arguments()
    application.start()
    #AppHelper.runEventLoop()