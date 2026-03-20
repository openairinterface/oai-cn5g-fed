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
        ./ci-scripts/increaseDnnRange.py --help
        ./ci-scripts/increaseDnnRange.py docker-compose-file DC_FILENAME --nb-users NB_USERS_TO_ADD'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                     epilog=example_text,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '--docker-compose-file', '-dcf',
        action='store',
        help='Docker-compose File to modify',
    )

    parser.add_argument(
        '--nb-users', '-n',
        action='store',
        type=int,
        default=30,
        help='Number of Users to add',
    )
    return parser.parse_args()


if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()

    cwd = os.getcwd()
    if not os.path.isfile(os.path.join(cwd, args.docker_compose_file)):
        logging.error(f'{args.docker_compose_file} does not exist')
        sys.exit(-1)

    startingIP = '12.1.0.0'
    cicdrSuffix = '24'
    if args.nb_users < 1023:
        cicdrSuffix = '22'
    elif args.nb_users < 2047:
        cicdrSuffix = '21'
    elif args.nb_users < 4095:
        cicdrSuffix = '20'
    elif args.nb_users < 8191:
        cicdrSuffix = '19'
    elif args.nb_users < 16383:
        cicdrSuffix = '18'

    lines = ''
    with open(os.path.join(cwd, args.docker_compose_file), 'r') as rfile:
        for line in rfile:
            if (re.search('NETWORK_UE_IP=12.1.1.0/24', line) is not None):
                lines += re.sub('12.1.1.0/24', f'12.1.0.0/{cicdrSuffix}', line)
            elif (re.search('UE_NETWORK=12.1.1.0/24', line) is not None):
                lines += re.sub('12.1.1.0/24', f'12.1.0.0/{cicdrSuffix}', line)
            elif (re.search('ip route add 12.1.1.0/24', line) is not None):
                lines += re.sub('12.1.1.0/24', f'12.1.0.0/{cicdrSuffix}', line)
            elif (re.search('grep 12.1.1', line) is not None):
                lines += re.sub('grep 12.1.1', 'grep 12.1.0', line)
            elif (re.search('ipv4_subnet: "12.1.1.128/25"', line) is not None):
                lines += re.sub("12.1.1.128/25", "13.1.1.128/25", line)
            elif (re.search('ipv4_subnet: "12.1.1.64/26"', line) is not None):
                lines += re.sub("12.1.1.64/26", "13.1.1.64/26", line)
            elif (re.search('ipv4_subnet: "12.1.1.0/26"', line) is not None):
                lines += re.sub('12.1.1.0/26', f'{startingIP}/{cicdrSuffix}', line)
            else:
                lines += line

    with open(os.path.join(cwd, args.docker_compose_file), 'w') as wfile:
        wfile.write(lines)

    sys.exit(0)
