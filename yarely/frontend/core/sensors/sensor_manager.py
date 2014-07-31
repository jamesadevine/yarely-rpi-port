#!/usr/bin/env python3.2

# Standard library imports
import copy
import logging
import queue
import threading
import time
from xml.etree import ElementTree

# Third party imports
import zmq

# Local (Yarely) imports
from yarely.frontend.core.helpers.base_classes import ApplicationError, \
        HandlerStub
from yarely.frontend.core.helpers.base_classes.manager import \
        check_handler_token, Manager
from yarely.frontend.core.helpers.execution import application_loop
from yarely.frontend.core.helpers.zmq import ZMQ_ADDRESS_INPROC, \
        ZMQ_ADDRESS_LOCALHOST, ZMQ_SOCKET_LINGER_MSEC, \
        ZMQ_SOCKET_NO_LINGER, ZMQ_REQUEST_TIMEOUT_MSEC, \
        ZMQ_SENSORMANAGER_REP_PORT, ZMQ_SENSORMANAGER_REQ_PORT

log = logging.getLogger(__name__)

_TERMINATION_MARKER = object()
QUEUE_TIMEOUT = 1        # Seconds
SUBPROCESS_CHECKIN_INTERVAL = 1        # Seconds
WARN_NO_REPLY = 'Expected reply from Scheduler not received, will retry.'

SOCKET_PORT = 9786


class SensorMangerError(ApplicationError):
    """Base class for sensor manager errors"""
    pass


class SensorManager(Manager):
    """Manages subscriptions"""

    def __init__(self):
        """Default constructor - Creates a new SensorManager."""
        description = "Manage Yarely sensors"

        # The parent constructor provides config and logging and gets a
        # starting set of handlers using this classes _init_handlers() method.
        super().__init__(ZMQ_SENSORMANAGER_REP_PORT, description)
        self.registered = False

        # Setup for ZMQ Scheduler Messaging
        sensor_term_id = "sensormanager_term_{id}"
        self.zmq_sensormanager_term_identifier = sensor_term_id.format(
                                                     id=id(self)
                                                 )
        self.zmq_scheduler_req_addr = ZMQ_ADDRESS_LOCALHOST.format(
            port=ZMQ_SENSORMANAGER_REQ_PORT
        )
        self.zmq_scheduler_request_queue = queue.Queue()   # Q of infinite size

    def _init_handlers(self):
        # The _registered_handlers dictionary is keyed by 'type',
        # current keys are:
        #     'socket' => Handles a socket (virtual) sensor.
        python_launch_str = 'python3.2 -m {module}'
        socket_handler = HandlerStub(
            command_line_args=python_launch_str.format(
                module='yarely.frontend.core.sensors.handlers.socket'
            )
        )
        socket_handler.params_over_zmq = dict([('port', str(SOCKET_PORT))])
        self.add_handler('socket', socket_handler)

    def _handle_zmq_req_to_scheduler(self):
        """Executes in separate thread: _zmq_req_to_scheduler_thread."""

        # Provide some constants used as the return codes of nested
        # function _loop_over_sockets()
        NO_DATA = 0
        TERM = -1

        # Initialise ZMQ request socket
        zmq_request_socket = self.zmq_context.socket(zmq.REQ)
        zmq_request_socket.setsockopt(zmq.LINGER, ZMQ_SOCKET_LINGER_MSEC)
        zmq_request_socket.connect(self.zmq_scheduler_req_addr)

        # Initialise ZMQ socket to watch for termination before recvs
        # (we use the request queue to watch for termination before sends).
        zmq_termination_reply_socket = self.zmq_context.socket(zmq.REP)
        zmq_termination_reply_socket.bind(
            ZMQ_ADDRESS_INPROC.format(
                identifier=self.zmq_sensormanager_term_identifier
            )
        )

        # Initialise ZMQ Poller for recvs
        zmq_request_poller = zmq.Poller()
        zmq_request_poller.register(zmq_request_socket, zmq.POLLIN)
        zmq_request_poller.register(zmq_termination_reply_socket, zmq.POLLIN)

        # Provide a method to loop over sockets that have data
        def _loop_over_sockets():
            rtn = NO_DATA
            for sock in socks_with_data:
                if sock is zmq_termination_reply_socket:
                    return TERM
                elif sock is zmq_request_socket:
                    reply = sock.recv().decode()
                    if not reply:
                        continue
                    log.debug(
                        'Received reply from Scheduler: {msg}'.format(
                            msg=reply
                        )
                    )
                    self._handle_zmq_msg(reply)
                    rtn = len(reply)
                else:
                    log.info(
                        'Unhandled socket data: {sock}'.format(sock=sock)
                    )
            return rtn

        # Time the last request was sent (unix timestamp)
        last_request = 0

        while True:
            # Send a message from the message queue
            try:
                qitem = self.zmq_scheduler_request_queue.get(
                    timeout=QUEUE_TIMEOUT
                )

                # First check for termnation
                if qitem is _TERMINATION_MARKER:
                    break

                # We've not been asked to terminate, so send
                # the message over ZMQ.

                # Queue items are ElementTree Elements, so we encode them to a
                # byte representation.
                encoded_qitem = ElementTree.tostring(qitem, encoding="UTF-8")

                last_request = time.time()
                log.debug('Sending request to Scheduler: {msg}'.format(
                    msg=encoded_qitem)
                )
                zmq_request_socket.send(encoded_qitem)

                # Every send should have an associated receive.
                expect_reply = True
                result = None
                while expect_reply:
                    socks_with_data = dict(
                        zmq_request_poller.poll(ZMQ_REQUEST_TIMEOUT_MSEC)
                    )
                    if socks_with_data:
                        result = _loop_over_sockets()
                        if result is TERM:          # Terminate
                            break
                        elif result is NO_DATA:     # Rebuild socket
                            log.warning(WARN_NO_REPLY)
                            zmq_request_socket.setsockopt(zmq.LINGER,
                                                          ZMQ_SOCKET_NO_LINGER)
                            zmq_request_socket.close()
                            zmq_request_poller.unregister(zmq_request_socket)
                            zmq_request_socket = self.zmq_context.socket(
                                                 zmq.REQ)
                            zmq_request_socket.setsockopt(
                                zmq.LINGER, ZMQ_SOCKET_LINGER_MSEC
                            )
                            zmq_request_socket.connect(self.zmq_req_addr)
                            zmq_request_poller.register(zmq_request_socket,
                                                        zmq.POLLIN)
                            zmq_request_socket.send(encoded_qitem)
                        else:
                            assert(result > 0)
                            expect_reply = False    # Success!
                if result is TERM:
                    break

            except queue.Empty:
                pass

            # We do this last so we don't check in if we've just sent data
            # If we're not registered yet, we can't checkin
            next_checkin = last_request + SUBPROCESS_CHECKIN_INTERVAL
            if self.registered and next_checkin <= time.time():
                self.check_in()

        zmq_request_socket.close()

    def _handle_reply_pong(self, msg_root, msg_elem):
        self.registered = True

    @check_handler_token
    def _handle_request_sensor_update(self, msg_root, msg_elem):

        token = msg_root.attrib['token']
        with self._lock:
            handler = self._lookup_executing_handler_with_token(token)
            handler.last_checkin = time.time()

            # Forward the message
            self.zmq_scheduler_request_queue.put_nowait(
                self._encapsulate_request(msg_elem)
            )
        return self._encapsulate_reply(self._generate_pong())

    def check_in(self):
        """Provide an occasional check-in to the Scheduler via ZMQ."""
        etree = self._encapsulate_request(self._generate_ping())
        self.zmq_scheduler_request_queue.put_nowait(etree)

    def start(self):
        """The main execution method for this application"""
        super().start()

        # Start the socket handler
        handler = copy.deepcopy(self.get_handler_stub('socket'))
        self.start_handler(handler)

        # Start a new thread to create a ZMQ socket and send messages to
        # the scheduler
        self._zmq_req_to_scheduler_thread = threading.Thread(
            target=self._handle_zmq_req_to_scheduler
        )
        t_name = 'ZMQ Request Messenger (-> Scheduler)'
        self._zmq_req_to_scheduler_thread.name = t_name
        self._zmq_req_to_scheduler_thread.daemon = True
        self._zmq_req_to_scheduler_thread.start()

    def stop(self):
        # Send a ZMQ request to the inproc socket to be picked up by the poller
        zmq_termination_request_socket = self.zmq_context.socket(zmq.REQ)
        zmq_termination_request_socket.setsockopt(
            zmq.LINGER, ZMQ_SOCKET_LINGER_MSEC
        )
        zmq_termination_request_socket.connect(
            ZMQ_ADDRESS_INPROC.format(
                identifier=self.zmq_sensormanager_term_identifier
            )
        )
        zmq_termination_request_socket.send_unicode('TERMINATE')
        zmq_termination_request_socket.close()

        # And then pop a message on the queue of messages to go out just in
        # case we'd otherwise be blocked at that line.
        self.zmq_scheduler_request_queue.put_nowait(_TERMINATION_MARKER)

        # Now join the ZMQ thread and then call the parent class's stop() for
        # final cleanup.
        self._zmq_req_to_scheduler_thread.join()
        super().stop()


if __name__ == "__main__":
    application_loop(SensorManager)
