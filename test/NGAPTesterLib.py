# SPDX-License-Identifier: LicenseRef-CSSL-1.0

import re
import shutil

from common import *
from docker_api import DockerApi

NGAP_TESTER_TEMPLATE_DOCKER_COMPOSE = "template/docker-compose-ngap-tester.yaml"
NGAP_TESTER_TEMPLATE_CONFIG = "template/ngap_tester_template_config.yaml"


class NGAPTesterLib:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.docker_api = DockerApi()
        self.docker_compose_path = ""
        self.conf_path = ""
        self.name = ""
        self.tc_name = ""

    def prepare_ngap_tester(self, tc_name, mt_profile="default", single_interface=True):
        self.tc_name = tc_name
        self.name = f"ngap-tester-{tc_name}-{mt_profile}"
        self.docker_compose_path = os.path.join(get_out_dir(),
                                                f"docker-compose-ngap-tester-{tc_name}-{mt_profile}.yaml")
        self.conf_path = os.path.join(get_out_dir(),
                                      "ngap_tester_config.yaml")  # we only have one config for all the tests
        shutil.copy(os.path.join(DIR_PATH, NGAP_TESTER_TEMPLATE_CONFIG), self.conf_path)

        with open(os.path.join(DIR_PATH, NGAP_TESTER_TEMPLATE_DOCKER_COMPOSE)) as f:
            parsed = yaml.safe_load(f)
            for service in parsed["services"].copy():
                container_service = parsed["services"].pop(service)
                service_name = service
                if single_interface:
                    container_service["networks"].pop("n3_test_net", None)
                    container_service["networks"].pop("n6_test_net", None)
                if service == "REPLACE_SERVICE":
                    service_name = self.name
                container_service["command"] = container_service["command"].replace("REPLACE_TEST", tc_name)
                container_service["command"] = container_service["command"].replace("REPLACE_MT_PROFILE", mt_profile)
                container_service["container_name"] = service_name
                container_service["image"] = image_tags.get("ngap-tester")
                parsed["services"][service_name] = container_service

            with (open(self.docker_compose_path, "w")) as out_file:
                yaml.dump(parsed, out_file)
            return self.name

    def check_ngap_tester_done(self):
        self.docker_api.check_container_stopped(self.name)

    def replace_in_ngap_tester_config(self, path, value):
        """
        Sets and replaces YAML values in config. The path only takes keys.
        If you need to replace structures or lists, please use dicts or lists.
        :param path: path of YAML config file
        :param value: value to set/replace, YAML anchors are not supported
        :return:
        """
        replace_in_config_generic(path, value, self.conf_path)

    # def set_routing_for_multiple_interfaces(self, ):

    def __read_ngap_tester_results(self):
        log = self.docker_api.get_log(self.name)
        test_ended = False
        test_passed = False
        description = ""
        for line in log.splitlines():
            result = re.search('Scenario *: Status *: Description', line)
            if result is not None:
                test_ended = True
            result = re.search(f'{self.tc_name} *: (?P<status>[A-Z]+) *: (?P<description>.*$)', line)
            if result is not None and test_ended:
                if result.group('status') == 'PASSED':
                    test_passed = True
                description = result.group('description')
                description = re.sub('NOT YET VALIDATED - ', '', description)
        return test_ended, test_passed, description

    def get_ngap_tester_description(self):
        self.check_ngap_tester_done()
        res = self.__read_ngap_tester_results()
        if res[0]:
            return res[2]
        else:
            return "There was an issue in starting the test. Please see the logs"

    def check_ngap_tester_result(self):
        self.check_ngap_tester_done()
        res = self.__read_ngap_tester_results()
        if not res[1]:
            raise Exception("NGAP Tester Test did not pass")

    def start_ngap_tester(self):
        # starts trafficgen and ngap tester
        start_docker_compose(self.docker_compose_path)

    def stop_ngap_tester(self):
        stop_docker_compose(self.docker_compose_path)

    def down_ngap_tester(self):
        down_docker_compose(self.docker_compose_path)

    def collect_all_ngap_tester_logs(self):
        all_services = get_docker_compose_services(self.docker_compose_path)
        self.docker_api.store_all_logs(get_log_dir(), all_services)

    def create_ngap_tester_docu(self):
        if not self.name:
            return ""
        docu = " = NGAP Tester Image = \n"
        docu += create_image_info_header()
        size, date = self.docker_api.get_image_info(get_image_tag("ngap-tester"))
        docu += create_image_info_line("ngap-tester",get_image_tag("ngap-tester"), date, size)
        return docu


if __name__ == "__main__":
    test = NGAPTesterLib()
    prepare_folders()
    test.prepare_ngap_tester("test", single_interface=False)
