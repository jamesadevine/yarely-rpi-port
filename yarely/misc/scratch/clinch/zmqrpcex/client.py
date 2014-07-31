import logging

from yarely.frontend.core.helpers import zmq_ex
from yarely.frontend.core.helpers.base_classes import zmq_rpc_ex

logging.basicConfig(level=logging.DEBUG)

class DemoClient(zmq_rpc_ex.ZMQRPCClient):
    def add(self, *args):
        result = self.call("add", *args)
        return int(result[0])

io_loop_worker = zmq_ex.IOLoopWorker()
io_loop_worker.start()

client = DemoClient(io_loop_worker)
client.zmq_socket.connect("tcp://127.0.0.1:1234")
