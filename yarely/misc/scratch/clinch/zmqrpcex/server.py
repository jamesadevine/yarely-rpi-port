import logging

from yarely.frontend.core.helpers import zmq_ex
from yarely.frontend.core.helpers.base_classes import zmq_rpc_ex

logging.basicConfig(level=logging.DEBUG)

class DemoServer(zmq_rpc_ex.ZMQRPCServer):
    def handle_add(self, *args):
        return sum(args)
    handle_add.arg_types = [int]

io_loop_worker = zmq_ex.IOLoopWorker()
io_loop_worker.start()

server = DemoServer(io_loop_worker)
server.zmq_socket.bind("tcp://127.0.0.1:1234")
