# GPU Dashboard

A web-based dashboard to monitor the status of GPUs on multiple servers.

**URL:** [GPU Server Status Dashboard](http://163.17.11.82:5000/)

## Overview

This project consists of two main components:

* `gpu_exporter.py`: A script that runs on each server with GPUs. It collects GPU status information.
* `gpu_dashboard/app.py`: A Flask web application that runs on a main host. It aggregates data from all `gpu_exporter` instances and presents it in a web dashboard.

## Prerequisites

* Python 3.12
* pip (Python package installer)
* `nvidia-smi` command-line utility (usually comes with NVIDIA drivers) must be installed and working on all servers with GPUs.

## Installation

These steps need to be performed on **all servers** you want to monitor, including the main host.

1.  **Clone the  repo:**
    ```shell
    git clone https://github.com/CYUT-M416/GPU_Dashboard.git
    ```
    ```shell
    mv GPU_Dashboard GPU-Monitor
    ```

2.  **Install Flask:**
    Flask is required for both the exporter and the dashboard.
    ```shell
    # Install it to the system Python
    pip install Flask
    ```

3.  **Make scripts executable:**
    * On **all servers** (including the main host):
        ```shell
        chmod +x gpu_exporter.py
        ```
    * On the **main host only**:
        ```shell
        chmod +x gpu_dashboard/app.py
        ```

## Setup as Systemd Services

This allows the exporter and dashboard to run automatically in the background and restart on boot.

### On each GPU server (Clients)

This sets up the `gpu_exporter` service.

1.  **Create the service file:**
    ```shell
    sudo vim /etc/systemd/system/gpu_exporter.service
    ```
    Paste the following content into the file. **Important:** You **must** update `WorkingDirectory` to the absolute path where you cloned or placed the `gpu_exporter.py` script, and `ExecStart` to include the full path to `python3` if it's not in `/usr/bin/python3` and the full path to your `gpu_exporter.py` script.

    ```ini
    [Unit]
    Description=GPU Exporter Service
    After=network.target

    [Service]
    User=<YOUR_USER>
    Group=<YOUR_USER>
    WorkingDirectory=/home/<YOUR_USER>/Project/GPU-Monitor/
    ExecStart=/usr/bin/python3 gpu_exporter.py
    Restart=on-failure
    RestartSec=5
    #StandardOutput=syslog  # Optional: Send output to syslog
    #StandardError=syslog  # Optional: Send errors to syslog

    [Install]
    WantedBy=multi-user.target
    ```

2.  **Reload systemd, enable and start the service:**
    ```shell
    sudo systemctl daemon-reload
    sudo systemctl enable gpu_exporter.service
    sudo systemctl start gpu_exporter.service
    ```

3.  **Check the status (optional):**
    ```shell
    sudo systemctl status gpu_exporter.service
    journalctl -u gpu_exporter.service # To view logs
    ```

### On the Main Host Server (Dashboard)

This sets up the `gpu_dashboard` service. You also need to have set up the `gpu_exporter.service` on this machine if it has GPUs you want to monitor directly via its own exporter.

1.  **Create the service file:**
    ```shell
    sudo vim /etc/systemd/system/gpu_dashboard.service
    ```
    Paste the following content into the file. **Important:** You **must** update `WorkingDirectory` to the absolute path where you cloned or placed the `gpu_dashboard` directory, and `ExecStart` to include the full path to `python3` if it's not in `/usr/bin/python3` and the full path to your `app.py` script.

    ```ini
    [Unit]
    Description=GPU Dashboard Service
    After=network.target

    [Service]
    User=<YOUR_USER>
    Group=<YOUR_USER>
    WorkingDirectory=/home/<YOUR_USER>/Project/GPU-Monitor/gpu_dashboard/
    ExecStart=/usr/bin/python3 app.py
    Restart=on-failure
    RestartSec=5
    #StandardOutput=syslog  # Optional: Send output to syslog
    #StandardError=syslog  # Optional: Send errors to syslog

    [Install]
    WantedBy=multi-user.target
    ```

2.  **Reload systemd, enable and start the service:**
    ```shell
    sudo systemctl daemon-reload
    sudo systemctl enable gpu_dashboard.service
    sudo systemctl start gpu_dashboard.service
    ```

3.  **Check the status (optional):**
    ```shell
    sudo systemctl status gpu_dashboard.service
    journalctl -u gpu_dashboard.service # To view logs
    ```

## Configuration

* **`gpu_exporter.py`**:
    * By default, the exporter runs on port `5001`. You might need to configure this if the port is in use or if your `gpu_dashboard` expects a different port. (You'll need to modify the script if you want to change the port).
* **`gpu_dashboard/app.py`**:
    * You need to configure the list of GPU server IPs and ports that the dashboard should poll. This is typically done within the `app.py` script itself in a variable (e.g., a list of server addresses). **Please specify where this configuration is done in your `app.py` or provide a sample configuration file if you have one.**
    * The dashboard runs on port `5000` by default. This can be changed in `app.py` if needed (e.g., `app.run(host='0.0.0.0', port=NEW_PORT)`).

## Usage

1.  Ensure all `gpu_exporter.service` instances are running on your GPU servers.
2.  Ensure the `gpu_dashboard.service` is running on your main host.
3.  Open a web browser and navigate to `http://<YOUR_MAIN_HOST_IP>:5000` (or the URL you provided: `http://163.17.11.82:5000/`).

## Troubleshooting

* **Service Fails to Start:**
    * Check the service logs: `sudo journalctl -u gpu_exporter.service` or `sudo journalctl -u gpu_dashboard.service`.
    * Ensure the paths in the `.service` files (`WorkingDirectory`, `ExecStart`) are correct.
    * Verify that the scripts can be run manually: `python3 /path/to/<script.py>`.
    * Check for port conflicts if services start but are not accessible. Use `ss -tulnp | grep <port_number>`.
* **Dashboard Shows No Data or Errors:**
    * Verify that the `gpu_exporter` services are running on all target servers and accessible from the main host (check firewalls).
    * Ensure the server IPs and ports are correctly configured in `gpu_dashboard/app.py`.
    * Check the logs of the `gpu_dashboard` application.

## Contributing

If you plan for others to contribute:
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
