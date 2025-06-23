#!/usr/bin/env python3
import subprocess
import threading
import sys
import yaml

def load_inventory(inventory_file):
    """Load the inventory.yaml file"""
    try:
        with open(inventory_file, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load {inventory_file}: {e}")
        sys.exit(1)

def extract_hosts_from_group(inventory, group_name):
    """Extract the list of hostnames under the specified group"""
    children = inventory.get("all", {}).get("children", {})
    group = children.get(group_name, {})
    hosts = group.get("hosts", {})
    return list(hosts.keys())

def run_remote_script(target, script_path):
    """Execute the specified script on the remote device via SSH and print output in real-time."""
    remote_cmd = (
        'cd ~/DLI_Validation/Measure && '
        'export PYTHONPATH="/usr/local/lib/python3/dist-packages:$PYTHONPATH"; '

        f'python3 -u {script_path}'
    )
    cmd = ["ssh", target, remote_cmd]
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)

        # Read stdout in real-time
        for line in process.stdout:
            print(f"[{target}] Output: {line}", end='')

        process.wait()

        # Print stderr (if any)
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"[{target}] Error Output:\n{stderr_output}")

    except Exception as e:
        print(f"❌ Failed to run script on {target}: {e}")

def main():
    inventory_file = "inventory.yaml"
    inventory = load_inventory(inventory_file)

    TX_NAME = "M01"
    RX_GROUP_NAME = "ceiling"
    RX_NAMES = extract_hosts_from_group(inventory, RX_GROUP_NAME)

    global_user = inventory.get("all", {}).get("vars", {}).get("ansible_user", "pi")
    all_hosts = inventory.get("all", {}).get("hosts", {})

    if TX_NAME not in all_hosts:
        print(f"❌ Transmitter {TX_NAME} not found in inventory")
        sys.exit(1)
    tx_ip = all_hosts[TX_NAME].get("ansible_host")
    if not tx_ip:
        print(f"❌ Transmitter {TX_NAME} is missing the ansible_host attribute")
        sys.exit(1)
    tx_target = f"{global_user}@{tx_ip}"

    TX_SCRIPT_PATH = "~/DLI_Validation/Measure/Tx.py"
    RX_SCRIPT_PATH = "~/DLI_Validation/Measure/beamform.py"

    threads = []
    processes = []

    def run_and_store(target, path):
        """Wrap run_remote_script and store Popen process"""
        remote_cmd = (
            'cd ~/DLI_Validation/Measure && '
            'export PYTHONPATH="/usr/local/lib/python3/dist-packages:$PYTHONPATH"; '
            f'python3 -u {path}'
        )
        cmd = ["ssh", target, remote_cmd]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            processes.append(process)

            for line in process.stdout:
                print(f"[{target}] Output: {line}", end='')
            process.wait()
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"[{target}] Error Output:\n{stderr_output}")
        except Exception as e:
            print(f"❌ Failed to run script on {target}: {e}")

    try:
        print(f"🚀 Starting transmitter {TX_NAME} ({tx_target}) ...")
        tx_thread = threading.Thread(target=run_and_store, args=(tx_target, TX_SCRIPT_PATH))
        threads.append(tx_thread)
        tx_thread.start()

        for rx_name in RX_NAMES:
            if rx_name not in all_hosts:
                print(f"⚠️ Skipping receiver {rx_name}, host not found in inventory")
                continue
            rx_ip = all_hosts[rx_name].get("ansible_host")
            if not rx_ip:
                print(f"⚠️ Skipping receiver {rx_name}, missing ansible_host")
                continue
            rx_target = f"{global_user}@{rx_ip}"
            print(f"📡 Starting receiver {rx_name} ({rx_target}) ...")
            rx_thread = threading.Thread(target=run_and_store, args=(rx_target, RX_SCRIPT_PATH))
            threads.append(rx_thread)
            rx_thread.start()

        for t in threads:
            t.join()

    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C detected. Terminating all SSH processes...")
        for proc in processes:
            if proc.poll() is None:  # still running
                proc.terminate()
        print("✅ All remote scripts terminated.")

    finally:
        print("🔚 Coordination script finished.")

if __name__ == "__main__":
    main()
