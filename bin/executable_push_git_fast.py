#!/usr/bin/env python
"""
push_git_fast.py - Push multiple branches to remote
Description:
    This script pushes multiple branches to remote in a git repository. It allows you to specify commit messages, branches, and options to skip linter checks or pre-commit hooks.
Usage:
    push_git_fast.py [-c COMMIT_MESSAGE] [-b BRANCH] [-dp] [-s SKIP_LINTER] [--verify] [positional]
    push_git_fast.py -h
Options:
    -h, --help            show this help message and exit
    -c COMMIT_MESSAGE, --commit-message COMMIT_MESSAGE
                        Commit message
    -b BRANCH, --branch BRANCH
                        Branch to push. Defaults to current branch
    -dp, --dontpush      Don't push to remote
    -s SKIP_LINTER, --skip_linter SKIP_LINTER
                        Skip linter
    --verify             Skip pre-commit hooks
    positional           Positional argument for commit message if only one argument is provided
"""

import argparse

# from pprint import pprint
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path

CURDIR = os.path.dirname(os.path.realpath(__file__))
LOGDIR = f"{CURDIR}/logs"
LOGLEVEL = logging.DEBUG
ansi_red = "\033[91m"
ansi_green = "\033[92m"
ansi_blue = "\033[94m"
ansi_cyan = "\033[96m"
ansi_magenta = "\033[95m"
ansi_yellow = "\033[93m"
ansi_reset = "\033[0m"

os.makedirs(LOGDIR, exist_ok=True)
logger = logging.getLogger(__name__)
detailed_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler = logging.FileHandler(f"{LOGDIR}/push_git_fast.log")
file_handler.setFormatter(detailed_formatter)
logger.addHandler(file_handler)
logger.setLevel(LOGLEVEL)


def run_command(command: list[str], capture_output: bool = False, check: bool = True) -> str | None:
    """
    Helper function to run shell and python commands.
    """

    if os.name == "nt":
        # Path to Git Bash on Windows
        bash_path = r"C:\Program Files\Git\usr\bin\bash.exe"
        norm_path = os.path.normpath(command[0])
        win_path = norm_path.split("\\")[1:]  # Remove the drive letter
        if command[0].endswith(".py"):
            command = [sys.executable, win_path] + command[1:]
        else:
            command = [bash_path, win_path] + command[1:]
    result = subprocess.run(command, capture_output=capture_output, text=True, check=check)
    return result.stdout.strip() if capture_output else None


def print_in_and_out(cmd: list[str]) -> str:
    cmd_str = " ".join(cmd)
    # print(f"{ansi_green}{cmd_str}{ansi_reset}")
    print(cmd_str)
    response = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if response.returncode != 0:
        raise Exception(
            f"Command '{cmd_str}' failed with return code {response.returncode}\n Response: {response.stdout.decode('utf-8')}"
        )
    output = response.stdout.decode("utf-8")
    print(output)
    return output


def main():
    parser = argparse.ArgumentParser(description="Push multiple branches")
    parser.add_argument(
        "-c",
        "--commit-message",
        required=False,
        help="Commit message",
    )
    (
        parser.add_argument(
            "-b",
            "--branch",
            nargs="+",
            required=False,
            action="append",
            help="Branch to push. Defaults to current branch",
        ),
    )
    parser.add_argument(
        "-dp",
        "--dontpush",
        action="store_true",
        help="Don't push to remote",
        required=False,
        default=False,
    )
    parser.add_argument(
        "-s",
        "--skip_linter",
        help="Skip linter",
        required=False,
        default="",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Skip pre-commit hooks",
        required=False,
        default=False,
    )
    parser.add_argument(
        "positional",
        nargs="?",
        help="Positional argument for commit message if only one argument is provided",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    commit_message = args.commit_message or args.positional
    if not commit_message:
        parser.print_help()
        sys.exit(1)

    if args.branch:
        branches = [b[0] for b in args.branch]
    else:
        branches = [subprocess.check_output(["git", "branch", "--show-current"]).decode("utf-8").strip()]

    verbose = args.verbose

    # Check if smart_push is in path
    smart_push_path = shutil.which("smart_push")
    if smart_push_path is None:
        # Try the Windows way
        mybindir = next(x for x in os.environ["PATH"].split(";") if x.endswith(r"prube194\bin"))
        smart_push_path = str(Path(mybindir) / "smart_push")

    if not smart_push_path:
        push_command = ["git", "push"]
        logger.debug(f"{ansi_magenta}smart_push not found in PATH, using git push instead{ansi_reset}")
    else:
        push_command = [smart_push_path]
        logger.debug(f"{ansi_magenta}smart_push found at {smart_push_path}{ansi_reset}")
    logger.info(f"{ansi_yellow}Using push command: {push_command[:]}{ansi_reset}")

    try:
        for numbranch, branch in enumerate(branches):
            new_branches = []
            print_in_and_out(["git", "checkout", branch])
            try:
                print_in_and_out(["git", "pull"])
            except Exception:
                # Maybe the upstream branch doesn't exist yet
                upstream_exists = print_in_and_out(f"git ls-remote --heads origin refs/heads/foo/{branch}".split())
                if not upstream_exists:
                    new_branches.append(branch)
                else:
                    raise

            commit_parts = ["git", "commit", "-m", f"'{commit_message}'"]
            if not args.verify:
                commit_parts.append("--no-verify")
            merge_parts = ["git", "merge", f"{branches[0]}"]
            if not args.verify:
                merge_parts.append("--no-verify")

            try:
                if numbranch == 0:
                    print_in_and_out(["git", "add", "-A"])
                    if args.skip_linter:
                        os.environ["SKIP"] = args.skip_linter
                    print_in_and_out(commit_parts)
                else:
                    print_in_and_out(merge_parts)
            except Exception as e:
                message = f"{e.__class__} : {e} : Failed to push/merge {branches[0]}"
                print(f"{ansi_red}{message}{ansi_reset}")
                raise Exception(message)
        if not args.dontpush:
            for branch in branches:
                if branch in new_branches:
                    push_parts = push_command + ["--set-upstream", "origin", branch]
                    if verbose:
                        push_parts.append("-v")
                else:
                    push_parts = push_command + ["origin", branch]
                    if verbose:
                        push_parts.append("-v")
                print_in_and_out(push_parts)
    except Exception as e:
        print(f"{e.__class__, e}")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
