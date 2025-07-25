#!C:\Program\ Files\Python311\python.exe
import subprocess
import datetime
import os

# Define variables
VM_EXE = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
VM_NAME = "ubuntu33"
LOG_FILE = r"C:\Users\prube194\VirtualBox VMs\logs\launch_log.txt"

# Function to log messages
def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")

# Log the start of the script
log("Starting VM launch process.")

# Check if the VM is already running
result = subprocess.run([VM_EXE, "list", "runningvms"], capture_output=True, text=True)
running_vms = [line.split('"')[1] for line in result.stdout.splitlines() if '"' in line]

if VM_NAME in running_vms:
    log(f"VM '{VM_NAME}' is already running.")
else:
    # Launch the VM in headless mode
    result = subprocess.run([VM_EXE, "startvm", VM_NAME, "--type", "headless"], capture_output=True, text=True)
    log(result.stdout)
    if result.returncode == 0:
        log(f"VM '{VM_NAME}' started in headless mode successfully.")
    else:
        log(f"Error starting VM '{VM_NAME}'. {result.stderr}")

# Log the end of the script
log("VM launch process completed.")
