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
        ./ci-scripts/checkIperf3ClientLog.py --help
        ./ci-scripts/checkIperf3ClientLog.py --log-file path-to-file'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    # Container Name
    parser.add_argument(
        '--log-file', '-f',
        action='store',
        help='Absolute path to the iperf3 client log file to analyze',
    )
    return parser.parse_args()

if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()

    if not os.path.isfile(args.log_file):
        logging.error(f'Can not find {args.log_file}')
        sys.exit(-1)

    sentBW = 0
    receivedBW = 0
    with open(args.log_file, 'r') as logFile:
        for line in logFile:
            sender = re.search(' *(?P<bw>[0-9\\.]+) [MG]bits/sec.*sender', line)
            if sender is not None:
                sentBW = float(sender.group('bw'))
                if re.search('Mbits/sec', line) is not None:
                    sentBW *= 1000000
                else:
                    sentBW *= 1000000000
                logging.debug(f'sentBW = {sentBW}')
            receiver = re.search(' *(?P<bw>[0-9\\.]+) [MG]bits/sec.*receiver', line)
            if receiver is not None:
                receivedBW = float(receiver.group('bw'))
                if re.search('Mbits/sec', line) is not None:
                    receivedBW *= 1000000
                else:
                    receivedBW *= 1000000000
                logging.debug(f'receivedBW = {receivedBW}')

    if sentBW == 0 and receivedBW == 0:
        logging.error('Could not find summary numbers in client file')
        sys.exit(-2)
    elif receivedBW == 0:
        logging.error('Receiver did NOT receive anything')
        sys.exit(-3)
    else:
        percentage = (float) ((receivedBW - sentBW) / sentBW)
        percentage *= 100
        logging.debug(f'Error b/w sentBW and receivedBW = {percentage:2.2}%')
        if abs(percentage) > 5:
            logging.error('Too big error')
            sys.exit(-4)

    sys.exit(0)
