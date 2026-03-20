#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
import os
import re
import sys

from common.python.generate_html import (
    generate_header,
    generate_footer,
    generate_chapter,
    generate_button_header,
    generate_button_footer,
    generate_image_table_header,
    generate_image_table_footer,
    generate_image_table_row,
    generate_image_table_separator,
    generate_list_header,
    generate_list_footer,
    generate_list_row,
    generate_list_sub_header,
    generate_list_sub_footer,
    generate_list_sub_row,
    generate_command_table_header,
    generate_command_table_row,
    generate_command_table_footer,
)

REPORT_NAME = 'test_results_oai_cn5g_load_test.html'

class HtmlReport():
    def __init__(self):
        pass

    def generate(self, args):
        cwd = os.getcwd()
        with open(os.path.join(cwd, REPORT_NAME), 'w') as wfile:
            wfile.write(generate_header(args))
            loadTests = [('Registration', 'registration-test'), \
                         ('PDU Session Establishment', 'pdu-sess-est-test'),
                         ('Deregistration', 'deregistration')]
            for (testName, testPath) in loadTests:
                wfile.write(self.testSummary(testName, testPath))
            wfile.write(generate_footer())

    def testSummary(self, testName, testPath):
        cwd = os.getcwd()

        if not os.path.isdir(cwd + '/archives/' + testPath):
            return ''

        log_files = sorted(os.listdir(cwd + '/archives/' + testPath))
        deployedContainerImages = []
        byeMessages = []
        for log_file in log_files:
            if not log_file.endswith(".log"):
                continue
            if re.search('oai-cn5g-load-test', log_file) is not None:
                continue
            containerName = re.sub('.log.*$', '', log_file)
            if re.search('omec-gnbsim', containerName) is not None:
                imageRootName = '5gc-gnbsim:'
                fileRootName = '5gc-gnbsim'
            else:
                imageRootName = f'{containerName}:'
                fileRootName = containerName
            imageTag = ''
            imageSize = ''
            imageDate = ''
            if not os.path.isfile(cwd + '/archives/' + fileRootName + '-image-info.log'):
                continue
            with open(cwd + '/archives/' + fileRootName + '-image-info.log','r') as imageDetailsFile:
                for line in imageDetailsFile:
                    result = re.search('Tested Tag is .*.*:(?P<tag>[a-zA-Z0-9\\-\\_]+)', line)
                    if result is not None:
                        imageTag = result.group('tag')
                    result = re.search('Size = (?P<size>[0-9]+) bytes', line)
                    if result is not None:
                        sizeInt = int(result.group('size'))
                        if sizeInt < 1000000:
                            sizeInt = int(sizeInt / 1000)
                            imageSize = str(sizeInt) + ' kB'
                        else:
                            sizeInt = int(sizeInt / 1000000)
                            imageSize = str(sizeInt) + ' MB'
                    result = re.search('Date = (?P<date>[a-zA-Z0-9\\-\\_:]+)', line)
                    if result is not None:
                        imageDate = re.sub('T', '  ', result.group('date'))
            deployedContainerImages.append((containerName, f'{imageRootName}{imageTag}', imageSize, imageDate))
            if fileRootName == '5gc-gnbsim':
                continue
            byeMessagePresent = False
            with open(cwd + f'/archives/{testPath}/{containerName}.log','r') as nfRuntimeLogFile:
                for line in nfRuntimeLogFile:
                    result = re.search('system.*info.* Bye. Shutdown Procedure took (?P<duration>[0-9]+) ms', line)
                    if result is not None and not byeMessagePresent:
                        byeMessagePresent = True
                        duration = int(result.group('duration'))
                        byeMessages.append((containerName, f'{containerName}   -- properly shutdown in {duration} ms  -- See {testPath}/{containerName}.log for details', True))
            if not byeMessagePresent:
                byeMessages.append((containerName, f'{containerName}   --   {testPath}/{containerName}.log -- does not show Bye message', False))

        instancesDetails = []
        fullTestStatus = True
        fullCountUePassed = 0
        fullCountUeFailed = 0
        for log_file in log_files:
            if not log_file.endswith(".log"):
                continue
            if re.search('omec-gnbsim', log_file) is None:
                continue
            testCompleted = False
            testPassed = False
            profileName = ''
            profileType = ''
            passedUeCount = 0
            failedUeCount = 0
            with open(cwd + '/archives/' + testPath + '/' + log_file,'r') as gnbsimLog:
                for line in gnbsimLog:
                    if re.search('ExecuteProfile ended', line) is not None:
                        testCompleted = True
                    pName = re.search('Init profile: (?P<name>[a-zA-Z0-9\\-]+).*profile type: (?P<type>[a-zA-Z0-9\\-]+)', line)
                    if pName is not None:
                        profileName = pName.group('name')
                        profileType = pName.group('type')
                    ueCount = re.search('Ue\'s Passed: (?P<pass>[0-9]+) , Ue\'s Failed: (?P<fail>[0-9]+)', line)
                    if ueCount is not None:
                        passedUeCount = int(ueCount.group('pass'))
                        failedUeCount = int(ueCount.group('fail'))
                    if re.search('Profile Status: PASS', line) is not None:
                        testPassed = True
                    # In case of the test not completing
                    if re.search('No more procedures left', line) is not None:
                        passedUeCount += 1
            instancesDetails.append((testCompleted, testPassed, profileName, profileType, passedUeCount, failedUeCount))
            if not testCompleted or not testPassed:
                fullTestStatus = False
            fullCountUePassed += passedUeCount
            fullCountUeFailed += failedUeCount

        testDetails = ''
        if fullCountUeFailed == 0 and fullTestStatus:
            message = f'Test Passed for all {fullCountUePassed} Users'
        elif fullCountUeFailed == 0:
            message = f'Test Completed for only {fullCountUePassed} Users'
        else:
            message = f'Test Passed for only {fullCountUePassed} Users and Failed for {fullCountUeFailed}'
        testDetails += generate_chapter(f'Load Test Summary for {testName}', message, fullTestStatus)
        testDetails += generate_button_header(f'{testPath}-details', 'More details on load test results')
        testDetails += generate_image_table_header()
        for (cName,iTag,iSize,iDate) in deployedContainerImages:
            if cName == 'omec-gnbsim-0':
                testDetails += generate_image_table_separator()
            testDetails += generate_image_table_row(cName, iTag, 'N/A', iDate, iSize)
        testDetails += generate_image_table_footer()
        testDetails += re.sub('Command', 'Shutdown procedure', generate_command_table_header())
        for (containerName, byeMessage, byeStatus) in byeMessages:
            testDetails += generate_command_table_row(byeMessage, byeStatus)
        testDetails += generate_command_table_footer()
        testDetails += generate_list_header()
        for (comp, status, pName, pType, passUe, failUe) in instancesDetails:
            if status:
                testDetails += generate_list_row(f'{pName} -- {pType} completed and PASSED', 'info-sign')
            elif comp:
                testDetails += generate_list_row(f'{pName} -- {pType} completed but FAILED', 'remove-sign')
            else:
                testDetails += generate_list_row(f'{pName} -- {pType} did not completed', 'remove-sign')
            testDetails += generate_list_sub_header()
            if comp:
                testDetails += generate_list_sub_row('Passing UE count', str(passUe), 'primary')
                if status:
                    testDetails += generate_list_sub_row('Failing UE count', str(failUe), 'primary')
                else:
                    testDetails += generate_list_sub_row('Failing UE count', str(failUe), 'danger')
            else:
                testDetails += generate_list_sub_row('Completed UE test count', str(passUe), 'danger')
            testDetails += generate_list_sub_footer()

        testDetails += generate_list_footer()
        testDetails += generate_button_footer()
        return testDetails

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        ./ci-scripts/checkLoadTestHtmlReport.py --help
        ./ci-scripts/checkLoadTestHtmlReport.py --job_name NameOfPipeline --job_id BuildNumber --job_url BuildURL'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Load Test HTML report',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # Job Name
    parser.add_argument(
        '--job_name', '-n',
        action='store',
        help='Pipeline is called JOB_NAME',
    )

    # Job Build Id
    parser.add_argument(
        '--job_id', '-id',
        action='store',
        help='Build # JOB_ID',
    )

    # Job URL
    parser.add_argument(
        '--job_url', '-u',
        action='store',
        help='Pipeline provides an URL for this run',
    )

    return parser.parse_args()

#--------------------------------------------------------------------------------------------------------
#
# Start of main
#
#--------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()

    # Generate report
    HTML = HtmlReport()
    HTML.generate(args)
