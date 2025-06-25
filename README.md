# 📡 DLI\_Validation Beamforming System

This project provides tools for managing and performing distributed beamforming measurements using USRP B210 devices. It includes tools for synchronization, configuration, and measurement orchestration, using `zmq`, `ansible`, and custom Python scripts.

---

## 🗂️ Directory Structure

```
/storage/gilles/DLI_Validation
├── Ansible
│   ├── delete_file.yml              # Delete remote files
│   ├── grant_permissions.yml        # Fix execution permissions
│   ├── inventory.yaml               # List of target hosts
│   ├── kill.yml                     # Kill running measurement scripts
│   └── pull_code.yml                # Pull the latest code from Git
├── Measure
│   ├── data/                        # Auto-generated measurement result files (YAML)
│   ├── double-pilot/                # Double pilot BF implementation
│   │   ├── BF-server.py             # Receives CSI, computes BF weights
│   │   ├── beamform.py              # Applies beamforming weights
│   │   ├── combingTxRx.py           # Transmits and receives signal for measurement
│   │   ├── generateBFcoeff.py       # Computes BF coefficients
│   │   ├── sync-server.py           # Synchronization message server
│   │   ├── config*.yml              # Configuration files
│   │   ├── usrp_b210_fpga_loopback_ctrl.bin # Custom FPGA image
│   │   └── *.py, *.yml              # Supporting utilities and configs
│   ├── single-pilot/                # Single pilot BF variant
│   │   └── (same structure as double-pilot)
│   └── usrp_b210_fpga_loopback_ctrl.bin     # Shared binary
└── Process
    └── process.ipynb                # Jupyter notebook for post-processing measurements
```

---

## 🚀 Measurement Workflow

### On the server:

1. **Kill and pull latest code:**

   ```bash
   ansible-playbook Ansible/kill.yml
   ansible-playbook Ansible/pull_code.yml
   ```

2. **Start synchronization server:**

   ```bash
   python3 Measure/double-pilot/sync-server.py
   ```

3. **Start beamforming server:**

   ```bash
   python3 Measure/double-pilot/BF-server.py
   ```

4. **Start TX/RX orchestration:**

   ```bash
   python3 Measure/double-pilot/combingTxRx.py
   ```

---

## 🧪 TODO

* ✅ Add M01 cable and configure TX board accordingly
* 🔧 Extend `BF-server.py` to also:

  * Compute a second beamforming weight
  * Enable **zero forcing** via CSI combination
