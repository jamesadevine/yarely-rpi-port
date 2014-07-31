""" Yarely execution control module. """

import logging
import signal
import sys
import time

log = logging.getLogger(__name__)

SLEEP_INTERVAL = 30


def application_loop(concrete, *args, **kwargs):
    """Main entry point - creates a new Application instance (whose specific
    implementation is provided by concrete) and starts execution. Listens
    for KeyboardInterrupts to allow termination.

    For use by modules containing classes that extend
    yarely.frontend.core.helpers.base_classes.Application.

    """
    application = concrete(*args, **kwargs)   # Instantiate the concrete class

    def sigterm(*args, **kwargs):
        """SIGTERM handler, attempt a clean termination."""
        terminate('SIGTERM')

    def terminate(cause):
        """Attempt a clean termination logging the cause."""
        log.info('Termination from {cause}'.format(cause=cause))
        application.stop()
        sys.exit()

    signal.signal(signal.SIGTERM, sigterm)
    application.process_arguments()
    application.start()
    try:
        while True:
            time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        terminate('KeyboardInterrupt')
