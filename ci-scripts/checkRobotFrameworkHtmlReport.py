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
)

from robot.api import ExecutionResult

REPORT_NAME = 'test_results_robot_framework.html'

class HtmlReport():
    def __init__(self):
        pass

    def generate(self, args):
        cwd = os.getcwd()
        status = True
        with open(os.path.join(cwd, REPORT_NAME), 'w') as wfile:
            wfile.write(generate_header(args))
            (status, testSummary) = self.testSummary('Robot Framework Tests')
            wfile.write(testSummary)
            wfile.write(generate_footer())
        if status:
            sys.exit(0)
        else:
            sys.exit(-1)

    def testSummary(self, testName):
        cwd = os.getcwd()

        if not os.path.isdir(cwd + '/archives/'):
            return ''

        testDetails = ""
        path = os.path.join(cwd, "archives")
        path = os.path.join(path, "output.xml")
        result = ExecutionResult(path)
        stats = result.statistics
        globalStatus = False
        if stats.total.passed == stats.total.total:
            statusDescription = f'All {stats.total.passed} robot tests passed!'
            globalStatus = True
        else:
            statusDescription = f'Only {stats.total.passed} out of {stats.total.total} robot tests passed'

        testDetails += generate_chapter('Robot Framework Test Summary', statusDescription, globalStatus)

        testDetails += generate_list_row(f'More details can be found in the <a href="archives/log.html"> robot framework log </a>', 'info-sign')
        testDetails += generate_list_row(f'NGAP Tester Logs on private CI server at `oaicicd@selfix:/opt/ngap-tester-logs/cn5g_fed-{args.job_name}-{args.job_id}.zip`', 'info-sign')

        return (globalStatus, testDetails)

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        ./ci-scripts/checkNgapTesterHtmlReport.py --help
        ./ci-scripts/checkNgapTesterHtmlReport.py --job_name NameOfPipeline --job_id BuildNumber --job_url BuildURL'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK NGAP-Tester HTML report',
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
