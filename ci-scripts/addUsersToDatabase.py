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
        ./ci-scripts/addUsersToDatabase.py --help
        ./ci-scripts/addUsersToDatabase.py --database-file SQL_FILENAME --nb-users NB_USERS_TO_ADD'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '--database-file', '-df',
        action='store',
        help='SQL File to modify',
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
    if not os.path.isfile(os.path.join(cwd, args.database_file)):
        logging.error(f'{args.database_file} does not exist')
        sys.exit(-1)

    lines = ''
    with open(os.path.join(cwd, args.database_file), 'r') as rfile:
        for line in rfile:
           lines += line
           if (re.search('208950000000128', line) is not None) and (re.search('defaultSingleNssais', line) is not None):
               count = 0
               while count < args.nb_users:
                   newImsi = format(count + 130, '08d')
                   lines += re.sub('208950000000128', f'2089500{newImsi}', line)
                   count += 1

           if (re.search('208950000000130', line) is not None) and (re.search('5G_AKA', line) is not None):
               count = 0
               while count < args.nb_users:
                   newImsi = format(count + 132, '08d')
                   lines += re.sub('208950000000130', f'2089500{newImsi}', line)
                   count += 1

    with open(os.path.join(cwd, args.database_file), 'w') as wfile:
        wfile.write(lines)

    sys.exit(0)
