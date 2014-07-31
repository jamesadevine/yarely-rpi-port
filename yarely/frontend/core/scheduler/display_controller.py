# Standard library imports
import configparser
import logging
import os
import subprocess
import termios
import threading
import time
from xml.etree import ElementTree

# Third party imports
#from IxionAnalytics import IxionAnalytics
import zmq

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes import ApplicationWithConfig
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
DISPLAY_STATE_POLLING_FREQ = 5  # Seconds

DISPLAY_DEVICE_DIRECTORY = os.path.abspath(__file__)[:-len('display_controller.py')]
DISPLAY_DEVICE_DRIVER_SUFFIX = '_display_device.py'
DISPLAY_IS_ON = "IS_ON"

LINESPEED_DISPLAY = termios.B9600
#FIXEME
ZMQ_SCHEDULER_ADDR = ZMQ_ADDRESS_LOCALHOST.format(
    port=ZMQ_DISPLAYCONTROLLER_REP_PORT
)


class DisplayControllerError(Exception):
    """Base class for display manager errors"""
    pass


class DisplayController(threading.Thread, ZMQRPC):
    def __init__(self, serial, tracking_id, display_type='sony', etree=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.connection_requests = dict()
        self.schedule_req_list = list()

        #self.analytics = IxionAnalytics(tracking_id)
        self.display_type = display_type

        self.display_is_on = None
        self.recvd_change = threading.Event()
        self.display_serial = serial
        self.update_display_is_on()
        self.keep_display_on_until = time.time() + 5

    def run(self):
        while True:
            now = time.time()
            diff = self.keep_display_on_until - now
            display_should_be_on = diff > 0
            # Update display_is_on to real power state of display
            self.update_display_is_on()

            if display_should_be_on:
                if not self.display_is_on:
                    self.turn_on()
                self.recvd_change.wait(min(diff, DISPLAY_STATE_POLLING_FREQ))
            else:
                if self.display_is_on:
                    self.turn_off()
                # Wait for N seconds and keep on checking the display state
                self.recvd_change.wait(DISPLAY_STATE_POLLING_FREQ)

            self.recvd_change.clear()

    def display_device(self):
        display_device_path = os.path.join(
            DISPLAY_DEVICE_DIRECTORY,
            self.display_type + DISPLAY_DEVICE_DRIVER_SUFFIX
        )
        return ['python3', display_device_path]

    def turn_display(self, new_state='ON'):
        log.info('Turning display {new_state}'.format(new_state=new_state))
        args = self.display_device()
        args += [new_state, self.display_serial]
        log.debug('Display device args are: {}'.format(args))
        subprocess.call(args)
        self.update_display_is_on()

    def turn_on(self):
        #self.analytics.track_event('yarely', 'display_command', 'turn_on')
        self.turn_display('ON')

    def turn_off(self):
        #self.analytics.track_event('yarely', 'display_command', 'turn_off')
        self.turn_display('OFF')

    def update_display_is_on(self):
        log.debug('Requesting display power status')
        args = self.display_device() 
        args += ['GET_POWER_STATUS', self.display_serial]
        log.debug('Display device args are: {}'.format(args))
        process_output = subprocess.check_output(args).decode("utf-8")
        log.debug('Display power status output: {output}'.format(
            output=process_output
        ))

        # Check to see if the current display state is different to previous
        # state 
        new_display_state = DISPLAY_IS_ON in process_output
        old_display_state = self.display_is_on
        if new_display_state != old_display_state:
            self.display_is_on = new_display_state
            log.debug('Changed display_is_on to {displayison}'.format(
                displayison=self.display_is_on))
            self.analytics.track_event(
                'yarely', 'changed_display_status', process_output
            )


class DisplayControllerReceiver(ApplicationWithConfig, ZMQRPC):
    """
        Creates a socket to receive commands from the scheduler.
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
        self.display_device_serial = self.config.get(
            'DisplayDevice', 'DisplayDeviceSerialUSBName'
        )

        # Read Analytics Tracking ID
        self.analytics_tracking_id = self.config.get(
            'Analytics', 'tracking_id'
        )

    def _handle_incoming_zmq(self):
        """Executes in separate thread: _zmq_req_to_scheduler_thread."""
        self.zmq_context_req = zmq.Context()

        # Initialise ZMQ reply socket to scheduler
        zmq_scheduler_reply_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_scheduler_reply_socket.setsockopt(
            zmq.LINGER, ZMQ_SOCKET_LINGER_MSEC
        )
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
                    # Extract time to keep display on until
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
        device_type = None
        try:
            device_type = self.config.get(
                'DisplayDevice', 'DeviceType'
            )
            self.display_type = device_type
        except (configparser.NoSectionError, configparser.NoOptionError):
            pass

        self.DisplayController = DisplayController(
            self.display_device_serial, self.analytics_tracking_id,
            'sony' if device_type is None else self.display_type
        )
        log.info('Starting display contoller')
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
