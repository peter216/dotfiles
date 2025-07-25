#!/usr/bin/env python3

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from typing import Optional

import yaml


# ANSI color codes
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    YELLOW = "\033[0;33m"
    MAUVE = "\033[0;35m"
    NC = "\033[0m"


class Config:
    """Configuration class to manage environment variables."""

    def __init__(self):
        self.loaded_variables = []
        self.load_env_variables()

    def load_env_variables(self):
        """Load environment variables from yaml string."""
        # Load environment variables from a YAML string
        env_vars = """
        GH_HOST: git.marriott.com
        """
        ydata = yaml.safe_load(env_vars)
        for key, value in ydata.items():
            if key in os.environ and os.environ[key]:
                print(
                    f"{Colors.YELLOW}Environment variable {key} already set{Colors.NC}"
                )
            else:
                os.environ[key] = value
                self.loaded_variables.append(key)
                print(f"{Colors.GREEN}Set environment variable {key}{Colors.NC}")

    def unload_env_variables(self):
        """Unload environment variables."""
        for key, value in self.loaded_variables:
            if key in os.environ:
                del os.environ[key]
                self.loaded_variables.remove(key)
                print(f"{Colors.RED}Unset environment variable {key}{Colors.NC}")
            else:
                print(
                    f"{Colors.YELLOW}Environment variable {key} not set, cannot unset{Colors.NC}"
                )


home_dir = os.path.expanduser("~")
logger = logging.getLogger(__name__)
detailed_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(lineno)d] - %(message)s"
)
try:
    file_handler = logging.FileHandler("logs/gh_script.log")
except:
    print(
        f"{Colors.YELLOW}Unable to open log file in this directory. Using home directory instead.{Colors.NC}"
    )
    os.makedirs(f"{home_dir}/logs", exist_ok=True)
    file_handler = logging.FileHandler(f"{home_dir}/logs/gh_script.log")
file_handler.setFormatter(detailed_formatter)
logger.addHandler(file_handler)


def run_command(cmd: list[str]) -> tuple[int, str]:
    """Run a command and return returncode and output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        logger.debug(f"run_command: cmd: '{cmd}'")
        logger.debug(f"run_command: result.stdout: {result.stdout}")
        logger.debug(f"run_command: result.stderr: {result.stderr}")
        logger.debug(f"run_command: result.returncode: {result.returncode}")
        return result.returncode, result.stdout
    except subprocess.SubprocessError as e:
        print(f"{Colors.RED}Error running command: {e}{Colors.NC}")
        sys.exit(1)


def get_last_run_id(workflow_name: str) -> str:
    """Get the ID of the last workflow run."""
    _, output = run_command(
        [
            "gh",
            "run",
            "list",
            "--workflow",
            workflow_name,
            "--limit",
            "1",
            "--json",
            "url",
        ]
    )
    logger.debug(f"get_last_run_id: output: {output}")
    url = json.loads(output)[0]["url"]
    id = url.split("/")[-1]
    logger.debug(f"get_last_run_id: url:{url} id:{id}")
    return id


def check_run_status(run_id: str) -> Optional[str]:
    """Check the status of a workflow run."""
    _, output = run_command(["gh", "run", "view", run_id, "--json", "conclusion"])
    status = json.loads(output)["conclusion"]
    logger.debug(f"check_run_status: output:{output} status:{status}")
    return status


def main():
    # Load environment variables
    config = Config()

    variable_commands = []

    # Define common arguments
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-v",
        "--verbosity",
        choices=["0", "1", "2", "3", "4", "5"],
        required=False,
        default="0",
        help="Verbosity level",
    )
    common_parser.add_argument(
        "-l",
        "--log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        required=False,
        default="INFO",
        dest="LOGLEVEL",
        help="Log level",
    )
    common_parser.add_argument(
        "-w",
        "--watch",
        action="store_true",
        required=False,
        default=False,
        dest="watch",
        help="Watch the workflow as it runs",
    )

    parser = argparse.ArgumentParser(
        description="GitHub Workflow Runner", parents=[common_parser]
    )

    # Create subparsers for different workflow types
    subparsers = parser.add_subparsers(dest="workflow_type", help="Sub-command help")

    # Subparser for 'diff'
    parser_diff = subparsers.add_parser(
        "diff", help="Diff workflow", parents=[common_parser]
    )
    parser_diff.add_argument(
        "-b",
        "--branch",
        required=False,
        default="production",
        help="Branch name to diff",
    )
    parser_diff.add_argument(
        "-e",
        "--send_email",
        required=False,
        default="false",
        choices=["true", "false"],
        help="Send an email to yourself",
    )
    parser_diff.add_argument(
        "-t",
        "--test",
        required=False,
        default="false",
        choices=["true", "false"],
        help="Use stub data to test the workflow",
    )
    parser_diff.add_argument(
        "--base_branch",
        required=False,
        default="production",
        dest="base_branch",
        help="The base branch to launch the workflow",
    )
    parser_diff.add_argument(
        "-s",
        "--simulate_scheduled",
        choices=["true", "false"],
        required=False,
        default="false",
        help="Simulate a scheduled event",
    )

    # Subparser for 'validate'
    parser_validate = subparsers.add_parser(
        "validate", help="Validate workflow", parents=[common_parser]
    )
    parser_validate.add_argument(
        "-tv",
        "--test_validate",
        choices=["true", "false"],
        required=False,
        default="false",
        help="Use stub data to test the workflow",
    )
    parser_validate.add_argument(
        "-xyz",
        required=False,
        default="false",
        choices=["true", "false"],
        help="XYZ mode",
    )

    # Subparser for 'deploy'
    parser_deploy = subparsers.add_parser(
        "deploy", help="Deploy workflow", parents=[common_parser]
    )
    parser_deploy.add_argument(
        "-t",
        "--ticket",
        required=False,
        default="TEST123",
        help="Ticket number",
    )
    parser_deploy.add_argument(
        "-tv",
        "--test_validate",
        choices=["true", "false"],
        required=False,
        default="false",
        help="Test validate mode",
    )
    parser_deploy.add_argument(
        "-td",
        "--test_deploy",
        choices=["true", "false"],
        required=False,
        default="false",
        help="Test deploy mode",
    )
    parser_deploy.add_argument(
        "-s",
        "--skip_pre_validation",
        choices=["true", "false"],
        required=False,
        default="false",
        help="Skip validation step",
    )
    parser_deploy.add_argument(
        "-p",
        "--push",
        choices=["true", "false"],
        required=False,
        default="false",
        help="Push to network devices",
    )
    parser_deploy.add_argument(
        "-xyz",
        required=False,
        default="false",
        choices=["true", "false"],
        help="XYZ mode",
    )
    parser_deploy.add_argument(
        "-d",
        "--debug",
        choices=["true", "false"],
        required=True,
        help="Debug mode",
    )

    # Subparser for execution environment workflow
    parser_ee = subparsers.add_parser(
        "mind.ee",
        help="Execute execution environment workflow",
        parents=[common_parser],
    )
    parser_ee.add_argument(
        "-b",
        "--branch",
        required=False,
        default="development",
        help="Branch to use for the workflow",
    )
    parser_ee.add_argument(
        "-d",
        "--directory",
        required=True,
        help="Directory on which to build the execution environment",
    )
    parser_ee.add_argument(
        "-t", "--tag", required=False, default="TEST", help="Tag to use for the image"
    )

    args = parser.parse_args()
    LOGLEVEL = args.LOGLEVEL

    # Set log level
    logger.setLevel(LOGLEVEL)

    if args.workflow_type == "deploy":
        # Define workflow_name
        workflow_name = "Deploy configuration from Arista AVD to CVP"

        cmd = [
            "gh",
            "workflow",
            "run",
            f"{workflow_name}",
            "--ref",
            "production",
            "-f",
            f"ticket={args.ticket}",
            "-f",
            f"test_deploy={str(args.test_deploy).lower()}",
            "-f",
            f"test_validate={str(args.test_validate).lower()}",
            "-f",
            f"skip_pre_validation={str(args.skip_pre_validation).lower()}",
            "-f",
            f"verbosity={args.verbosity}",
            "-f",
            f"push={str(args.push).lower()}",
            "-f",
            f"xyz={str(args.xyz).lower()}",
            "-f",
            f"debug={str(args.debug).lower()}",
        ]

    elif args.workflow_type == "diff":
        workflow_name = "Run a CVP Diff Against AVD and Network Devices"

        cmd = [
            "gh",
            "workflow",
            "run",
            f"{workflow_name}",
            "--ref",
            f"{str(args.base_branch).lower()}",
            "-f",
            f"branch={str(args.branch).lower()}",
            "-f",
            f"send_email={str(args.send_email).lower()}",
            "-f",
            f"test={str(args.test).lower()}",
            "-f",
            f"verbosity={args.verbosity}",
        ]
        if args.simulate_scheduled == "true":
            variable_cmd = [
                "gh",
                "variable",
                "set",
                "SIMULATE_SCHEDULED",
                "--body",
                "true",
            ]
            variable_commands.append(variable_cmd)

    elif args.workflow_type == "validate":
        workflow_name = "Run a validation on network devices"

        cmd = [
            "gh",
            "workflow",
            "run",
            f"{workflow_name}",
            "--ref",
            "production",
            "-f",
            f"verbosity={args.verbosity}",
            "-f",
            f"test_validate={str(args.test_validate).lower()}",
            "-f",
            f"xyz={str(args.xyz).lower()}",
        ]

    elif args.workflow_type == "mind.ee":
        workflow_name = "Manual Build Environements"
        cmd = [
            "gh",
            "workflow",
            "run",
            f"{workflow_name}",
            "--ref",
            f"{args.branch}",
            "-f",
            f"directory={args.directory}",
            "-f",
            f"tag={args.tag}",
        ]

    else:
        print(f"{Colors.RED}Error: Unknown workflow type{Colors.NC}")
        sys.exit(1)

    # Print the commands
    for variable_cmd in variable_commands:
        print(f"Running command: {' '.join(variable_cmd)}")
        returncode, _ = run_command(variable_cmd)
        if returncode != 0:
            print(f"{Colors.RED}Error setting variable{Colors.NC}")
            sys.exit(1)
    cmd_parts = [f"'{part}'" if " " in part else part for part in cmd]
    print(f"Running command: {' '.join(cmd_parts)}")
    # Run workflow
    returncode, _ = run_command(cmd)
    if returncode != 0:
        print(f"{Colors.RED}Error running GitHub workflow{Colors.NC}")
        sys.exit(1)

    print(f"{Colors.GREEN}Workflow started successfully{Colors.NC}")
    time.sleep(5)

    # Get the run ID and monitor status
    last_id = get_last_run_id(workflow_name)
    print(f"{Colors.CYAN}Run ID: {last_id}{Colors.NC}")
    if args.watch:
        print(f"{Colors.CYAN}Live watching the workflow{Colors.NC}")
        cmd = f"gh run watch {last_id}"
        subprocess.run(cmd, shell=True)
    else:
        while True:
            conclusion = check_run_status(last_id)
            if conclusion:
                print()
                if conclusion == "success":
                    print(f"{Colors.GREEN}Conclusion: {conclusion}{Colors.NC}")
                    break
                elif conclusion == "failure":
                    print(f"{Colors.RED}Conclusion: {conclusion}{Colors.NC}")
                    break
                else:
                    print(f"{Colors.MAUVE}Conclusion: {conclusion}{Colors.NC}")
                    break
            time.sleep(5)
            print(".", end="", flush=True)

    # Get and print the run link
    _, link_output = run_command(["gh", "run", "view", last_id])
    for line in link_output.splitlines():
        if "View this run on GitHub" in line:
            print(f"{Colors.YELLOW}{line}{Colors.NC}")
            break

    # Remove variables created by this script
    for variable_cmd in variable_commands:
        variable_name = variable_cmd[3]
        delete_cmd = variable_cmd[:4]
        delete_cmd[2] = "remove"
        print(f"Running command: {' '.join(delete_cmd)}")
        returncode, _ = run_command(delete_cmd)
        if returncode != 0:
            print(f"{Colors.RED}Error removing variable{Colors.NC}")
            sys.exit(1)
        else:
            print(
                f"{Colors.GREEN}variable {variable_name} removed successfully{Colors.NC}"
            )

    # Unload environment variables
    config.unload_env_variables()
    print(f"{Colors.GREEN}Run complete!{Colors.NC}")


if __name__ == "__main__":
    main()
