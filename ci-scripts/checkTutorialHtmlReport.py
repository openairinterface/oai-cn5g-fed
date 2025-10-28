#!/usr/bin/env python3
"""
Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The OpenAirInterface Software Alliance licenses this file to You under
the OAI Public License, Version 1.1  (the "License"); you may not use this file
except in compliance with the License.
You may obtain a copy of the License at

  http://www.openairinterface.org/?page_id=698

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
For more information about the OpenAirInterface (OAI) Software Alliance:
  contact@openairinterface.org

---------------------------------------------------------------------
"""

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
    generate_command_table_header,
    generate_command_table_footer,
    generate_command_table_row,
)

REPORT_NAME = 'test_results_oai_cn5g_tutorials.html'

class HtmlReport():
	def __init__(self):
		pass

	def generate(self, args):
		cwd = os.getcwd()
		with open(os.path.join(cwd, REPORT_NAME), 'w') as wfile:
			wfile.write(generate_header(args))

			tutorials = ['mini-gnbsim', 'static-ue-ip', 'slicing-with-nssf', 'ulcl-scenario', 'mongodb-test', 'upf-ebpf-gnbsim', 'qos-testing']
			for tutorial in tutorials:
				if not os.path.isfile(cwd + '/archives/' + tutorial + '.log'):
					continue
				if not os.path.isdir(cwd + '/archives/' + tutorial):
					continue
				wfile.write(self.tutorialSummary(tutorial))

			wfile.write(generate_footer())

	def tutorialSummary(self, tutorial):
		cwd = os.getcwd()
		tutoName = ''
		tutoStatus = True
		cmdSummary = False
		listOfCmds = []
		nbAllCmds = '0'
		nbPassCmds = '0'
		with open(cwd + '/archives/' + tutorial + '.log','r') as tutoLog:
			for line in tutoLog:
				if cmdSummary:
					pushToList = True
					passFailStatus = re.search('FAIL', line)
					nbCommands = re.search('(?P<pass>[0-9]+) out of (?P<all>[0-9]+) commands passed', line)
					if passFailStatus is not None:
						cmd = re.sub('^.*FAIL : ', '', line.strip())
						cmdStatus = False
					elif nbCommands is not None:
						nbAllCmds = nbCommands.group('all')
						nbPassCmds = nbCommands.group('pass')
						pushToList = False
					else:
						cmd = re.sub('^.*PASS : ', '', line.strip())
						cmdStatus = True
					cmd = re.sub('\\[0m.*$', '', cmd)
					if pushToList:
						listOfCmds.append((cmd,cmdStatus))
				result = re.search('Final result for the tutorial (?P<doc_name>[a-zA-Z0-9\\.\\_:]+)', line)
				if result is not None:
					cmdSummary = True
					tutoName = result.group('doc_name')
					if re.search('FAIL', line) is not None:
						tutoStatus = False
		tutoLog.close()

		log_files = sorted(os.listdir(cwd + '/archives/' + tutorial))
		deployedContainerImages = []
		byeMessages = []
		for log_file in log_files:
			if not log_file.endswith(".log"):
				continue
			if re.search('gnbsim', log_file) is not None or \
			   re.search('rfsim5g-oai', log_file) is not None or \
			   re.search('ueransim', log_file) is not None:
				continue
			rootName = re.sub('.log.*$', '', log_file)
			containerName = 'oai-' + rootName
			if re.search('vpp-upf', rootName) is not None:
				imageRootName = 'oai-upf-vpp:'
				fileRootName = 'upf-vpp'
				containerName = rootName
			else:
				imageRootName = 'oai-' + re.sub('-slice.*','',rootName) + ':'
				fileRootName = re.sub('-slice.*','',rootName)
			imageTag = ''
			imageSize = ''
			imageDate = ''
			if not os.path.isfile(cwd + '/archives/oai-' + fileRootName + '-image-info.log'):
				continue
			with open(cwd + '/archives/oai-' + fileRootName + '-image-info.log','r') as imageDetailsFile:
				for line in imageDetailsFile:
					result = re.search('Tested Tag is oai-.*:(?P<tag>[a-zA-Z0-9\\-\\_]+)', line)
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
			deployedContainerImages.append((containerName, imageRootName + imageTag, imageSize, imageDate))
			if re.search('vpp-upf', rootName) is not None:
				continue
			byeMessagePresent = False
			with open(cwd + f'/archives/{tutorial}/{log_file}','r') as nfRuntimeLogFile:
				for line in nfRuntimeLogFile:
					result = re.search('system.*info.* Bye. Shutdown Procedure took (?P<duration>[0-9]+) ms', line)
					if result is not None and not byeMessagePresent:
						byeMessagePresent = True
						duration = int(result.group('duration'))
						byeMessages.append((containerName, f'{containerName}   -- {rootName} properly shutdown in {duration} ms  -- See {tutorial}/{log_file} for details', True))
			if not byeMessagePresent:
				byeMessages.append((containerName, f'{containerName}   --   {tutorial}/{log_file} -- {rootName} does not show Bye message', False))

		if tutoName == '':
			return ''

		tutoText = ''
		if tutoStatus:
			tutoText += generate_chapter('Tutorial Check Summary', f'Successful Check for {tutoName} : all {nbAllCmds} commands PASSED', tutoStatus)
		else:
			tutoText += generate_chapter('Tutorial Check Summary', f'Failed Check for {tutoName}: ONLY {nbPassCmds} over {nbAllCmds} commands passed', tutoStatus)

		tutoText += generate_button_header(f'{tutorial}-details', 'More details on tutorial results')
		tutoText += generate_image_table_header()
		for (cName,iTag,iSize,iDate) in deployedContainerImages:
			tutoText += generate_image_table_row(cName, iTag, 'N/A', iDate, iSize)
		tutoText += generate_image_table_footer()
		tutoText += generate_command_table_header()
		for (cmd,cmdStatus) in listOfCmds:
			tutoText += generate_command_table_row(cmd, cmdStatus)
		tutoText += generate_command_table_footer()
		tutoText += re.sub('Command', 'Shutdown procedure', generate_command_table_header())
		for (containerName, byeMessage, byeStatus) in byeMessages:
			tutoText += generate_command_table_row(byeMessage, byeStatus)
		tutoText += generate_command_table_footer()
		tutoText += generate_button_footer()
		return tutoText

def _parse_args() -> argparse.Namespace:
	"""Parse the command line args

	Returns:
		argparse.Namespace: the created parser
	"""
	example_text = '''example:
		./ci-scripts/checkTutorialHtmlReport.py --help
		./ci-scripts/checkTutorialHtmlReport.py --job_name NameOfPipeline --job_id BuildNumber --job_url BuildURL'''

	parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Tutorial Check HTML report',
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
