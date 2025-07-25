#!/usr/bin/env python3

import os
import subprocess
import sys
import argparse
import difflib
import re

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RESET = "\033[0m"


def run_git_command(scope, unset):
    if scope == "local":
        scope_tag = "--local"
    else:
        scope_tag = "--global"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(script_dir, "templates", ".git_command.env")

    # Load environment variables from the file
    env_vars = {}
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                env_vars[key] = value

    user_name = env_vars.get("user_name")
    user_email = env_vars.get("user_email")

    if scope == "local":
        print("Setting local config")
    else:
        print("Setting global config")

    before_config = subprocess.run(
        ["git", "config", scope_tag, "--list"], stdout=subprocess.PIPE, check=True
    )
    before_config_lines = before_config.stdout.decode("utf-8").split("\n")

    if setopt == "unset":
        commands_list = [
            f"git config {scope_tag} --unset-all credential.helper",
            f"git config {scope_tag} --unset-all pull.rebase",
            f"git config {scope_tag} --unset-all user.name",
            f"git config {scope_tag} --unset-all user.email",
            f"git config {scope_tag} --unset-all alias.bc",
        ]
    else:
        commands_list = [
            f'git config {scope_tag} credential.helper "cache --timeout=86400"',
            f"git config {scope_tag} pull.rebase false",
            f"git config {scope_tag} user.name {user_name}",
            f"git config {scope_tag} user.email {user_email}",
            f'git config {scope_tag} alias.bc "branch --show-current"',
        ]

    for command in commands_list:
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"{RED}{command}{RESET}")
        else:
            print(f"{GREEN}{command}{RESET}")

    after_config = subprocess.run(
        ["git", "config", scope_tag, "--list"], stdout=subprocess.PIPE, check=True
    )
    after_config_lines = after_config.stdout.decode("utf-8").split("\n")

    diff = difflib.context_diff(
        before_config_lines, after_config_lines, fromfile="before", tofile="after", n=0
    )

    difflines = list(diff)
    ignore_pattern = re.compile(r"^(?:\*\*\*|---|\+\+\+|\s*$)")
    if len(difflines) == 0:
        print("No changes made")
    else:
        print("Changes made:")
        for line in difflines:
            if ignore_pattern.match(line):
                continue
            print(f"{YELLOW}{line}{RESET}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Configure git")
    parser.add_argument(
        "--scope",
        help="The scope of the configuration (local or global)",
        choices=["local", "global"],
        required=False,
        default="global",
        dest="scope",
    )
    parser.add_argument(
        "--setopt",
        help="Set the option",
        choices=["unset", "set"],
        required=False,
        default="set",
        dest="setopt",
    )
    args = parser.parse_args()
    scope = args.scope
    setopt = args.setopt

    run_git_command(scope, setopt)
