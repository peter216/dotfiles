#!/usr/bin/env python3
"""
soft_link_files.py - Create soft links for files in a directory
Description:
    This script creates soft links for files in a directory. It creates a new directory for each LAB number and links the files from the original directory to the new directory.
Usage:
    soft_link_files.py -d DIRNAME
    soft_link_files.py -h
Options:
    -d, --debug          Enable debug logging
    -h, --help           Show this help message and exit
"""

import argparse
import logging
import os
import re

ip_address_re = r"10.82.227.\d+"


# get all files recursively under directory
def get_all_files(directory):
    file_list = []
    dir_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
        for dir in dirs:
            dir_list.append(os.path.join(root, dir))
    return dir_list, file_list


def main(directory, ip_address_re):
    logging.debug(f"Directory: {directory}")
    basedir = os.path.abspath(os.curdir)
    logging.debug(f"Base directory: {basedir}")
    parentdir = os.path.dirname(basedir)
    logging.debug(f"Parent directory: {parentdir}")

    dirs, files = get_all_files(basedir)

    for num in range(1, 35):
        padded_num_dir = f"LAB{num:02d}"
        logging.debug(f"Directory name: {padded_num_dir}")
        newdir = os.sep.join([parentdir, padded_num_dir])
        logging.debug(f"New directory: {newdir}")
        os.makedirs(newdir, exist_ok=True)
        logging.debug(f"Creating directory: {newdir}")
        for dir in dirs:
            relative_dir_path = os.path.relpath(dir, basedir)
            logging.debug(f"Relative directory path: {relative_dir_path}")
            new_subdir_path = os.sep.join([newdir, relative_dir_path])
            logging.debug(f"New subdirectory path: {new_subdir_path}")
            os.makedirs(new_subdir_path, exist_ok=True)
            logging.debug(f"Creating directory: {new_subdir_path}")

        for file in files:
            logging.debug(f"File: {file}")
            relative_path = os.path.relpath(file, basedir)
            logging.debug(f"Relative path: {relative_path}")
            if "interface_output" in relative_path:
                # Find all matches
                matches = list(re.finditer(ip_address_re, relative_path))
                if matches:
                    # Get the last match
                    last_match = matches[-1]
                    start, end = last_match.span()

                    # Replace the last match
                    new_relative_path = (
                        relative_path[:start]
                        + f"{last_match.group()}.{padded_num_dir}"
                        + relative_path[end:]
                    )
                else:
                    raise RuntimeError(
                        f"No match found for {ip_address_re} in {relative_path}"
                    )
            else:
                new_relative_path = relative_path
            logging.debug(f"New relative path: {new_relative_path}")
            new_path = os.sep.join([newdir, new_relative_path])
            logging.debug(f"New path: {new_path}")
            try:
                os.symlink(file, new_path)
                logging.debug(f"Linking {file} to {new_path}")
            except FileExistsError:
                logging.debug(f"File already exists: {new_path}")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--debug", action="store_true", help="Enable debug logging")
    args.add_argument(
        "-d", "--directory", help="Directory to create soft links in", required=False
    )
    args.add_argument("-i", "--ip_address_re", help="IP address regex", required=True)
    debug_on = args.parse_args().debug
    directory = args.parse_args().directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if directory:
        os.chdir(directory)
    else:
        os.chdir(os.path.expanduser("~"))
    ip_address_re = args.parse_args().ip_address_re
    if debug_on:
        debug_level = logging.DEBUG
    else:
        debug_level = logging.INFO
    logging.basicConfig(
        format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
        level=debug_level,
    )
    main(directory, ip_address_re)
    os.chdir(current_dir)
    logging.debug(f"Changed back to directory: {current_dir}")
    logging.debug("Script completed successfully.")
