#!/usr/bin/env python3

import os
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Create a workspace file for a project."
    )
    parser.add_argument(
        "-p", "--project_name", help="The name of the project.", required=True
    )
    parser.add_argument(
        "-s",
        "--project_name_short",
        help="The short name of the project. Defaults to the project_name.",
        required=False,
    )
    parser.add_argument("--username", help="The username of the user.", required=False)
    args = parser.parse_args()

    project_name = args.project_name
    project_name_short = args.project_name_short
    username = args.username

    # if username is not defined, get it from the environment variable
    if username is None:
        username = os.environ["GUEST_USERNAME"]
    if username is None:
        print("No username provided and no GUEST_USERNAME environment variable found.")
        parser.usage()
        exit(1)
    if project_name_short is None:
        project_name_short = project_name

    print(f"project_name: {project_name}")
    print(f"project_name_short: {project_name_short}")
    print(f"username: {username}")

    script_dir = os.path.dirname(os.path.realpath(__file__))

    subprocess.check_call(
        [
            "ansible-playbook",
            f"{script_dir}/create_code_workspace_file.yml",
            "--extra-vars",
            f"project_name={project_name} project_name_short={project_name_short} username={username}",
        ]
    )


if __name__ == "__main__":
    main()
