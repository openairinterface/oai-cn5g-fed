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

oc_registry_url = 'https://default-route-openshift-image-registry.apps.oai.cs.eurecom.fr'

def _parse_args() -> argparse.Namespace:
    """Parse the command line args

    Returns:
        argparse.Namespace: the created parser
    """
    example_text = '''example:
        ./ci-scripts/checkOcRegistry.py --help
        ./ci-scripts/checkOcRegistry.py --image-name iName --tag tName'''

    parser = argparse.ArgumentParser(description='OAI 5G CORE NETWORK Utility tool',
                                    epilog=example_text,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # Container Name
    parser.add_argument(
        '--image-name', '-in',
        action='store',
        required=True,
        help='Image Name to check',
    )

    # Tag
    parser.add_argument(
        '--tag', '-t',
        action='store',
        required=True,
        help='Image Tag to check',
    )

    # OC project
    parser.add_argument(
        '--project', '-p',
        action='store',
        required=True,
        help='Openshift project',
    )

    # OC username
    parser.add_argument(
        '--username', '-u',
        action='store',
        required=True,
        help='Openshift Account',
    )
    return parser.parse_args()

def checkImageInfo(imageName, imageTag):
    myCmds = cls_cmd.LocalCmd()
    ret = myCmds.run(f'oc describe istag {imageName}:{imageTag}', silent=True)
    if ret.returncode != 0:
        logging.error(f'Image Tag {imageName}:{imageTag} not present in OC registry')
        myCmds.close()
        return -1
    myCmds.run(f'echo "Tested Tag is {imageName}:{imageTag}" > archives/{imageName}-image-info.log')
    myCmds.run(f'oc describe istag {imageName}:{imageTag} | grep "Image Size:" >> archives/{imageName}-image-info.log')
    ret = myCmds.run(f'oc describe istag {imageName}:{imageTag} | grep --color=never "Image Name:" | sed -e "s#Image Name:.*sha256#{imageName}@sha256#"', silent=True)
    myCmds.run(f'oc get -o json isimage {ret.stdout} | jq .image.dockerImageMetadata.Created >> archives/{imageName}-image-info.log')
    myCmds.run(f'echo "OC Pushed Tag is {imageName}:{imageTag}" >> archives/{imageName}-image-info.log')
    myCmds.close()
    return 0

def pushToOcProjectRegistry(imageName, imageTag, ocProject, ocUser):
    myCmds = cls_cmd.LocalCmd()
    myCmds.run(f'oc whoami -t | sudo podman login -u {ocUser} --password-stdin {oc_registry_url} --tls-verify=false')
    noHttpsURL = re.sub("https://", "", oc_registry_url)
    logging.debug(f'noHttpsURL is {noHttpsURL}')
    myCmds.run(f'sudo podman rmi {noHttpsURL}/{ocProject}/{imageName}:{imageTag} || true')
    myCmds.run(f'sudo podman image tag {imageName}:{imageTag} {noHttpsURL}/{ocProject}/{imageName}:{imageTag}')
    cnt = 0
    while (cnt < 4):
        cnt += 1
        ret = myCmds.run(f'sudo podman push --tls-verify=false {noHttpsURL}/{ocProject}/{imageName}:{imageTag}')
        if ret.returncode == 0:
            cnt = 10
    myCmds.run(f'sudo podman rmi {noHttpsURL}/{ocProject}/{imageName}:{imageTag} || true')
    myCmds.run(f'sudo podman logout {oc_registry_url}')
    myCmds.close()
    if cnt == 10:
        return 0
    else:
        return -1

if __name__ == '__main__':
    # Parse the arguments
    args = _parse_args()

    firstStatus = checkImageInfo(args.image_name, args.tag)
    # If image is already on the OC registry, we are done
    if firstStatus == 0:
        sys.exit(0)

    pushStatus = pushToOcProjectRegistry(args.image_name, args.tag, args.project, args.username)
    if pushStatus == -1:
        sys.exit(-1)

    checkImageInfo(args.image_name, args.tag)
    sys.exit(0)
