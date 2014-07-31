
# Standard library imports
import logging
import os
import subprocess
import threading
import time
from xml.etree import ElementTree

# Third party imports
import zmq

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes import \
        ApplicationWithConfig
from yarely.frontend.core.helpers.base_classes.zmq_rpc import ZMQRPC
from yarely.frontend.core.helpers.execution import application_loop
from yarely.frontend.core.helpers.zmq import ZMQ_ADDRESS_INPROC, \
        ZMQ_DISPLAYCONTROLLER_REP_PORT, ZMQ_ADDRESS_LOCALHOST, \
        ZMQ_SOCKET_LINGER_MSEC

log = logging.getLogger(__name__)

SUBPROCESS_CHECKIN_INTERVAL = 1        # Seconds
_TERMINATION_MARKER = object()
QUEUE_TIMEOUT = 1                      # Seconds
WARN_NO_REPLY = 'Expected reply from Scheduler not received.'
DEFAULT_DISPLAY_TIMEOUT = 300          # Seconds

DISPLAY_DEVICE_PATH = os.path.join(
    os.path.abspath(__file__)[:-len('display_controller_projector.py')],
    'sanyo_display_device.py'
)

#FIXEME
ZMQ_SCHEDULER_ADDR = ZMQ_ADDRESS_LOCALHOST.format(
            port=ZMQ_DISPLAYCONTROLLER_REP_PORT
        )


class DisplayControllerError(Exception):
    """Base class for display manager errors"""
    pass


class DisplayController(threading.Thread, ZMQRPC):
    def __init__(self, etree=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.connection_requests = dict()
        self.schedule_req_list = list()

    def set_display_serial(self, serial, timeout):
        self.display_serial = serial
        self.display_timeout = timeout
        # controls display state
        self.turn_on()
        self.keep_display_on_until = time.time() + int(self.display_timeout)
        self.recvd_change = threading.Event()

    def run(self):
        while True:
            now = time.time()
            diff = self.keep_display_on_until - now
            display_should_be_on = diff > 0

            if display_should_be_on:
                if not self.display_is_on:
                    self.turn_on()
                self.recvd_change.wait(diff)
            else:
                if self.display_is_on:
                    self.turn_off()
                self.recvd_change.wait()

            self.recvd_change.clear()

    def turn_on(self):
        log.info('Turning display on')
        args = ['python', DISPLAY_DEVICE_PATH, 'ON', self.display_serial]
        subprocess.call(args)
        self.display_is_on = True

    def turn_off(self):
        log.info('Turning display off')
        args = ['python', DISPLAY_DEVICE_PATH, 'OFF', self.display_serial]
        subprocess.call(args)
        self.display_is_on = False


class DisplayControllerReceiver(ApplicationWithConfig, ZMQRPC):
    """
        Creates a socket to receive content_descriptor set
        from subscription manager
    """
    def __init__(self):
        super().__init__('DisplayControllerReceiver')
        self.connection_requests = dict()
        self.zmq_display_term_identifier = "display_term_{id}".format(
            id=id(self)
        )

    def _handle_arguments(self, args):
        """Handle arguments received from the argument parser."""
        super()._handle_arguments(args)

        # The device display serial
        self.display_device_serial = self.config.get('DisplayDevice',
                                                 'DisplayDeviceSerialUSBName')

        # The device display timeout
        self.display_device_timeout = max(int(self.config.get('DisplayDevice',
                                                 'DisplayTimeout')),
                                    DEFAULT_DISPLAY_TIMEOUT)

    def _handle_incoming_zmq(self):
        """Executes in separate thread: _zmq_req_to_scheduler_thread."""
        self.zmq_context_req = zmq.Context()

        # Initialise ZMQ reply socket to scheduler
        zmq_scheduler_reply_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_scheduler_reply_socket.setsockopt(zmq.LINGER,
                                                ZMQ_SOCKET_LINGER_MSEC)
        zmq_scheduler_reply_socket.bind(ZMQ_SCHEDULER_ADDR)

        # Initialise ZMQ reply socket to watch for termination
        zmq_termination_reply_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_termination_reply_socket.bind(
            ZMQ_ADDRESS_INPROC.format(
                identifier=self.zmq_display_term_identifier
            )
        )

        # Initialise ZMQ poller to watch REP sockets
        zmq_poller = zmq.Poller()
        zmq_poller.register(zmq_scheduler_reply_socket, zmq.POLLIN)
        zmq_poller.register(zmq_termination_reply_socket, zmq.POLLIN)

        # Provide a method to loop over sockets that have data
        def _loop_over_sockets():
            term = False
            for sock in socks_with_data:
                if sock is zmq_termination_reply_socket:
                    term = True

                # B. FIXME THIS SHOULD USE THE _handle_zmq_msg METHOD
                elif sock is zmq_scheduler_reply_socket:
                    req_str = sock.recv_unicode()
                    log.debug(
                        'Received data via ZMQ: {msg}'.format(msg=req_str)
                    )
                    sock.send_unicode(
                        ElementTree.tostring(
                            self._encapsulate_reply(self._generate_pong()),
                            encoding="unicode"
                        )
                    )
                    # Extract duration from XML
                    elem = ElementTree.XML(req_str)
                    timestamp = float(elem.find('display-on').attrib['until'])
                    if req_str is not None:
                        self.DisplayController.keep_display_on_until = \
                            timestamp
                        self.DisplayController.recvd_change.set()
                else:
                    msg = sock.recv().decode()
                    log.debug(
                        'Received data via ZMQ: {msg}'.format(msg=msg)
                    )
                    reply = self._handle_zmq_msg(msg)
                    if reply is None:
                        log.warning(WARN_NO_REPLY)
                        reply = self._encapsulate_reply(self._generate_error())
                    sock.send(ElementTree.tostring(reply))
            return term

        while True:
            socks_with_data = dict(zmq_poller.poll())
            if socks_with_data:
                term = _loop_over_sockets()
                if term:
                    break

        # Cleanup ZMQ
        zmq_poller.unregister(zmq_scheduler_reply_socket)
        zmq_poller.unregister(zmq_termination_reply_socket)
        zmq_scheduler_reply_socket.close()
        zmq_termination_reply_socket.close()

    def display_control(self):
        self.DisplayController = DisplayController()
        log.info('Starting display contoller')
        self.DisplayController.set_display_serial(
            self.display_device_serial, self.display_device_timeout)
        self.DisplayController.start()

    def start(self):
        """The main execution method for this application."""
        self.zmq_scheduler_req_addr = ZMQ_SCHEDULER_ADDR

        self._zmq_scheduler_reply_thread = threading.Thread(
            target=self._handle_incoming_zmq
        )
        t_name = 'ZMQ reply socket monitor'
        self._zmq_scheduler_reply_thread.name = t_name
        self._zmq_scheduler_reply_thread.daemon = True
        self._zmq_scheduler_reply_thread.start()
        # Start display controller with display device taken from config
        self.display_control()

    def stop(self):
        """Application termination cleanup.

        """
        # Terminate ZMQ-related threads
        zmq_termination_request_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_termination_request_socket.setsockopt(
            zmq.LINGER, ZMQ_SOCKET_LINGER_MSEC
        )
        zmq_termination_request_socket.connect(
            ZMQ_ADDRESS_INPROC.format(
                identifier=self.zmq_display_term_identifier
            )
        )
        zmq_termination_request_socket.send_unicode('TERMINATE')
        zmq_termination_request_socket.close()
        self._zmq_scheduler_reply_thread.join()

        super().stop()
        self.zmq_context_req.term()

if __name__ == "__main__":
    application_loop(DisplayControllerReceiver)
