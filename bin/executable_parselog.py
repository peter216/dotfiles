#!/usr/bin/env python
"""
parselog.py - Parse Ansible log files
Description:
    This script parses Ansible log files and extracts the output for a specific host or all hosts.
    It can also skip skipped tasks if specified. It creates a tmp directory in the current path for the files. It then attempts to open the new files in VS Code.
Usage:
    parselog.py -n <HOSTNAME> -f <INPUTFILE> [-s]
    parselog.py -a -f <INPUTFILE> [-s]
    parselog.py -h
Options:
    -h, --help            show this help message and exit
    -n HOSTNAME, --hostname HOSTNAME
                        Hostname(s) (may be IP address) to match
    -a, --all            Match all hosts
    -f INPUTFILE, --file INPUTFILE
                        Input file to process
    -s, --no-skipped     Don't print skipped tasks
    -d, --debug          Debug output
    -v, --verbose        Verbose output
"""

import argparse
import logging
import os
import re
import tempfile

debug = True


def main(options):
    verbose = options.verbose
    if verbose or debug:
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    hostnames = options.hostnames
    inputfile = options.inputfile
    skip_skipped = options.skip_skipped
    all_hosts = options.all_hosts

    logdir = os.path.join(os.path.expanduser("~"), ".parselog")
    os.makedirs(logdir, exist_ok=True)
    logger = logging.getLogger(__name__)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler = logging.FileHandler(f"{logdir}/parselog.log")
    # handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(loglevel)

    logger.debug("hostnames: {}".format(hostnames))
    logger.debug("inputfile: {}".format(inputfile))
    logger.debug("skip_skipped: {}".format(skip_skipped))
    logger.debug("all_hosts: {}".format(all_hosts))
    logger.debug("verbose: {}".format(verbose))

    assert len(hostnames) > 0 or all_hosts, (
        "Must specify at least one hostname or --all"
    )
    assert not (len(hostnames) > 0 and all_hosts), (
        "Cannot specify both hostnames and --all"
    )
    assert inputfile, "Must specify an input file"

    all_hosts_pattern = r"^\w+: \[([\S]+?)\] =>"
    with open(inputfile, "r", encoding="ASCII", errors="ignore") as file:
        inputfile_contents = file.read()
    if all_hosts:
        found_hosts = re.findall(all_hosts_pattern, inputfile_contents, re.MULTILINE)
        hostnames = set(found_hosts)

    # Create a temporary directory
    inputfilebase = os.path.basename(inputfile).split(".")[0]
    tempdir = tempfile.mkdtemp(prefix=f"{inputfilebase}.", suffix=".tmpdir", dir=".")
    logger.debug("tempdir: {}".format(tempdir))

    for inventory_hostname in hostnames:
        logger.debug("inventory_hostname: {}".format(inventory_hostname))
        if skip_skipped:
            host_pattern = re.compile(
                rf"\b(?!skipping\b)[a-z]+\b: \[{re.escape(inventory_hostname)}\]"
            )
        else:
            host_pattern = re.compile(rf"\w+: \[{re.escape(inventory_hostname)}\]")
        task_pattern = re.compile(r"TASK")
        close_brace_pattern = re.compile(r"\}\s*$")
        other_host_pattern = re.compile(rf"\w+: \[(?!{inventory_hostname})[\S]+]")
        empty_line_pattern = re.compile(r"^\s*$")
        printing = False
        check_nextline_blank = False
        latest_task = ""
        outputlist = []

        with open(inputfile, "r", encoding="ASCII", errors="ignore") as file:
            for line in file:
                if task_pattern.match(line):
                    printing = False
                    latest_task = line
                if host_pattern.match(line):
                    printing = True
                    outputlist.append("\n")
                    outputlist.append(latest_task)
                if printing:
                    outputlist.append(line)
                if close_brace_pattern.match(line):
                    printing = False
                if close_brace_pattern.search(line):
                    check_nextline_blank = True
                if empty_line_pattern.match(line):
                    if check_nextline_blank:
                        printing = False
                        check_nextline_blank = False

        logger.debug("length of outputlist: {}".format(len(outputlist)))
        outputfile = os.path.join(
            tempdir, "examine-{}-{}".format(inventory_hostname, inputfile)
        )
        logger.debug("outputfile: {}".format(outputfile))
        with open(outputfile, "w") as file:
            for line in outputlist:
                if not other_host_pattern.match(line):
                    file.write(line)

    print(tempdir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="""
        %(prog)s [options] -n <HOSTNAME> [-n <HOSTNAME>] -f <INPUTFILE> [-s]
        %(prog)s [options] -a -f <INPUTFILE> [-s]
        """
    )
    parser.add_argument(
        "-n",
        "--hostname",
        dest="hostnames",
        action="append",
        default=[],
        help="Hostname(s) (may be IP address) to match",
    )
    parser.add_argument(
        "-a",
        "--all",
        dest="all_hosts",
        action="store_true",
        default=False,
        help="Match all hosts",
    )
    parser.add_argument("-f", "--file", dest="inputfile", help="Input file to process")
    parser.add_argument(
        "-s",
        "--no-skipped",
        dest="skip_skipped",
        action="store_true",
        default=False,
        help="Don't print skipped tasks",
    )
    parser.add_argument(
        "-d",
        "--debug",
        dest="debug",
        action="store_true",
        default=False,
        help="Debug output",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        default=False,
        help="Verbose output",
    )

    options = parser.parse_args()

    main(options)
