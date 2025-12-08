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

import shutil
import time
import re

from common import *
from docker_api import DockerApi
from vars import *

DOCKER_COMPOSE_TEMPLATE = "template/docker-compose-all-nfs.yaml"
CONF_TEMPLATE = "template/template_config.yaml"
POLICY_PATH = "template/policies"
MYSQL_PATH = "template/mysql"
MYSQL_DB_PATH = "template/oai_db2.sql"
TRACE_DUMMY_CONTAINER_NAME = "trace_dummy"
TEST_NETWORK_NAME = "demo-oai-test"
TEST_NETWORK_NAME_N3 = "demo-n3-test"
TEST_NETWORK_NAME_N6 = "demo-n6-test"

TRACE_FILTER_SIGNALING = f"sctp or port 80 or port 8080 or port 8805 or icmp or port 3306"
TRACE_FILTER_UP = ""


class CNTestLib:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.docker_api = DockerApi()
        self.running_iperf_servers = {}
        self.running_iperf_clients = {}
        self.last_iperf_result = {}

        self.conf_path = ""
        self.docker_compose_path = ""
        self.running_traces = {}
        self.list_of_containers = []
        prepare_folders()

    def prepare_scenario(self, list_of_containers, tc_name):
        """
        Prepares scenario by copying template config and docker-compose to the test-case specific directory
        :param list_of_containers: list of containers from docker-compose to use
        :param tc_name: name of the test case
        :return:
        """
        self.docker_compose_path = os.path.join(get_out_dir(), f"docker-compose-{tc_name}.yaml")
        self.conf_path = os.path.join(get_out_dir(), f"conf-{tc_name}.yaml")
        shutil.copy(os.path.join(DIR_PATH, CONF_TEMPLATE), self.conf_path)
        self.list_of_containers = list_of_containers
        if "oai-pcf" in list_of_containers:
            shutil.copytree(os.path.join(DIR_PATH, POLICY_PATH), os.path.join(get_out_dir(), "policies"),
                            dirs_exist_ok=True)
        if "mysql" in list_of_containers:
            shutil.copytree(os.path.join(DIR_PATH, MYSQL_PATH), os.path.join(get_out_dir(), "mysql"),
                            dirs_exist_ok=True)

        list_of_containers.append(TRACE_DUMMY_CONTAINER_NAME)
        # here we remove the unused NFs
        with open(os.path.join(DIR_PATH, DOCKER_COMPOSE_TEMPLATE)) as f:
            parsed = yaml.safe_load(f)
            for service in parsed["services"].copy():
                if service not in list_of_containers:
                    parsed["services"].pop(service, None)
                    continue
                # replace with used config file
                nf = parsed["services"][service]
                if nf.get("volumes"):
                    for i, volume in enumerate(nf["volumes"]):
                        nf["volumes"][i] = volume.replace("REPLACE", self.conf_path)
                # the only dependency we have to add is to oai-nrf for stability reasons
                if "oai-nrf" in list_of_containers and service != "oai-nrf":
                    if nf.get("depends_on") and "oai-nrf" not in nf["depends_on"]:
                        nf["depends_on"].append("oai-nrf")
                    else:
                        nf["depends_on"] = ["oai-nrf"]

                if "vpp-upf" in list_of_containers and service == "oai-smf":
                    extra_host_entry = "vpp-upf.node.5gcn.mnc95.mcc208.3gppnetwork.org:192.168.79.201"
                    if 'extra_hosts' in nf:
                        if extra_host_entry not in nf['extra_hosts']:
                            nf['extra_hosts'].append(extra_host_entry)
                    else:
                        nf['extra_hosts'] = [extra_host_entry]
                if "vpp-upf" in list_of_containers and service == "oai-ext-dn":
                    entry_point = '/bin/bash -c \"iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE;"\"ip route add 12.1.1.0/24 via 192.168.81.201 dev eth0; ip route; sleep infinity"'
                    nf['entrypoint'] = entry_point
                    if 'networks' in nf:
                        nf['networks'] = {'n6_test_net': {'ipv4_address': '192.168.81.141'}}
                if get_image_tag(service):
                    nf["image"] = get_image_tag(service)

            with open(self.docker_compose_path, "w") as out_file:
                yaml.dump(parsed, out_file)
        logging.info(f"Successfully prepared scenario for TC {tc_name}")

    def add_dependency(self, container, depends_on):
        parsed = None
        with open(self.docker_compose_path, "r") as f:
            parsed = yaml.safe_load(f)
            for service in parsed["services"].copy():
                if service != container:
                    continue
                nf = parsed["services"][service]
                if nf.get("depends_on") and depends_on not in nf["depends_on"]:
                    nf["depends_on"].append(depends_on)
                else:
                    nf["depends_on"] = [depends_on]
        if parsed:
            with open(self.docker_compose_path, "w") as f:
                yaml.dump(parsed, f)

    def replace_in_config(self, path, value):
        """
        Sets and replaces YAML values in config. The path only takes keys.
        If you need to replace structures or lists, please use dicts or lists.
        :param path: path of YAML config file, e.g. smf, smf_info, sNssaiSmfInfoList
        :param value: value to set/replace, YAML anchors are not supported
        :return:
        """
        replace_in_config_generic(path, value, self.conf_path)

    def check_cn_health_status(self):
        all_services = get_docker_compose_services(self.docker_compose_path)
        all_services.remove(TRACE_DUMMY_CONTAINER_NAME)
        self.docker_api.check_health_status(all_services)

    def collect_all_logs(self, folder=None):
        all_services = get_docker_compose_services(self.docker_compose_path)
        log_dir = get_log_dir()
        if folder:
            log_dir = os.path.join(log_dir, folder)
        cn_log_list = self.docker_api.store_all_logs(log_dir, all_services)
        for filename in cn_log_list:
            if re.search('mysql', filename) is not None or re.search('oai-ext-dn', filename) is not None or re.search('trace_dummy', filename) is not None or re.search('vpp-upf', filename) is not None:
                continue
            name_split = filename.split('logs/')
            bye_message_present = False
            with open(filename, 'r') as f:
                for line in f:
                    if "Bye." in line:
                        bye_message_present = True
                        temp_line = line.split(" ")
                        duration = [temp_line[i+1] for i in range(0,len(temp_line)) if "took" in temp_line[i]][0]
                        logging.info(f'{name_split[1]} container properly shutdown in {duration} ms.')
            if not bye_message_present:
                logging.error(f'{name_split[1]} container did NOT properly shutdown.')

    def configure_default_qos(self, five_qi=9, session_ambr=50):
        print("TODO implement me")

    def add_qos_flow_on_pcf(self, five_qi, match, gfbr=10, mfbr=11):
        print("TODO implement me")
        # the plan is to write the yaml files here and if necessary restart PCF

    def start_iperf3_server(self, container, port=39265, bind_ip=""):
        cmd = f"iperf3 -s -i 2 -p {port}"
        if bind_ip:
            cmd += f" -B {bind_ip}"

        logging.info(f"Starting iperf3 Server: {cmd}")
        proc_id = self.docker_api.exec_on_container_background(container, cmd)
        self.running_iperf_servers[f"{container}-{port}"] = proc_id
        # wait until server is ready
        time.sleep(1)

    def stop_iperf3_server(self, container, port=39265):
        proc_id = self.running_iperf_servers[f"{container}-{port}"]
        self.docker_api.stop_background_process(proc_id)

    def start_iperf3_client(self, container, bind_ip, server, port=39265, bandwidth="", duration=20):
        cmd = f"iperf3 -t {duration} -i 2 -c {server} -p {port}"
        if bind_ip:
            cmd += f" -B {bind_ip}"
        if bandwidth:
            b = int(bandwidth) * 1024 * 1024
            cmd += f" -b {b}"
        print(f"Starting iperf3 Test: {cmd}")
        proc_id = self.docker_api.exec_on_container_background(container, cmd)
        self.running_iperf_clients[container] = proc_id

    def iperf3_is_finished(self, container):
        proc_id = self.running_iperf_clients[container]
        self.docker_api.is_process_finished(proc_id)
        self.last_iperf_result[container] = self.docker_api.get_process_result(proc_id)

    def iperf3_results_should_be(self, container, bandwidth, interval=0.1):
        res = self.last_iperf_result[container]
        bandwidth = float(bandwidth)
        interval = float(interval)

        last_line = res.split("\n")[-4]
        bandwidth_receiver = float(last_line.split()[6])
        unit = last_line.split()[7]

        if "Gbit" in unit:
            bandwidth_receiver = bandwidth_receiver * 1024

        min_b = bandwidth - (bandwidth * interval)
        max_b = bandwidth + (bandwidth * interval)

        print(res)

        if bandwidth_receiver < min_b or bandwidth_receiver > max_b:
            raise Exception(f"Bandwidth should be in interval [{min_b}, {max_b}], but it is {bandwidth_receiver}")
        
    def get_iperf3_results(self, container):
        return self.last_iperf_result[container]
    
    def start_cn(self):
        print("Starting Core Network ....")
        start_docker_compose(self.docker_compose_path)

    def stop_cn(self):
        stop_docker_compose(self.docker_compose_path)

    def down_cn(self):
        down_docker_compose(self.docker_compose_path)

    def start_trace(self, name, signaling_only=True, single_interface=True):
        if signaling_only:
            trace_filter = TRACE_FILTER_SIGNALING
        else:
            trace_filter = TRACE_FILTER_UP
        # first, create docker network
        start_docker_compose(self.docker_compose_path, TRACE_DUMMY_CONTAINER_NAME)
        if self.running_traces.get(name):
            self.stop_trace(name)
            raise Exception("There is already a trace running!")
        trace_path = os.path.join(get_out_dir(), f"{name}.pcapng")
        cmd = ["tshark", "-i"]
        if single_interface:
            cmd += [TEST_NETWORK_NAME]
        else:
            # TODO it should be this, we have to take any because of eBPF mode
            # cmd += ["-i", TEST_NETWORK_NAME, "-i", TEST_NETWORK_NAME_N3, "-i", TEST_NETWORK_NAME_N6]
            cmd += ["any"]
        cmd += ["-f", trace_filter, "-w", trace_path]
        self.running_traces[name] = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                                     stderr=subprocess.DEVNULL)
        logging.info(f"Start trace on interface {TEST_NETWORK_NAME} at path {trace_path}")

    def stop_trace(self, name):
        if not self.running_traces.get(name):
            logging.info("There is no running trace")
            return
        self.running_traces[name].terminate()
        del self.running_traces[name]
        logging.info(f"Trace {name} is stopped")

    def create_cn_documentation(self):
        docu = " = Core Network Images = \n"
        docu += create_image_info_header()
        for container in self.list_of_containers:
            if not get_image_tag(container):
                continue
            size, date = self.docker_api.get_image_info(get_image_tag(container))
            docu += create_image_info_line(container, get_image_tag(container), date, size)
        return docu

    def log_should_contain(self, container, match):
        log = self.docker_api.get_log(container)
        if match not in log:
            raise Exception(f"Expected string {match} was not found in log of {container}")

    def get_log(self, container):
        self.docker_api.get_log(container)

    def __del__(self):
        logging.info("Stopping CNTestLib. Stop all traces")
        for key in self.running_traces.copy():
            self.stop_trace(key)
