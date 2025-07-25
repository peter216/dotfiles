#!/usr/bin/env python

import json, yaml
import sys
import shutil
import os

# ANSI color codes
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    YELLOW = "\033[0;33m"
    MAUVE = "\033[0;35m"
    NC = "\033[0m"

input_file = sys.argv[1]

def main():

    if len(sys.argv) != 2:
        print(f"{Colors.RED}Usage: {sys.argv[0]} <input_file>{Colors.NC}")
        sys.exit(1)

    # Check if the file exists
    if not os.path.isfile(input_file):
        print(f"{Colors.RED}Error: File '{input_file}' not found.{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.CYAN}Sorting items in '{input_file}'...{Colors.NC}")

    try:
        with open(input_file) as f:
            jdata = json.load(f)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}Error: Failed to parse JSON file '{input_file}'.{Colors.NC}")
        print(f"{Colors.RED}Details: {e}{Colors.NC}")
        sys.exit(1)

    try:
        item_section = jdata["item"]
    except KeyError:
        print(f"{Colors.RED}Error: 'item' section not found in the JSON file.{Colors.NC}")
        sys.exit(1)

    try:
        shutil.copy(input_file, input_file + ".bak")
        print(f"{Colors.GREEN}Backup of '{input_file}' created as '{input_file}.bak'.{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}Error: Failed to create a backup of '{input_file}'.{Colors.NC}")
        print(f"{Colors.RED}Details: {e}{Colors.NC}")
        sys.exit(1)

    new_items_section = []
    # If item in item_section is a list, sort it
    if isinstance(item_section, list):
        for item in item_section:
            if isinstance(item, dict) and "item" in item:
                print(f"{Colors.MAUVE}Sorting items in '{item['name']}'...{Colors.NC}")
                item["item"] = sorted(item["item"], key=lambda i: i["name"].lower())
            new_items_section.append(item)

    # Sort the item_section itself
    new_items_section = sorted(new_items_section, key=lambda i: i["name"].lower())
    jdata["item"] = new_items_section

    print(f"{Colors.CYAN}Writing sorted items to '{input_file}'...{Colors.NC}")
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(jdata, f, indent=4)

    print(f"{Colors.GREEN}Items sorted successfully!{Colors.NC}")

if __name__ == "__main__":
    main()
