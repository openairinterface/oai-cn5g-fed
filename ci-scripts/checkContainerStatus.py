#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
import logging
import re
import sys
import time
import common.python.cls_cmd as cls_cmd

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
        ./ci-scripts/checkContainerStatus.py --help
        ./ci-scripts/checkContainerStatus.py --container_name NameOfContainer --timeout MaxTimeInSeconds'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # Container Name
    parser.add_argument(
        '--container_name', '-n',
        action='store',
        help='Name of Container to follow',
    )

    # Time out in seconds
    parser.add_argument(
        '--timeout', '-t',
        action='store',
        type=int,
        default=30,
        help='Time-Out before leaving (in seconds)',
    )
    return parser.parse_args()

if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()
    start_time = time.time()

    myCmds = cls_cmd.LocalCmd()
    doLoop = True
    silent = False
    status = True
    timeOut = False
    while doLoop:
        res = myCmds.run('docker inspect --format="STATUS: {{.State.Health.Status}}" ' + args.container_name, silent=silent)
        silent = True
        if res.returncode != 0:
            status = False
            break
        run_time = time.time() - start_time
        if int(run_time) > args.timeout:
            status = False
            timeOut = True
            break
        if re.search('STATUS: healthy', res.stdout) is not None:
            status = True
            break
        else:
            time.sleep(2)

    myCmds.close()
    run_time = time.time() - start_time
    if status:
        logging.debug(f'Healthy in {run_time:.2f} seconds')
        sys.exit(0)
    else:
        if timeOut:
            logging.error(f'Time-out in {run_time:.2f} seconds; not healthy yet')
        else:
            logging.error(f'Something went wrong!')
        sys.exit(-1)
