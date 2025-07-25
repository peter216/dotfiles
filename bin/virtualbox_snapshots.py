#!C:\Program\ Files\Python311\python.exe
import subprocess
import datetime
import re
import os

# Define variables
VM_EXE = r"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
VM_NAME = "ubuntu33"
SNAPSHOT_NAME = f"Snapshot_{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}"
LOG_FILE = r"C:\Users\prube194\VirtualBox VMs\logs\logfile.txt"

# Function to log messages
def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")

# Log the start of the script
log("Starting snapshot process.")

# Take a new snapshot and log the action
result = subprocess.run([VM_EXE, "snapshot", VM_NAME, "take", SNAPSHOT_NAME], capture_output=True, text=True)
log(result.stdout)
if result.returncode == 0:
    log(f"Snapshot {SNAPSHOT_NAME} taken successfully.")
else:
    log(f"Error taking snapshot {SNAPSHOT_NAME}. {result.stderr}")

# Get the list of snapshots and count them
result = subprocess.run([VM_EXE, "snapshot", VM_NAME, "list", "--machinereadable"], capture_output=True, text=True)
snapshots = [line for line in result.stdout.splitlines() if re.match(r"SnapshotName[0-9-]*=", line)]
count = len(snapshots)

# Log the number of snapshots
log(f"Total snapshots: {count}.")

# If there are more than 5 snapshots, delete the oldest ones and log the action
if count > 5:
    delete_count = count - 5
    for i in range(delete_count):
        snapshot_name = snapshots[i].split('=')[1].strip('"')
        result = subprocess.run([VM_EXE, "snapshot", VM_NAME, "delete", snapshot_name], capture_output=True, text=True)
        log(result.stdout)
        if result.returncode == 0:
            log(f"Snapshot {snapshot_name} deleted successfully.")
        else:
            log(f"Error deleting snapshot {snapshot_name}. {result.stderr}")

# Log the end of the script
log("Snapshot process completed.")
