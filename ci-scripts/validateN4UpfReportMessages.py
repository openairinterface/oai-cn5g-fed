# SPDX-License-Identifier: MIT

import argparse
import os
import re
import sys

class N4Statistics():
    def __init__(self):
        self.nbN4Messages = 0
        self.totalDuration = 0
        self.nbPacketsTotal = 0
        self.nbPacketsDL = 0
        self.nbPacketsUL = 0
        self.totalVolume = 0
        self.dlVolume = 0
        self.ulVolume = 0

    def printStats(self):
        print(f'Received {self.nbN4Messages} N4 SESSION REPORT REQUESTS from an UPF')
        print(f'-  for a total duration of {self.totalDuration} seconds')
        print(f'-  Total Number of Packets : {self.nbPacketsTotal}')
        print(f'-     DL Number of Packets : {self.nbPacketsDL}')
        print(f'-     UL Number of Packets : {self.nbPacketsUL}')
        print(f'-  Total Volume            : {self.totalVolume} bytes')
        print(f'-     DL Volume            : {self.dlVolume} bytes')
        print(f'-     UL Volume            : {self.ulVolume} bytes')

def main() -> None:
    args = _parse_args()
    status = analyzeSmfLog(args.filename)
    sys.exit(status)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Analysis for SMF/UPF N4 Report messages')

    parser.add_argument(
        '--filename', '-f',
        action='store',
        required=True,
        help='Absolute path to the SMF file to analyze'
    )
    return parser.parse_args()

def analyzeSmfLog(logfile):
    if not os.path.isfile(logfile):
        print(f'{logfile} does not exist!')
        return -1
    stats = N4Statistics()
    with open(logfile, 'r') as smfLog:
        printSection = False
        packetSection = False
        volumeSection = False
        for line in smfLog:
            if re.search('Received N4 SESSION REPORT REQUEST from an UPF', line):
                printSection = True
                stats.nbN4Messages += 1
            if re.search('itti_n4_session_report_response', line):
                printSection = False
                volumeSection = False
                packetSection = False
            if printSection:
                res = re.search('Duration        -> (?P<duration>[0-9]+)', line)
                if res is not None:
                    stats.totalDuration += int(res.group('duration'))
                res = re.search('NoP    Total    -> (?P<total>[0-9]+)', line)
                if res is not None:
                    stats.nbPacketsTotal += int(res.group('total'))
                    packetSection = True
                    volumeSection = False
                res = re.search('Volume Total    -> (?P<total>[0-9]+)', line)
                if res is not None:
                    stats.totalVolume += int(res.group('total'))
                    volumeSection = True
                    packetSection = False
                res = re.search('       Uplink   -> (?P<ul>[0-9]+)', line)
                if res is not None and packetSection:
                    stats.nbPacketsUL += int(res.group('ul'))
                if res is not None and volumeSection:
                    stats.ulVolume += int(res.group('ul'))
                res = re.search('       Downlink -> (?P<dl>[0-9]+)', line)
                if res is not None and packetSection:
                    stats.nbPacketsDL += int(res.group('dl'))
                if res is not None and volumeSection:
                    stats.dlVolume += int(res.group('dl'))
        smfLog.close()
    stats.printStats()
    if stats.nbN4Messages == 0:
        return -1
    else:
        return 0

if __name__ == '__main__':
    main()
