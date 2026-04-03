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
        ./ci-scripts/checkTsharkCapture.py --help
        ./ci-scripts/checkTsharkCapture.py --log_file fileName --timeout MaxTimeInSeconds'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # Container Name
    parser.add_argument(
        '--log_file', '-n',
        action='store',
        help='FileName to stdout redirection for tshark capture',
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
        res = myCmds.run(f'cat {args.log_file}', silent=silent)
        silent = True
        if res.returncode != 0:
            status = False
            break
        run_time = time.time() - start_time
        if int(run_time) > args.timeout:
            status = False
            timeOut = True
            break
        if re.search('Capturing on', res.stdout) is not None:
            status = True
            break
        else:
            time.sleep(2)

    myCmds.close()
    run_time = time.time() - start_time
    if status:
        logging.debug(f'Started Capture in {run_time:.2f} seconds')
        sys.exit(0)
    else:
        if timeOut:
            logging.error(f'Time-out in {run_time:.2f} seconds; not ready yet')
        else:
            logging.error(f'Something went wrong!')
        sys.exit(-1)
