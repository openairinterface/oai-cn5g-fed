#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
import logging
import re
import sys
import time
import matplotlib.pyplot as plt
import common.python.cls_cmd as cls_cmd

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] %(levelname)8s: %(message)s"
)

LOOP_INTERVAL = 5
NB_GNBSIM_INSTANCES = 8
NB_PROFILES = [1, 1, 1, 1, 1, 1, 1, 1]

def main() -> None:
    #Parse arguments
    args = _parse_args()
    start_time = time.time()

    myCmds = cls_cmd.LocalCmd()
    plt.set_loglevel("info")
    logging.info('\033[0;32m OMEC gnbsim RAN emulator started, checking if all profiles finished... takes few secs\033[0m....')
    # First using docker ps to see which images were used.
    cmd = 'docker ps -a'
    res = myCmds.run(cmd)
    print(res.stdout)
    notSilentForFirstTime = False
    status = -1
    # Stats Arrays
    amfTimeX = []
    amfMemY = []
    amfCpuY = []
    nrfTimeX = []
    nrfMemY = []
    nrfCpuY = []
    ausfTimeX = []
    ausfMemY = []
    ausfCpuY = []
    udmTimeX = []
    udmMemY = []
    udmCpuY = []
    udrTimeX = []
    udrMemY = []
    udrCpuY = []
    smfTimeX = []
    smfCpuY = []
    smfMemY = []
    upfTimeX = []
    upfMemY = []
    upfCpuY = []
    x = 0
    while True:
        # Performing some statistics measurements on CPU and Memory usages for each NF
        stats = myCmds.run('docker stats --no-stream', silent=notSilentForFirstTime)
        for line in stats.stdout.split('\n'):
            if line.count('oai-amf') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    amfTimeX.append(x * LOOP_INTERVAL)
                    amfCpuY.append(float(result.group('cpu_usage')))
                    amfMemY.append(float(result.group('memory_usage')))
            if line.count('oai-nrf') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    nrfTimeX.append(x * LOOP_INTERVAL)
                    nrfCpuY.append(float(result.group('cpu_usage')))
                    nrfMemY.append(float(result.group('memory_usage')))
            if line.count('oai-ausf') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    ausfTimeX.append(x * LOOP_INTERVAL)
                    ausfCpuY.append(float(result.group('cpu_usage')))
                    ausfMemY.append(float(result.group('memory_usage')))
            if line.count('oai-udm') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    udmTimeX.append(x * LOOP_INTERVAL)
                    udmCpuY.append(float(result.group('cpu_usage')))
                    udmMemY.append(float(result.group('memory_usage')))
            if line.count('oai-udr') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    udrTimeX.append(x * LOOP_INTERVAL)
                    udrCpuY.append(float(result.group('cpu_usage')))
                    udrMemY.append(float(result.group('memory_usage')))
            if line.count('oai-smf') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    smfTimeX.append(x * LOOP_INTERVAL)
                    smfCpuY.append(float(result.group('cpu_usage')))
                    smfMemY.append(float(result.group('memory_usage')))
            if line.count('oai-upf') > 0:
                result = re.search(' (?P<cpu_usage>[0-9\\.]+)% *(?P<memory_usage>[0-9\\.]+)MiB / ', line)
                if result is not None:
                    upfTimeX.append(x * LOOP_INTERVAL)
                    upfCpuY.append(float(result.group('cpu_usage')))
                    upfMemY.append(float(result.group('memory_usage')))
        # Checking the status of each gnbsim container
        ret = []
        for idx in range(NB_GNBSIM_INSTANCES):
            cmd = f'docker logs omec-gnbsim-{idx} 2>&1 | egrep --colour=never "Summary|ERRO" || true'
            tmpRet = myCmds.run(cmd, silent=notSilentForFirstTime)
            if tmpRet is None:
                exit(f'\033[0;31m Incorrect/Unsupported executing command "{cmd}"')
            ret.append(str(tmpRet.stdout))
        notSilentForFirstTime = True
        allFinished = True
        allPassing = True
        failingForAMFnilAddress = 0
        for idx in range(NB_GNBSIM_INSTANCES):
            cnt = ret[idx].count('Profile Status:')
            passing = ret[idx].count('Profile Status: PASS')
            failingForAMFnilAddress += ret[idx].count('endToPeer failed: AMF IP address is nil')
            if cnt != NB_PROFILES[idx]:
                allFinished = False
            if passing != NB_PROFILES[idx]:
                allPassing = False
        if allFinished:
            logging.info('\033[0;32m All profiles finished\033[0m....')
            if allPassing:
                logging.info('\033[0;32m All profiles passed\033[0m....')
                status = 0
            elif failingForAMFnilAddress == 1:
                logging.info('\033[0;32m One profile failed on a single UE (maybe a gnbsim issue).\033[0m....')
                status = 0
            else:
                logging.error('\033[0;32m Some profiles failed\033[0m....')
                status = -1
            for idx in range(NB_GNBSIM_INSTANCES):
                print(ret[idx])
            break
        run_time = time.time() - start_time
        if int(run_time) > args.timeout:
            logging.error('\033[0;32m TimeOut\033[0m....')
            status = -2
            break

        time.sleep(LOOP_INTERVAL)
        x += 1
    cmd = 'docker ps -a'
    res = myCmds.run(cmd)
    print (res.stdout)
    myCmds.close()
    logging.info('Generating a plot for memory usage')
    # Generating a plot for memory usage
    plt.plot(amfTimeX, amfMemY, label='AMF')
    plt.plot(nrfTimeX, nrfMemY, label='NRF')
    plt.plot(ausfTimeX, ausfMemY, label='AUSF')
    plt.plot(udmTimeX, udmMemY, label='UDM')
    plt.plot(udrTimeX, udrMemY, label='UDR')
    plt.plot(smfTimeX, smfMemY, label='SMF')
    if len(upfTimeX) > 0:
        plt.plot(upfTimeX, upfMemY, label='UPF')
    plt.legend()
    plt.title('Memory Usage per NF')
    plt.ylabel('MiB')
    plt.xlabel('seconds')
    plt.savefig('oai-cn5g-memory.png')
    plt.cla()
    plt.clf()
    logging.info('Generating a plot for CPU usage')
    # Generating a plot for cpu usage
    plt.plot(amfTimeX, amfCpuY, label='AMF')
    plt.plot(nrfTimeX, nrfCpuY, label='NRF')
    plt.plot(ausfTimeX, ausfCpuY, label='AUSF')
    plt.plot(udmTimeX, udmCpuY, label='UDM')
    plt.plot(udrTimeX, udrCpuY, label='UDR')
    plt.plot(smfTimeX, smfCpuY, label='SMF')
    plt.plot(upfTimeX, upfCpuY, label='UPF')
    plt.legend()
    plt.title('CPU Usage per NF')
    plt.ylabel('%age')
    plt.xlabel('seconds')
    plt.savefig('oai-cn5g-cpu.png')
    if not allFinished:
        logging.error('\033[0;31m Some profiles could not finish\033[0m....')
        for idx in range(NB_GNBSIM_INSTANCES):
            print(ret[idx])
        sys.exit(-1)
    sys.exit(status)

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    parser = argparse.ArgumentParser(description='Script to check if OMEC-gnbsim deployment went OK.')

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
    main()
