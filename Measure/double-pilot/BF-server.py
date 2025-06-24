import zmq
import time
import sys
import numpy as np
import os
from datetime import datetime, timezone
import json

if len(sys.argv) > 1:
    delay = int(sys.argv[1])
    num_subscribers = int(sys.argv[2])
else:
    delay = 5
    num_subscribers = 31

host = "*"
port = "5559"

context = zmq.Context()

alive_socket = context.socket(zmq.REP)
alive_socket.bind(f"tcp://{host}:{port}")

poller = zmq.Poller()
poller.register(alive_socket, zmq.POLLIN)

csi_data = []
hostnames = []

meas_id = 0
unique_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(script_dir, "..", "data")
os.makedirs(data_dir, exist_ok=True)
output_path = os.path.join(data_dir, f"exp-{unique_id}.yml")

print(f"Starting experiment: {unique_id}")

with open(output_path, "w") as f:
    f.write(f"experiment: {unique_id}\n")
    f.write(f"num_subscribers: {num_subscribers}\n")
    f.write(f"measurements:\n")

    while True:
        print(f"Waiting for {num_subscribers} subscribers to send a message...")
        f.write(f"  - meas_id: {meas_id}\n")
        f.write("    active_tiles:\n")

        csi_data.clear()
        hostnames.clear()

        messages_received = 0
        start_time = time.time()
        while messages_received < num_subscribers:
            socks = dict(poller.poll(1000))
            if alive_socket in socks and socks[alive_socket] == zmq.POLLIN:
                msg_json = alive_socket.recv_json()
                hostname = msg_json.get("host")
                csi_ampl = msg_json.get("csi_ampl", 0.0)
                csi_phase = msg_json.get("csi_phase", 0.0)
                csi_value = csi_ampl * np.exp(1j * csi_phase)

                hostnames.append(hostname)
                csi_data.append(csi_value)

                messages_received += 1
                print(
                    f"Received from {hostname}: {csi_ampl} {csi_phase} rad ({messages_received}/{num_subscribers})"
                )
                f.write(f"     - {hostname}\n")

                # Send the phase-inverted complex number back
                response_csi = np.conj(csi_value)
                alive_socket.send_json({
                    "real": response_csi.real,
                    "imag": response_csi.imag
                })

        print(f"DONE")
