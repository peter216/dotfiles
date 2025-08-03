#!/usr/bin/env python3
"""Quick and dirty conversion from json to yaml and back"""

import json
import os
import sys

import yaml


class AnsibleDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(AnsibleDumper, self).increase_indent(flow, indentless)


debug = os.getenv("DEBUG")
if debug:
    print(f"sys.argv: {sys.argv}", file=sys.stderr)
    print(f"sys.stdin: {sys.stdin}", file=sys.stderr)

if len(sys.argv) > 1:
    input_file = sys.argv[1]
    if input_file.endswith(".json"):
        jdata = json.load(open(input_file))
        yaml_data = yaml.dump(jdata, Dumper=AnsibleDumper)
        print("---\n")
        print(yaml_data)
    elif input_file.endswith(".yml") or input_file.endswith(".yaml"):
        ydata = yaml.load(open(input_file), Loader=yaml.SafeLoader)
        json_data = json.dumps(ydata, indent=4)
        print(json_data)
# Otherwise take input from stdin
else:
    try:
        jdata = json.load(sys.stdin)
        yaml_data = yaml.dump(jdata, Dumper=AnsibleDumper)
        print("---\n")
        print(yaml_data)
    except json.JSONDecodeError:
        ydata = yaml.load(sys.stdin, Loader=yaml.SafeLoader)
        json_data = json.dumps(ydata, indent=4)
        print(json_data)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
