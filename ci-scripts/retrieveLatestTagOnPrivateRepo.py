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
from datetime import datetime
import logging
import re
import sys
import json
import common.python.cls_cmd as cls_cmd

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[%(asctime)s] %(levelname)8s: %(message)s"
)

PRIVATE_LOCAL_REGISTRY_URL='https://selfix.sboai.cs.eurecom.fr:443'

def main() -> None:
    args = _parse_args()
    if args.repo_name == '5gc-gnbsim':
        tagRoot = 'main'
        nbChars = 11
    if args.repo_name == 'oai-upf-vpp': # UPF-VPP is not maintained and we are not buidling multi-architecture image for it
        print("develop-863d2bf7") # The last develop commit on UPF-VPP
        sys.exit(0)
    else:
        tagRoot = 'develop'
        nbChars = 15

    myCmds = cls_cmd.LocalCmd()
    cmd = f'curl --insecure -Ss -u oaicicd:oaicicd {PRIVATE_LOCAL_REGISTRY_URL}/v2/{args.repo_name}/tags/list | jq .'
    tagList = myCmds.run(cmd, silent=True)
    latestTag = ''
    latestDate = datetime.strptime('2022-01-01T00:00:00', '%Y-%m-%dT%H:%M:%S')
    for line in tagList.stdout.split('\n'):
        res = re.search(f'"(?P<tag>{tagRoot}-[0-9a-zA-Z]+)"', line)
        if res is not None:
            tag = res.group('tag')
            # on SPGWU / GitHub     `git log -1 --pretty=format:"%h"` returns 7 characters
            # on other NF / GitLab  `git log -1 --pretty=format:"%h"` returns 8 characters
            if len(tag) == nbChars or len(tag) == (nbChars+1):
                cmd = f'curl --insecure -Ss -u oaicicd:oaicicd {PRIVATE_LOCAL_REGISTRY_URL}/v2/{args.repo_name}/manifests/{tag} | jq .history'
                tagInfo = myCmds.run(cmd, silent=True)
                # Fetch manifest (for multi-arch)
                manifest_cmd = (
                    f'curl --insecure -Ss -u oaicicd:oaicicd '
                    f'-H "Accept: application/vnd.oci.image.index.v1+json,application/vnd.oci.image.manifest.v1+json" '
                    f'{PRIVATE_LOCAL_REGISTRY_URL}/v2/{args.repo_name}/manifests/{tag}'
                )
                manifest_result = myCmds.run(manifest_cmd, silent=True)
                manifest_json = json.loads(manifest_result.stdout)

                # Default to single-arch manifest
                final_manifest_json = manifest_json

                # If multi-arch, pick amd64 platform
                if manifest_json.get('manifests'): # Check if this is a multi-arch (OCI index) manifest.
                    # select the manifest for amd64 platform with the standard OCI media type
                    amd64_manifest = next(
                        (
                            m for m in manifest_json.get('manifests', []) # Look through all manifests in the multi-arch image.
                            if m.get('platform', {}).get('architecture') == 'amd64'
                            # Only include standard single-arch OCI manifests.
                            and m.get('mediaType') == 'application/vnd.oci.image.manifest.v1+json'
                            and not m.get('annotations', {}).get('vnd.docker.reference.type')
                        ),
                        None
                    )

                    if amd64_manifest is None: # If no amd64 manifest is found, skip this tag and continue to the next one.
                        continue

                    amd64_digest = amd64_manifest['digest'] # Extract the digest of the amd64 manifest.
                    # Fetch single-arch manifest for config
                    single_arch_cmd = (
                        f'curl --insecure -Ss -u oaicicd:oaicicd '
                        f'-H "Accept: application/vnd.oci.image.manifest.v1+json" '
                        f'{PRIVATE_LOCAL_REGISTRY_URL}/v2/{args.repo_name}/manifests/{amd64_digest}'
                    )
                    single_arch_result = myCmds.run(single_arch_cmd, silent=True) # Execute the curl command for the amd64 single-arch manifest.
                    final_manifest_json = json.loads(single_arch_result.stdout)


                # Extract config digest
                config_digest = final_manifest_json.get('config', {}).get('digest')
                if not config_digest:
                    continue


                # Fetch config blob and extract creation date
                config_cmd = (
                    f'curl --insecure -Ss -u oaicicd:oaicicd '
                    f'-H "Accept: application/vnd.oci.image.config.v1+json" '
                    f'{PRIVATE_LOCAL_REGISTRY_URL}/v2/{args.repo_name}/blobs/{config_digest}'
                )
                config_result = myCmds.run(config_cmd, silent=True)
                config_json = json.loads(config_result.stdout)
                created_timestamp = config_json.get('created') # Extract the created timestamp from the config.
                if not created_timestamp:
                    continue
                # Update latest tag if this one is newer
                if created_timestamp:
                    created_datetime = datetime.strptime(created_timestamp[:19], '%Y-%m-%dT%H:%M:%S')  # truncate nanoseconds
                    if created_datetime > latestDate:
                        latestDate = created_datetime
                        latestTag = tag

    #logging.info(f'Latest Tag = {latestTag} made on {latestDate}')
    if latestTag == '':
        sys.exit(-1)
    print(latestTag)
    sys.exit(0)

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    parser = argparse.ArgumentParser(description='Script to retrieve on a given image repository, the latest (newest) develop image.')
    parser.add_argument(
        '--repo-name', '-rn',
        action='store',
        help='Image Repository Name (for example oai-amf)'
    )

    return parser.parse_args()

if __name__ == '__main__':
    main()
