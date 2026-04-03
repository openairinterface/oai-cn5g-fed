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
        ./ci-scripts/checkContainerStatus.py --container_name NameOfContainer --max_tries MaxNumberOfAttachTries'''

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
        '--max_tries', '-t',
        action='store',
        type=int,
        default=3,
        help='Maximum number of UE Attachments Tries',
    )
    return parser.parse_args()

if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()

    myCmds = cls_cmd.LocalCmd()
    doLoop = True
    status = -1
    count = 0
    while doLoop:
        if args.container_name == 'rfsim5g-oai-nr-ue1':
            time.sleep(20)
            res = myCmds.run('docker exec rfsim5g-oai-nr-ue1 ifconfig oaitun_ue1')
            if res.returncode == 0:
                if re.search('inet 12', res.stdout) is not None:
                    status = 0
                    break
            if count == args.max_tries:
                break
            myCmds.run('docker stop rfsim5g-oai-nr-ue1')
            time.sleep(5)
            myCmds.run('docker restart rfsim5g-oai-nr-ue1')
            time.sleep(10)
            count += 1
        else:
            status = 0
            break

    myCmds.close()
    sys.exit(status)
