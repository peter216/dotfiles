#!/usr/bin/env python3
"""
Replace occurrences of "no_log" in files.
This script takes a list of file paths from stdin and replaces occurrences of "no_log" with "# no_log"
or "# no_log" with "no_log" based on the provided argument.
The script uses regular expressions to match the patterns and replaces them accordingly.
"""

import re
import sys


def replace_no_log_in_file(file_path):
    with open(file_path, "r") as file:
        content = file.read()

    # Replace occurrences
    if sys.argv[1] == "remove":
        updated_content = re.sub(
            r"^(\s*)no_log", r"\1# no_log", content, flags=re.MULTILINE
        )
    elif sys.argv[1] == "add":
        updated_content = re.sub(
            r"^(\s*)# no_log", r"\1no_log", content, flags=re.MULTILINE
        )
    else:
        print('Invalid argument. Use "remove" or "add"')
        sys.exit(1)

    with open(file_path, "w") as file:
        file.write(updated_content)


if __name__ == "__main__":
    for file_path in sys.stdin:
        file_path = file_path.strip()
        if file_path:
            replace_no_log_in_file(file_path)
