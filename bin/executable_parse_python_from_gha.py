#!/usr/bin/env python
"""
Parse Python code from GitHub Actions workflow or restore it.

Extraction:
This script extracts Python code blocks from a GitHub Actions workflow file.
The workflow file should contain blocks of code that start with "run:"
and end with "shell: python".
The extracted code blocks are saved as separate Python files in the
specified output directory (default: current directory).
Example: parse_python_from_gha.py workflow.yaml -o ./extracted_code

Restoration:
This script can also insert Python code from files back into a workflow file.
It finds Python files matching '<workflow_basename>-pythonblock<num>.py'
in the specified input directory.
The content of each file replaces the corresponding Python block in the
workflow, applying appropriate indentation based on the 'run:' line.
The original workflow file is overwritten.
Example: parse_python_from_gha.py workflow.yaml -i ./extracted_code
"""

import argparse
import os
import re
import sys

## Pattern to find Python blocks in GitHub Actions YAML
## Group 1: The 'run:' directive line(s), including the newline
## Group 2: The Python code block itself
## Group 3: The whitespace and 'shell: python' directive line
pattern = re.compile(r"(?ms)(run:[\s|>]*\n)((?:(?!run:).)*?)(\s*shell:\s*python)")

## Global counter for replacement function
block_counter = 0


def extract_python_blocks(workflow_content, output_dir, basename):
    """Extracts Python blocks and saves them to files."""
    os.makedirs(output_dir, exist_ok=True)
    matches = pattern.findall(workflow_content)
    if not matches:
        print("No Python blocks found matching the pattern.")
        return

    output_details = {}
    print(f"Found {len(matches)} Python blocks. Extracting...")
    for num, match in enumerate(matches, start=1):
        ## The actual python code is in the second group
        python_code = match[1]
        output_details[num] = []
        lines = python_code.split("\n")

        ## Calculate minimum indentation of non-empty lines
        min_indent = float("inf")
        for line in lines:
            stripped_line = line.lstrip()
            if stripped_line:  ## Only consider non-empty lines
                indent = len(line) - len(stripped_line)
                min_indent = min(min_indent, indent)

        ## If no non-empty lines or no indentation, min_indent remains inf or 0
        if min_indent == float("inf"):
            min_indent = 0

        ## Remove common leading whitespace
        unindented_lines = []
        for line in lines:
            ## Only strip if the line has at least min_indent whitespace
            if line.startswith(" " * min_indent):
                unindented_lines.append(line[min_indent:])
            else:
                unindented_lines.append(line)  ## Keep lines with less indentation as is

        output_details[num] = unindented_lines

    for num, data in output_details.items():
        ## Construct the output file path
        output_filename = f"{basename}-pythonblock{num}.py"
        output_path = os.path.join(output_dir, output_filename)
        try:
            with open(output_path, "w") as f:
                f.write("\n".join(data))
            print(f"  Block {num} written to {output_path}")
        except IOError as e:
            print(f"Error writing file {output_path}: {e}", file=sys.stderr)


def replacer(match, workflow_content, input_dir, basename):
    """Replacement function for re.sub used in restore_python_blocks."""
    global block_counter
    block_counter += 1

    run_part = match.group(1)  ## Includes 'run: ...\n'
    ## original_python_code = match.group(2) ## Not directly used in replacement
    shell_part = match.group(3)  ## Includes '\nshell: python' or similar

    python_file_path = os.path.join(
        input_dir, f"{basename}-pythonblock{block_counter}.py"
    )

    print(f"Replacing block {block_counter} with file: {python_file_path}")

    if not os.path.exists(python_file_path):
        print(
            f"Warning: Python file not found for block {block_counter}: {python_file_path}. Skipping replacement.",
            file=sys.stderr,
        )
        ## Return the original matched text if file not found
        return match.group(0)

    try:
        with open(python_file_path, "r") as f:
            ## Read lines without trailing newlines
            python_lines = f.read().splitlines()
    except IOError as e:
        print(
            f"Warning: Error reading Python file {python_file_path}: {e}. Skipping replacement.",
            file=sys.stderr,
        )
        return match.group(0)

    ## Find the start of the line containing the 'run:' directive
    ## Search backwards from the start of the match group 1 for the previous newline
    run_line_start_pos = workflow_content.rfind("\n", 0, match.start(1)) + 1
    ## Extract the indentation of the 'run:' line itself
    run_line_indent = ""
    ## Iterate from the start of the line up to the start of the match group 1 content
    for char in workflow_content[run_line_start_pos : match.start(1)]:
        if char.isspace():
            run_line_indent += char
        else:
            ## Stop if a non-whitespace character is encountered before the run: part starts
            ## This handles multi-line run directives correctly
            break  ## Should find the indent of the line where run: starts

    ## Calculate the target indentation for the Python code (run_line_indent + 2 spaces)
    target_indent = run_line_indent + "  "

    ## Indent the Python code lines read from the file
    indented_python_lines = [target_indent + line for line in python_lines]

    ## Join the indented lines back into a single string with newlines
    indented_python_code_str = "\n".join(indented_python_lines)

    ## Reconstruct the block using group 1 (run:), the new indented code, and group 3 (shell:)
    ## Add a newline after the python code only if there was python code
    if indented_python_code_str:
        return run_part + indented_python_code_str + "\n" + shell_part.lstrip("\n")
    else:
        ## If no python code, just return run and shell parts, ensuring shell_part starts correctly
        return run_part + shell_part.lstrip("\n")


def restore_python_blocks(workflow_content, input_dir, basename):
    """Replaces Python blocks in workflow content with content from files."""
    global block_counter
    ## Reset counter for each call
    block_counter = 0

    ## List expected files first for comparison later
    try:
        expected_files = sorted(
            [
                f
                for f in os.listdir(input_dir)
                if f.startswith(f"{basename}-pythonblock") and f.endswith(".py")
            ]
        )
        if not expected_files:
            print(
                f"Warning: No Python files found matching '{basename}-pythonblock*.py' in '{input_dir}'. No changes will be made.",
                file=sys.stderr,
            )
            return workflow_content  # Return original content if no files found
    except FileNotFoundError:
        print(f"Error: Input directory '{input_dir}' not found.", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error accessing input directory '{input_dir}': {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(expected_files)} Python files in '{input_dir}'. Restoring...")

    ## Use a lambda to pass extra arguments to the replacer function
    new_content = pattern.sub(
        lambda m: replacer(m, workflow_content, input_dir, basename), workflow_content
    )

    ## Check if the number of replacements matches the number of files found
    if block_counter == 0 and len(expected_files) > 0:
        print(
            f"Warning: No Python blocks were found or replaced in the workflow file, but found {len(expected_files)} Python files in '{input_dir}'.",
            file=sys.stderr,
        )
    elif block_counter != len(expected_files):
        print(
            f"Warning: Replaced {block_counter} Python blocks in workflow, but found {len(expected_files)} matching Python files in '{input_dir}'. There might be a mismatch.",
            file=sys.stderr,
        )
    else:
        print(f"Successfully processed {block_counter} blocks.")

    return new_content


def main():
    parser = argparse.ArgumentParser(
        description="Parse Python code from GitHub Actions workflow or restore it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  Extract: %(prog)s workflow.yaml -o ./extracted_code
  Restore: %(prog)s workflow.yaml -i ./extracted_code""",
    )
    parser.add_argument("file", type=str, help="GitHub Actions workflow file")

    ## Group for mutually exclusive operations
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-o",
        "--output_dir",
        type=str,
        help="Output directory for extracted Python files (default: current dir)",
        nargs="?",
        const=".",
        default=None,  # Allows -o without value to mean current dir
    )
    group.add_argument(
        "-i",
        "--input_dir",
        type=str,
        help="Input directory containing Python files to restore",
    )

    args = parser.parse_args()
    input_file = args.file
    basename = os.path.basename(input_file)

    try:
        with open(args.file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: Workflow file not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading workflow file {args.file}: {e}", file=sys.stderr)
        sys.exit(1)

    if args.input_dir:
        ## Restore mode
        print(f"--- Restore Mode ---")
        print(f"Workflow file: {args.file}")
        print(f"Input directory: {args.input_dir}")
        modified_content = restore_python_blocks(content, args.input_dir, basename)

        if modified_content != content:
            try:
                with open(args.file, "w") as f:
                    f.write(modified_content)
                print(f"Successfully updated workflow file: {args.file}")
            except IOError as e:
                print(
                    f"Error writing updated workflow file {args.file}: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print("No changes made to the workflow file.")

    else:
        ## Extract mode (default or if -o is specified)
        output_directory = args.output_dir if args.output_dir is not None else "."
        print(f"--- Extract Mode ---")
        print(f"Workflow file: {args.file}")
        print(f"Output directory: {os.path.abspath(output_directory)}")
        extract_python_blocks(content, output_directory, basename)


if __name__ == "__main__":
    main()
