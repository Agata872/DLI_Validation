import zmq

context = zmq.Context()
socket = context.socket(zmq.PULL)
socket.bind("tcp://*:5555")  # Bind on server side

print("Log server started on tcp://*:5555")

while True:
    msg = socket.recv_string()
    print(f"[LOG] {msg}")
