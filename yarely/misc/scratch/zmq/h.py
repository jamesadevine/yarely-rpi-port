import argparse
import random
import zmq


class ZMQHandler:

    def __init__(self, zmq_req_addr, zmq_rep_addr):
        self.zmq_context = zmq.Context()

        self.zmq_request_socket = self.zmq_context.socket(zmq.REQ)
        self.zmq_request_socket.connect(zmq_req_addr)

        """self.zmq_reply_socket = self.zmq_context.socket(zmq.REP)
        self.zmq_reply_socket.bind(zmq_rep_addr)"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()    
    parser.add_argument('--zmq_req', dest='zmq_req')
    parser.add_argument('--zmq_rep', dest='zmq_rep')
    args = parser.parse_args()
    handler = ZMQHandler(args.zmq_req, args.zmq_rep)
    
    for i in range(random.randrange(1,5)):
        print("H> Sending")
        handler.zmq_request_socket.send_unicode('handler says hello')
        print("H> Receiving")
        print("H> {msg}".format(msg=handler.zmq_request_socket.recv().decode()))


    # Make sure the application doesn't exit
    import time
    time.sleep(10)
    