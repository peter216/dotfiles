#!/usr/bin/env python3
"""
Create an Ansible inventory from a CSV file.
This script takes a CSV file as input and generates an Ansible inventory in JSON or YAML format.
The CSV file should have the following columns:
- keyvar: The key variable for the inventory.
- hostnamevar: The hostname variable for the inventory.
- groupvar: The group variable for the inventory.
- outputfile: The name of the output file.
- format: The output format (json or yaml).
"""

import argparse
import json
import logging

import pandas as pd
import requests
import yaml
from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    NAME = "inventory_from_csv"  # used internally by Ansible, it should match the file name but not required


# Turn off requests warnings
requests.packages.urllib3.disable_warnings()

# Turn on logging with more advanced formatting
logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)


def main(args):
    filename = args.filename
    keyvar = args.keyvar
    hostnamevar = args.hostnamevar
    groupvar = args.groupvar
    outputfile = args.outputfile
    output_format = args.format
    assert output_format in ["json", "yaml"], "Output format must be json or yaml."
    if hostnamevar is None:
        hostnamevar = keyvar
    if groupvar is None:
        groupvar = "all"

    inventory_df = pd.read_csv(filename)
    # Drop empty rows
    inventory_df = inventory_df[inventory_df[keyvar].notna()]
    # Drop empty columns
    inventory_df = inventory_df.dropna(axis=1, how="all")

    # Print output_df as json, grouped by groupvar
    inventory = {}
    if groupvar == "all":
        inventory_df["all"] = "all"
    grouped = inventory_df.groupby(groupvar)
    for group, data in grouped:
        data_dict = {"hosts": data.to_dict(orient="records")}
        data_values = data_dict.values()
        data_values2 = {h[hostnamevar]: h for h in list(data_values)[0]}
        data_dict = {"hosts": data_values2}
        inventory[group] = data_dict

    if output_format == "json":
        inventory_json = json.dumps(inventory, indent=4)
        with open(outputfile, "w") as f:
            f.write(inventory_json)
        print(f"Inventory is written to {outputfile}")
    elif output_format == "yaml":
        inventory_yaml = yaml.dump(inventory, indent=2)
        with open(outputfile, "w") as f:
            f.write(inventory_yaml)
        print(f"Inventory is written to {outputfile}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create an Ansible inventory from a GitHub repository."
    )
    parser.add_argument(
        "-f",
        "--filename",
        help="Name of the input file.",
        required=True,
    )
    parser.add_argument(
        "-k",
        "--keyvar",
        help="Name of the key variable.",
        required=True,
    )
    parser.add_argument(
        "-n",
        "--hostnamevar",
        help="Name of the hostname variable.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "-g",
        "--groupvar",
        help="Name of the group variable.",
        required=False,
        default=None,
    )
    parser.add_argument(
        "-o",
        "--outputfile",
        help="Name of the output file.",
        required=False,
        default="inventory.yml",
    )
    parser.add_argument(
        "--format", help="Output format (json or yaml).", required=False, default="yaml"
    )

    try:
        args = parser.parse_args()
    except Exception:
        parser.print_help()
        exit(1)

    main(args)
