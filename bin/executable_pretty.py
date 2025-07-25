#!/usr/bin/env python3
"""
pretty.py - Pretty print JSON or Python objects
Description:
    This script takes a JSON or Python object as input and pretty prints it to the console or to a file.
Usage:
    pretty.py <input_file> [-o <output_file>] [-i]
    pretty.py -h
Options:
    -h, --help            show this help message and exit
    -o OUTPUT_FILE, --output_file OUTPUT_FILE
                        Output file to write
    -i, --inplace        Overwrite the input file
"""

import argparse
import ast
import json
from pprint import pformat


def make_pretty(unformatted_text):
    pyobj = ast.literal_eval(unformatted_text)
    return pformat(pyobj)


def format_json(json_text):
    jsonobj = json.loads(json_text)
    return json.dumps(jsonobj, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="input_file", help="Input file to read", type=str)
    parser.add_argument(
        "-o", "--output_file", help="Output file to write", required=False
    )
    parser.add_argument(
        "-i",
        "--inplace",
        help="Overwrite the input file",
        action="store_true",
        default=False,
    )
    args = parser.parse_args()
    if args.output_file and args.inplace:
        print("Cannot use --inplace and --output_file together")
        exit(1)
    input_file = args.input_file
    with open(input_file, "r") as f:
        unformatted_text = f.read()
    try:
        output_text = make_pretty(unformatted_text)
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}")
        try:
            output_text = format_json(unformatted_text)
        except Exception as e:
            print(f"{e.__class__.__name__}: {e}")
            print(f"Failed to parse {input_file}")
            exit(1)

    if args.output_file:
        output_file = args.output_file
        with open(output_file, "w") as f:
            f.write(output_text)
    elif args.inplace:
        with open(input_file, "w") as f:
            f.write(output_text)
    else:
        print(output_text)
