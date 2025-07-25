#!/usr/bin/env python3
"""
nlogin.py - Command execution script using Netmiko
"""

import argparse
import logging

from netmiko import ConnectHandler
from netmiko.channel import SSHChannel
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException


def setup_logging(logfile, verbose):
    """
    Set up logging configuration.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        filename=logfile,
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    if verbose:
        console = logging.StreamHandler()
        console.setLevel(log_level)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console.setFormatter(formatter)
        logging.getLogger().addHandler(console)


def execute_commands(connection, commands, show_command=False):
    """
    Execute a list of commands on the device.
    """
    for command in commands:
        logging.info(f"Executing command: {command}")
        output = connection.send_command(command)
        if show_command:
            print(f"{connection.base_prompt}# {command}")
        print(output)
        logging.debug(f"Command output: {output}")
        print()


def start_interactive(connection):
    """
    Start an interactive session with the device.
    """
    logging.info("Starting interactive session...")
    connection.send_command("terminal length 0")  # Disable paging
    connection.remote_conn_pre.invoke_shell()
    connection.remote_conn.settimeout(connection.blocking_timeout)
    if connection.keepalive:
        assert isinstance(connection.remote_conn.transport, paramiko.Transport)
        connection.remote_conn.transport.set_keepalive(connection.keepalive)

    # Migrating communication to channel class
    connection.channel = SSHChannel(conn=connection.remote_conn, encoding=connection.encoding)

    connection.special_login_handler()
    if connection.verbose:
        print("Interactive SSH session established")

    while connection.is_alive():
        print(f"{connection.base_prompt}# ", end="")
        try:
            command = input()
            if command.lower() in ["exit", "quit"]:
                print("Exiting interactive session.")
                break
            output = connection.send_command(command)
            print(output)
            print()
        except EOFError:
            print("End of file reached, exiting interactive session.")
            break
        except Exception as e:
            print(f"Error during interactive session: {e.__class__} {e}")
            break

    return None


def main():
    # 💠 Parse command-line arguments
    parser = argparse.ArgumentParser(description="Netmiko Command Execution Script")
    parser.add_argument("-d", "--device", required=True, help="Device hostname or IP")
    parser.add_argument("-y", "--device_type", required=True, help="Netmiko device type")
    parser.add_argument("-u", "--username", required=True, help="Username for login")
    parser.add_argument("-p", "--password", required=True, help="Password for login")
    parser.add_argument("-x", "--command_file", help="File containing commands (CRLF separated)")
    parser.add_argument("-c", "--commands", help="Semicolon-separated commands")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="Connection timeout (default: 30 seconds)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive session after running commands")
    parser.add_argument("-l", "--logfile", default="netmiko_script.log", help="Log file (default: netmiko_script.log)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging (DEBUG level)")
    parser.add_argument("--show_commands", action="store_true", help="Show commands being executed")
    args = parser.parse_args()

    # 💠 Set up logging
    setup_logging(args.logfile, args.verbose)

    # 💠 Prepare the device connection parameters
    device_params = {
        "device_type": args.device_type,
        "host": args.device,
        "username": args.username,
        "password": args.password,
        "timeout": args.timeout,
    }

    try:
        # 💠 Establish connection to the device
        logging.info(f"Connecting to {args.device}...")
        connection = ConnectHandler(**device_params)
        logging.info(f"Successfully connected to {args.device}")

        # 💠 Collect commands to execute
        commands = []
        if args.commands:
            commands.extend(args.commands.split(";"))
        if args.command_file:
            with open(args.command_file, "r") as file:
                commands.extend([line.strip() for line in file if line.strip()])

        # 💠 Execute commands
        if commands:
            logging.info("Executing commands...")
            execute_commands(connection, commands, show_command=args.show_commands)

        # 💠 Interactive session if requested
        if args.interactive:
            start_interactive(connection)

        # 💠 Close the connection
        connection.disconnect()
        logging.info("Connection closed.")

    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        logging.error(f"Connection failed: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
