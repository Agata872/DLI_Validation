#!/usr/bin/env python3

import zmq
import time
import sys
import numpy as np
import os
from datetime import datetime, timezone
import json

# Parse arguments
if len(sys.argv) > 1:
    delay = int(sys.argv[1])
    num_subscribers = int(sys.argv[2])
else:
    delay = 5
    num_subscribers = 31

# Setup
host = "*"
port = "5559"
context = zmq.Context()

# Use ROUTER socket to allow delayed reply
router_socket = context.socket(zmq.ROUTER)
router_socket.bind(f"tcp://{host}:{port}")

# Poller setup
poller = zmq.Poller()
poller.register(router_socket, zmq.POLLIN)

# Data storage
identities = []
hostnames = []
csi_data = []

# Output setup
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
        print(f"\nWaiting for {num_subscribers} subscribers to send a message...")
        f.write(f"  - meas_id: {meas_id}\n")
        f.write("    active_tiles:\n")

        # Clear for new round
        identities.clear()
        hostnames.clear()
        csi_data.clear()

        messages_received = 0
        start_time = time.time()

        # Receive all subscriber messages
        while messages_received < num_subscribers:
            socks = dict(poller.poll(1000))
            if router_socket in socks and socks[router_socket] == zmq.POLLIN:
                identity, empty, msg = router_socket.recv_multipart()
                msg_json = json.loads(msg.decode())

                hostname = msg_json.get("host")
                csi_ampl = float(msg_json.get("csi_ampl", 0.0))
                csi_phase = float(msg_json.get("csi_phase", 0.0))
                csi_value = csi_ampl * np.exp(1j * csi_phase)

                identities.append(identity)
                hostnames.append(hostname)
                csi_data.append(csi_value)

                messages_received += 1
                print(
                    f"Received from {hostname}: ampl={csi_ampl:.2f}, phase={csi_phase:.2f} rad -> CSI={csi_value:.2f} ({messages_received}/{num_subscribers})"
                )
                f.write(f"     - {hostname}\n")

            if time.time() - start_time > 10:
                print("Timeout waiting for subscribers.")
                break

        if messages_received == 0:
            continue

        # Perform computation after all messages
        avg_csi = np.mean(csi_data)
        avg_ampl = np.abs(avg_csi)
        avg_phase = np.angle(avg_csi)
        print(
            f"\nAverage CSI: {avg_csi:.4f} (ampl={avg_ampl:.2f}, phase={avg_phase:.2f} rad)"
        )

        # Send individual replies to all identities
        for identity, original_csi in zip(identities, csi_data):
            # delta_phase = np.angle(original_csi) - avg_phase
            # response = {"delta_phase": delta_phase, "avg_ampl": avg_ampl}
            response_csi = np.conj(original_csi)
            reponse = {"real": response_csi.real, "imag": response_csi.imag}
            router_socket.send_multipart([identity, b"", json.dumps(reponse).encode()])

        f.flush()
        print(f"SYNC {meas_id} complete. Sleeping {delay}s...\n")
        time.sleep(delay)
        meas_id += 1
