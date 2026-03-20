#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import re
import sys

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="[%(asctime)s] %(levelname)8s: %(message)s"
)

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        ./ci-scripts/silentCN5G-NF.py --help
        ./ci-scripts/silentCN5G-NF.py --docker-compose-file DC_FILENAME --all-log-level error
        ./ci-scripts/silentCN5G-NF.py --docker-compose-file DC_FILENAME --all-silent'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '--docker-compose-file', '-dcf',
        action='store',
        help='Docker-compose File to modify',
    )

    # ALL NF arguments
    parser.add_argument(
        '--all-silent',
        action='store_true',
        default=False,
        help='Make all NFs silent',
    )

    parser.add_argument(
        '--all-log-level',
        action='store',
        default='',
        choices = ["info", "error", "warning"],
        help='Set all NFs to the same log level',
    )


    return parser.parse_args()

if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()
    # Finalize arguments
    if args.all_silent and args.all_log_level == '':
        args.all_log_level = 'off'

    cwd = os.getcwd()
    if not os.path.isfile(os.path.join(cwd, args.docker_compose_file)):
        logging.error(f'{args.docker_compose_file} does not exist')
        sys.exit(-1)

    lines = ''
    logLevelSectionFound = False
    with open(os.path.join(cwd, args.docker_compose_file), 'r') as rfile:
        for line in rfile:
           modifiedLine = False
           # general
           if re.search('log_level:', line) is not None and args.all_log_level != '':
               logLevelSectionFound = True
           if re.search('general: debug', line) is not None and logLevelSectionFound and args.all_log_level != '':
               newLine = re.sub('general: debug$', f'general: {args.all_log_level}', line)
               logLevelSectionFound = False
               modifiedLine = True
           if modifiedLine:
               lines += newLine
           else:
               lines += line

    with open(os.path.join(cwd, args.docker_compose_file), 'w') as wfile:
        wfile.write(lines)

    sys.exit(0)
