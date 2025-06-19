#!/usr/bin/env python3
import subprocess
import threading
import sys
import yaml
from pathlib import Path

def load_inventory(inventory_file: str) -> dict:
    """Load the inventory.yaml file"""
    try:
        with open(inventory_file, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load {inventory_file}: {e}")
        sys.exit(1)

def extract_hosts_from_group(inventory: dict, group_name: str) -> list:
    """Extract the list of hostnames under the specified group"""
    children = inventory.get("all", {}).get("children", {})
    group = children.get(group_name, {})
    hosts = group.get("hosts", {})
    return list(hosts.keys())

def run_remote_script(target: str, script_path: str):
    """SSH to the target and run the given script, printing output live."""
    cmd = [
        "ssh",
        target,
        f'cd {Path(script_path).parent} && '
        'export PYTHONPATH="/usr/local/lib/python3/dist-packages:$PYTHONPATH";'
        f'python3 -u {script_path}'
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        # stream stdout
        for line in proc.stdout:
            print(f"[{target}] {line}", end='')
        proc.wait()
        # if any stderr
        err = proc.stderr.read()
        if err:
            print(f"[{target}] ERROR:\n{err}")
    except Exception as e:
        print(f"❌ Failed on {target}: {e}")

def main():
    inventory_file = "inventory.yaml"
    inventory = load_inventory(inventory_file)

    GROUP_NAME = "ceiling"
    hosts = extract_hosts_from_group(inventory, GROUP_NAME)
    if not hosts:
        print(f"❌ No hosts found in group '{GROUP_NAME}'")
        sys.exit(1)

    user = inventory.get("all", {}).get("vars", {}).get("ansible_user", "pi")
    all_hosts = inventory.get("all", {}).get("hosts", {})

    SCRIPT_REMOTE_PATH = "~/DLI_Validation/Measure/RxCSI_TX_DL.py"

    threads = []
    for host in hosts:
        info = all_hosts.get(host, {})
        ip = info.get("ansible_host")
        if not ip:
            print(f"⚠️ Skipping {host}: no ansible_host")
            continue
        target = f"{user}@{ip}"
        print(f"🚀 Launching beamform.py on {host} ({target})")
        t = threading.Thread(target=run_remote_script, args=(target, SCRIPT_REMOTE_PATH))
        t.start()
        threads.append(t)

    # wait for all to finish
    for t in threads:
        t.join()

    print("✅ beamform.py execution on all ceiling hosts completed.")

if __name__ == "__main__":
    main()
