#!/usr/bin/env python3
"""
replace_strings.py - Replace strings in files and directories
Description:
    This script replaces strings in files and directories based on a YAML configuration file.
    It creates a backup of the original file before making any changes.
Usage:
    replace_strings.py --directory <directory> --file_regex <regex> --replacements_file <yaml_file>
    replace_strings.py -h
Options:
    -h, --help            show this help message and exit
    --directory <directory>, -d <directory>
                        The directory to search for files. Defaults to the current directory.
    --file_regex <regex>, -f <regex>
                        The regular expression to match files. Defaults to ".*".
    --replacements_file <yaml_file>, -r <yaml_file>
                        A file containing the replacements to be made in YAML format.
"""

import argparse
import os
import re
import shutil

import yaml


def replace_strings_in_file(file_path, replacements):
    # Backup the original file
    shutil.copy(file_path, file_path + ".bak")

    with open(file_path, "r") as file:
        content = file.read()

    for replacement in replacements:
        old_string = replacement["old"]
        new_string = replacement["new"]
        content = content.replace(old_string, new_string)

    with open(file_path, "w") as file:
        file.write(content)

    print(f"Replaced strings in {file_path}")


def get_filepaths(directory, file_regex):
    for root, _, files in os.walk(directory):
        for file in files:
            if not re.match(file_regex, file):
                continue
            file_path = os.path.join(root, file)
            yield file_path


def main(directory, file_regex, replacements):
    filepaths = get_filepaths(directory, file_regex)

    for filepath in filepaths:
        replace_strings_in_file(filepath, replacements)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Replace strings in files and directories."
    )
    parser.add_argument(
        "--directory",
        "-d",
        help="The directory to search for files.",
        required=False,
        default=".",
    )
    parser.add_argument(
        "--file_regex",
        "-f",
        help="The regular expression to match files.",
        required=False,
        default=".*",
    )
    parser.add_argument(
        "--replacements_file",
        "-r",
        help="A file containing the replacements to be made in yaml format.",
        required=True,
    )

    args = parser.parse_args()

    directory = args.directory
    file_regex = args.file_regex
    replacements_file = args.replacements_file

    replacements = yaml.safe_load(open(args.replacements_file, "r"))

    # Replace strings in the current directory and all subdirectories
    main(directory, file_regex, replacements)
