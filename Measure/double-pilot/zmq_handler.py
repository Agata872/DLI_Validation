import logging
import zmq
import socket

class ZMQHandler(logging.Handler):
    def __init__(self, zmq_port="tcp://*:5555"):
        super().__init__()
        self.hostname = socket.gethostname()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(zmq_port)

    def emit(self, record):
        try:
            msg = self.format(record)
            full_msg = f"{self.hostname} | {msg}"
            self.socket.send_string(full_msg)
        except Exception:
            self.handleError(record)

    def close(self):
        self.socket.close()
        self.context.term()
        super().close()
