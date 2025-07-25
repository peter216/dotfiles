#!/usr/bin/env python3
"""Quick and dirty conversion from json to yaml and back"""

import json
import sys

import yaml


class AnsibleDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(AnsibleDumper, self).increase_indent(flow, indentless)


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
