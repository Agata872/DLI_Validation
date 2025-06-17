#!/usr/bin/env python3
import subprocess
import sys
import yaml

def load_inventory(inventory_file):
    try:
        with open(inventory_file, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to load inventory file: {e}")
        sys.exit(1)

def extract_hosts_from_group(inventory, group_name):
    """Extract hostnames from a group"""
    children = inventory.get("all", {}).get("children", {})
    group = children.get(group_name, {})
    hosts = group.get("hosts", {})
    return list(hosts.keys())

def run_check_and_kill(target, user):
    ssh_prefix = f"{user}@{target}"
    check_cmd = "sudo lsof -i :50001 -t"

    try:
        # Execute check command via SSH
        result = subprocess.run(
            ["ssh", ssh_prefix, check_cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )

        if result.stdout.strip():
            pids = result.stdout.strip().splitlines()
            print(f"💡 [{ssh_prefix}] Listening process PID(s): {', '.join(pids)}")

            for pid in pids:
                kill_cmd = f"sudo kill -9 {pid}"
                subprocess.run(["ssh", ssh_prefix, kill_cmd])
                print(f"🗡️  [{ssh_prefix}] Terminated PID {pid}")
        else:
            print(f"✅ [{ssh_prefix}] No process listening on port 50001, skipping.")

    except subprocess.TimeoutExpired:
        print(f"⚠️  [{ssh_prefix}] SSH timeout, skipping.")
    except Exception as e:
        print(f"❌ [{ssh_prefix}] Error occurred: {e}")

def main():
    inventory_file = "inventory.yaml"
    group_name = "All"

    inventory = load_inventory(inventory_file)
    global_user = inventory.get("all", {}).get("vars", {}).get("ansible_user", "pi")
    all_hosts = inventory.get("all", {}).get("hosts", {})

    rx_names = extract_hosts_from_group(inventory, group_name)

    for name in rx_names:
        host_info = all_hosts.get(name, {})
        ansible_host = host_info.get("ansible_host")
        if not ansible_host:
            print(f"⚠️  Skipping {name}, ansible_host not found.")
            continue
        run_check_and_kill(ansible_host, global_user)

    print("🎉 Port check and cleanup completed on all devices.")

if __name__ == "__main__":
    main()
