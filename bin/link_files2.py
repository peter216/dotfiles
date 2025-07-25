#!/usr/bin/env python3
import os
import shutil
import re

# Define the source directory
source_dir = "lab"

# Define the target directories
target_dirs = [f"LAB{str(i).zfill(2)}" for i in range(1, 35)]

# Define the replacements
replacements = {
    "BOSPBS045": "10.82.227.2.LABXX",
    "BOSPBS046": "10.82.227.4.LABXX",
    "BOSPBS047": "10.82.227.5.LABXX",
    "6200": "10.82.227.2.LABXX",
    "ProCurve 2910al-24G-PoE": "10.82.227.4.LABXX",
    "HP-2530-24": "10.82.227.5.LABXX",
}

# ip regex
ip_regex = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"


# Function to replace strings in file content
def replace_content(file_path, replacements, lab_number):
    with open(file_path, "r") as file:
        content = file.read()
    for old, new in replacements.items():
        content = content.replace(old, new.replace("LABXX", f"LAB{lab_number}"))
    return content


# Copy and replace content
for target_dir in target_dirs:
    lab_number = target_dir.split("LAB")[-1]
    os.makedirs(target_dir, exist_ok=True)
    for file_name in os.listdir(source_dir):
        source_file = os.path.join(source_dir, file_name)
        target_file_name = file_name
        if "interface_output" in file_name:
            target_file_name = re.sub(
                f"(interface_output_{ip_regex})", f"\\1.LAB{lab_number}", file_name
            )
        target_file = os.path.join(target_dir, target_file_name)
        if os.path.isfile(source_file):
            new_content = replace_content(source_file, replacements, lab_number)
            with open(target_file, "w") as f:
                f.write(new_content)
            print(f"Copied and modified {file_name} to {target_file}")

print("All files copied and modified successfully!")
