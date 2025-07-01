import logging
import zmq
import socket


class ZMQPushHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.hostname = socket.gethostname()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.connect(zmq_server)

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
