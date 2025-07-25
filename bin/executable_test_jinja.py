#!/usr/bin/env python3
"""
Python script that reads a jinja expression and variables from the command line and spawns an ansible playbook to evaluate the jinja expression.

Usage: test_jinja.py -j JINJA_EXPR -v VARS_JSON

Example: test_jinja.py -j "{{ 'Hello, ' ~ world }}" -v '{"world": "planet"}'
"""

import argparse
import json
import os
import subprocess


def main():
    parser = argparse.ArgumentParser(description="Test Jinja expressions")
    parser.add_argument("-j", "--jinja", help="Jinja expression", required=True)
    (
        parser.add_argument(
            "-v", "--vars_json", help="Variables in JSON format", required=True
        ),
    )
    parser.add_argument("-d", "--debug", help="Enable debug mode", action="store_true")
    args = parser.parse_args()

    if args.debug:
        print("args")
        print("--------------------------------")
        print(args)
        print()

    jinja_expr = f'"{args.jinja}"'

    if args.debug:
        print("jinja_expr")
        print("--------------------------------")
        print(jinja_expr)
        print()

    # Read the vars into a dictionary
    vars_dict = json.loads(args.vars_json)

    if args.debug:
        print("vars_dict")
        print("--------------------------------")
        print(vars_dict)
        print()

    # Create a temporary playbook
    playbook = f"""
---
- name: Test Jinja expression
  hosts: localhost
  gather_facts: false
  tasks:"""
    if vars_dict:
        playbook += """
    - name: Set variables
      set_fact:"""
        for k, v in vars_dict.items():
            playbook += f"\n        {k}: {v}"

    playbook += f"""\n
    - name: Test Jinja expression with variables
      debug:
        msg:
"""
    playbook += f"          - {jinja_expr}\n"

    # Create playbook file
    playbook_file = "/tmp/test_jinja.yml"
    with open(playbook_file, "w") as f:
        f.write(playbook)

    if args.debug:
        print(playbook_file)
        print("--------------------------------")
        with open(playbook_file, "r") as f:
            print(f.read())

    # Run the playbook
    subprocess.run(["ansible-playbook", "-i localhost,", playbook_file])

    # Clean up
    if not args.debug:
        os.remove(playbook_file)


if __name__ == "__main__":
    main()
