# SPDX-License-Identifier: LicenseRef-CSSL-1.0

import logging
import os
import subprocess
import sys

import robot.libraries.BuiltIn
import yaml
from robot.libraries.BuiltIn import BuiltIn

from image_tags import image_tags

GENERATED_DIR = "archives/robot_framework"
GENERATED_DIR_NGAP = "archives_ngap/framework"

logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="[%(asctime)s] %(levelname)8s: %(message)s"
)

DIR_PATH = os.path.split(os.path.abspath(__file__))[0]


def get_out_dir():
    try:
        suite_name = BuiltIn().get_variable_value("${SUITE_NAME}")
    except robot.libraries.BuiltIn.RobotNotRunningError:
        suite_name = "local"
    dir_to_use = GENERATED_DIR
    if "ngap tester" in suite_name.lower():
        dir_to_use = GENERATED_DIR_NGAP
    out_path = os.path.join(os.getcwd(), dir_to_use)
    return os.path.join(out_path, suite_name)


def get_log_dir():
    return os.path.join(get_out_dir(), "logs")


# import common ci scripts
# sys.path.append(os.path.join(DIR_PATH, "../ci-scripts/common/python"))
# from cls_cmd import LocalCmd
#
# cmd = LocalCmd()


def prepare_folders():
    os.makedirs(get_out_dir(), exist_ok=True)


def replace_in_config_generic(path, value, file_path):
    """
    Sets and replaces YAML values in config. The path only takes keys.
    If you need to replace structures or lists, please use dicts or lists.
    :param path: path of YAML config file, e.g. smf, smf_info, sNssaiSmfInfoList
    :param value: value to set/replace, YAML anchors are not supported
    :return:
    """
    with open(file_path) as f:
        parsed = yaml.safe_load(f)
        next_elem = parsed
        for i, key in enumerate(path):
            if i == len(path) - 1:
                next_elem[key] = value
            else:
                next_elem = next_elem[key]
        with (open(file_path, "w")) as out_file:
            yaml.dump(parsed, out_file)
    logging.info(f"Successfully set config value {value} in path {path}")

def __docker_subprocess(args):
    try:
        res = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, timeout=60)
        logging.info(res.stdout.decode("utf-8").strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(e.stdout.decode("utf-8").strip())
        raise e


def start_docker_compose(path, container=None):
    logging.info(f"Docker-compose file: {path}")
    if container:
        __docker_subprocess(["docker-compose", "-f", path, "up", "-d", container])
    else:
        __docker_subprocess(["docker-compose", "-f", path, "up", "-d"])


def stop_docker_compose(path):
    __docker_subprocess(["docker-compose", "-f", path, "stop", "-t", "30"])


def down_docker_compose(path):
    __docker_subprocess(["docker-compose", "-f", path, "down", "-t", "30", "-v"])


def get_docker_compose_services(docker_compose_file):
    all_services = []
    with open(docker_compose_file) as f:
        parsed = yaml.safe_load(f)
        for service in parsed["services"]:
            all_services.append(service)

    return all_services


def create_image_info_header():
    return "| =Container Name= | =Used Image= | =Date= | =Size= | \n"


def create_image_info_line(container, image, date, size):
    return f"| {container} | {image} | {date} | {size} | \n"


def get_image_tag(container_name):
    tag = image_tags.get(container_name, "")
    if tag:
        return tag
    # to allow oai-upf, oai-upf-ebpf, oai-upf-2, etc to be interpreted as oai-upf
    idx = container_name.rfind("-")
    container_name = container_name[:idx]

    return image_tags.get(container_name, "")
