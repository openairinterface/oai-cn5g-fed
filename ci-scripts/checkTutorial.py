#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import re
import sys
import subprocess
import time
from subprocess import PIPE, STDOUT

DOCKER_COMPOSE_FOLDER_NAME = "docker-compose"
DOCUMENT_FOLDER_NAME = "docs"
SLEEP_BETWEEN_COMMANDS = 1

# from https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;20m"
    reset = "\x1b[0m"
    format = "%(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger("checkTutorial")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


class CheckTutorial:
    docker_compose_dir = ""

    def __init__(self):
        self.cmds_per_block = {}
        self.tutorial_text = ""
        self.tutorial_name = ""
        self.h2_pattern = re.compile(r"^## (.*)", re.MULTILINE)
        self.shell_pattern = re.compile(r"`{3} shell\n([\S\s]+?)`{3}")
        self.cmd_pattern = re.compile(r"\$: (.*)")
        self.command_status = {}

        self.all_passed = True

    def prepare_tutorial(self, filename):
        base_path = os.path.split(os.path.abspath(filename))
        self.tutorial_name = base_path[1]
        base_path = os.path.split(base_path[0])
        self.docker_compose_dir = os.path.join(base_path[0], DOCKER_COMPOSE_FOLDER_NAME)

        if not os.path.exists(self.docker_compose_dir):
            raise Exception(f"Directory {self.docker_compose_dir} does not exist")

        with open(filename, "r") as f:
            self.tutorial_text = f.read()

        self.extract_cmds_per_h2_block()

    def extract_cmds_per_h2_block(self):
        last_end = -1
        last_header = ""
        for m in self.h2_pattern.finditer(self.tutorial_text):
            end = m.end(1)

            if last_end >= 0:
                self.extract_shell_commands(last_header, last_end, end)
            last_end = end
            last_header = m.group(1)

        # last section
        if last_end >= 0:
            self.extract_shell_commands(last_header, last_end, len(self.tutorial_text))

    def extract_shell_commands(self, title, start, end):
        cmds = []
        text_between_h2s = self.tutorial_text[start:end]
        shell_blocks = self.shell_pattern.findall(text_between_h2s)
        for block in shell_blocks:
            for cmd in self.cmd_pattern.findall(block):
                cmds.append(cmd)
        if len(cmds) > 0:
            self.cmds_per_block[title] = cmds

    def execute_all_tutorial_commands(self):
        for key in self.cmds_per_block:
            logger.warning(f"Executing commands of Section {key}")
            for cmd in self.cmds_per_block[key]:
                logger.info(f"Executing command: {cmd}")
                self.subprocess_call(cmd)
                time.sleep(SLEEP_BETWEEN_COMMANDS)

    def subprocess_call(self, command):
        popen = subprocess.Popen(command, shell=True, universal_newlines=True, cwd=self.docker_compose_dir, stdout=PIPE,
                                 stderr=STDOUT)
        for stdoutLine in popen.stdout:
            logger.debug(stdoutLine.strip())
        popen.stdout.close()
        return_code = popen.wait()

        if return_code == 0:
            self.command_status[command] = True
        else:
            self.command_status[command] = False
            self.all_passed = False
            logger.error(f"Command {command} failed!")

    def print_tutorial_summary(self):
        final_res = "\nFinal result for the tutorial {} is {}"
        if self.all_passed:
            logger.info(final_res.format(self.tutorial_name, "PASS"))
        else:
            logger.warning(final_res.format(self.tutorial_name, "FAIL"))

        pass_count = 0
        fail_count = 0
        for command in self.command_status:
            if self.command_status[command]:
                pass_count += 1
                logger.info(f"PASS : {command}")
            else:
                fail_count += 1
                logger.error(f"FAIL : {command}")

        passed = (f"{pass_count} out of {pass_count + fail_count} commands passed")
        if self.all_passed:
            logger.info(passed)
            return 0
        else:
            logger.critical(passed)
            return -1


def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        python3 checkTutorial.py --tutorial DEPLOY_SA5G_BASIC_STATIC_UE_IP.md'''

    parser = argparse.ArgumentParser(description='Run the tutorials to see they are executing fine',
                                     epilog=example_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Tutorial Name
    parser.add_argument(
        '--tutorial', '-t',
        action='store',
        required=True,
        help='name of the tutorial markdown file',
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    t = CheckTutorial()
    base_path = os.path.split(os.path.realpath(__file__))
    base_path = os.path.split(base_path[0])
    base_path = os.path.join(base_path[0], DOCUMENT_FOLDER_NAME)
    fname = os.path.join(base_path, args.tutorial)
    t.prepare_tutorial(fname)
    t.execute_all_tutorial_commands()
    return t.print_tutorial_summary()


if __name__ == "__main__":
    main()
