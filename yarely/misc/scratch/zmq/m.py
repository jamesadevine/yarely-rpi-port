import time
import zmq
from subprocess import Popen, PIPE

class ZMQManager:
    def __init__(self):
        self.zmq_context = zmq.Context()
        
        zmq_request_port = 5554
        zmq_reply_port = 5555
        zmq_address = 'tcp://127.0.0.1:{port}'

        """self.zmq_request_socket = self.zmq_context.socket(zmq.REQ)
        self.zmq_request_socket.connect(
            zmq_address.format(port=zmq_request_port)
        )"""

        self.zmq_reply_socket = self.zmq_context.socket(zmq.REP)
        self.zmq_reply_socket.bind(
            zmq_address.format(port=zmq_reply_port)
        )

        args = ["python3.2", "./h.py", "--zmq_rep",
                zmq_address.format(port=zmq_request_port), "--zmq_req", 
                zmq_address.format(port=zmq_reply_port)]
        print(args)
        """self.subproc = Popen(args, stderr=PIPE)"""             

        
if __name__ == "__main__":
    manager = ZMQManager()
    
    count = 0
    while True: #while manager.subproc.poll() is None:
        print("M> Receiving")      
        print("M> {msg}".format(msg=manager.zmq_reply_socket.recv()))
        count += 1
        print("M> Sending {count}".format(count=count))
        manager.zmq_reply_socket.send_unicode('manager says {count}'.format(count=count))
