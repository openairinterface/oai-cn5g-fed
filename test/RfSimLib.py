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
import os
import ipaddress
import yaml
from common import *
from docker_api import DockerApi
from copy import deepcopy


RAN_TEMPLATE = "template/docker-compose-rfsim.yaml"
GNB_FIRST_IP = "192.168.79.140"
GNB_N3_FIRST_IP = "192.168.80.140"
NR_UE_FIRST_IP = "192.168.79.150"
NR_UE_CONFIG_TEMPLATE = "../docker-compose/ran-conf/nr-ue.conf"
GNB_CONFIG_TEMPLATE = "../docker-compose/ran-conf/gnb.conf"


class RfSimLib:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.docker_api = DockerApi()
        self.gnb = []
        self.nr_ue = []
        self.start_imsi = 208950000000031
        self.gnb_docker_compose_path = ""
        self.ues_docker_compose_path = ""
        self.gnb_config_path = ""
        self.nr_ue_config_path = ""
        prepare_folders()

    def __generate_ip(self, first_ip, count):
        ip = ipaddress.ip_address(first_ip) + count
        return str(ip)

    def __generate_gnb_name(self):
        return f"gnb-{len(self.gnb) + 1}"
    
    def __generate_nr_ue_name(self):
        return f"nr_ue-{len(self.nr_ue) + 1}"
    
    def __generate_nr_ue_imsi(self):
        return str(self.start_imsi + len(self.nr_ue))

    def __get_docker_compose_path(self, name):
        return os.path.join(get_out_dir(), f"docker-compose-{name}.yaml")
    
    def __navigate_to_key(self,lines, path):
            current_level = 0
            target_level = len(path) - 1
            key_start_indices = []
            found = False

            for i, line in enumerate(lines):
                stripped_line = line.strip()
                if current_level < len(path) and stripped_line.startswith(path[current_level]):
                    key_start_indices.append(i)
                    current_level += 1
                    if current_level > target_level:
                        found = True
                        break

            return key_start_indices
    
    def prepare_ran(self, num_gnb, num_nr_ue):
        """
        Prepares the RAN components by generating the Docker Compose file with multiple gNBs and NR-UEs.
        :param num_gnb: Number of gNB instances to create.
        :param num_nr_ue: Number of NR-UE instances to create.
        :return: Path to the generated Docker Compose file.
        """
        gnb_output_path = self.__get_docker_compose_path("ran_gnb")
        ue_output_path = self.__get_docker_compose_path("ran-ue")
        shutil.copy(os.path.join(DIR_PATH, NR_UE_CONFIG_TEMPLATE), get_out_dir())
        shutil.copy(os.path.join(DIR_PATH, GNB_CONFIG_TEMPLATE), get_out_dir())
        self.nr_ue_config_path = os.path.join(get_out_dir(), 'nr-ue.conf')
        self.gnb_config_path = os.path.join(get_out_dir(), 'gnb.conf')
        with open(os.path.join(DIR_PATH, RAN_TEMPLATE)) as f:
            parsed = yaml.safe_load(f)

            # Template placeholders
            gnb_template = parsed["services"]["oai-gnb"]
            nr_ue_template = parsed["services"]["oai-nr-ue"]

            for i in range(num_gnb):
                gnb_name = self.__generate_gnb_name()
                gnb_ip = self.__generate_ip(GNB_FIRST_IP, i)
                gnb_n3_ip = self.__generate_ip(GNB_N3_FIRST_IP, i)
                gnb_service = gnb_template.copy()
                gnb_service["container_name"] = gnb_name
                gnb_service["networks"]["public_test_net"]["ipv4_address"] = gnb_ip
                gnb_service["networks"]["n3_test_net"]["ipv4_address"] = gnb_n3_ip
                parsed["services"][gnb_name] = gnb_service
                self.gnb.append(gnb_name)
            parsed["services"].pop("oai-gnb", None)
            parsed["services"].pop("oai-nr-ue", None)
            with open(gnb_output_path, "w") as out_file:
                yaml.dump(parsed, out_file)
                
        with open(os.path.join(DIR_PATH, RAN_TEMPLATE)) as f:
            parsed = yaml.safe_load(f) 
            nr_ue_template = parsed["services"]["oai-nr-ue"]
            for j in range(num_nr_ue):
                nr_ue_name = self.__generate_nr_ue_name()
                nr_ue_ip = self.__generate_ip(NR_UE_FIRST_IP, j)
                nr_ue_imsi = self.__generate_nr_ue_imsi()
                nr_ue_service = deepcopy(nr_ue_template)
                nr_ue_service["container_name"] = nr_ue_name
                nr_ue_service["networks"]["public_test_net"]["ipv4_address"] = nr_ue_ip
                nr_ue_service['environment']['USE_ADDITIONAL_OPTIONS'] = nr_ue_service['environment']['USE_ADDITIONAL_OPTIONS'].replace("REPLACE_IMSI", nr_ue_imsi)
                nr_ue_service['environment']['USE_ADDITIONAL_OPTIONS'] = nr_ue_service['environment']['USE_ADDITIONAL_OPTIONS'].replace("REPLACE_IP", gnb_ip)
                parsed["services"][nr_ue_name] = nr_ue_service
                self.nr_ue.append(nr_ue_name)
            parsed["services"].pop("oai-gnb", None)
            parsed["services"].pop("oai-nr-ue", None)
            with open(ue_output_path, "w") as out_file:
                yaml.dump(parsed, out_file)
        self.ues_docker_compose_path = ue_output_path
        self.gnb_docker_compose_path = gnb_output_path
        
        return self.gnb, self.nr_ue
    
    def replace_in_gnb_config(self, path, value, operation='replace'):
        """
        Sets and replaces values in a custom configuration file. The path takes keys.
        Supports replacing, adding, and deleting operations.
        :param path: List of keys representing the path to the desired value.
        :param value: The new value to set (used for replace and add operations).
        :param operation: The operation to perform: 'replace', 'add', or 'delete'.
        :return: None
        """
        with open(self.gnb_config_path, 'r') as f:
            lines = f.readlines()
        lines = [line for line in lines if not line.strip().startswith('#')]
        key_start_indices = self.__navigate_to_key(lines, path)
        if operation == 'replace':
            for i in key_start_indices:
                key, sep, old_value = lines[i].partition('=')
                if key.strip() == path[-1]:
                    indent = ' ' * (len(lines[i]) - len(lines[i].lstrip()))
                    new_line = f"{indent}{key.strip()} = {value};\n"
                    lines[i] = new_line
                    break
        elif operation == 'add':
            if not key_start_indices: 
                new_key = path[0]
                indent = ''
                new_line = f"{indent}{new_key} :{value}\n"
                lines.append(new_line)
            else:
                insertion_point = key_start_indices[-1] + 1
                indent = ' ' * (len(lines[insertion_point-1]) - len(lines[insertion_point-1].lstrip()))
                new_line = f"{indent}{path[-1]} = {value};\n"
                lines.insert(insertion_point, new_line)
        elif operation == 'delete':
            for i in key_start_indices:
                key, sep, old_value = lines[i].partition('=')
                if key.strip() == path[-1]:
                    lines.pop(i)
                    break
        with open(self.gnb_config_path, 'w') as f:
            f.writelines(lines)
        logging.info(f"Successfully performed '{operation}' on config value {value} at path {'.'.join(path)}")

    def check_ran_health_status(self):
        ran_containers = self.gnb + self.nr_ue
        logging.info(ran_containers)
        logging.info(self.docker_api.check_health_status(ran_containers))
        self.docker_api.check_health_status(ran_containers)

    def collect_all_ran_logs(self):
        self.docker_api.store_all_logs(get_log_dir(), self.gnb + self.nr_ue)
        
    def start_gnb(self, gnb_name):
        start_docker_compose(self.gnb_docker_compose_path, container=gnb_name)
    
    def start_all_gnb(self):
        for gnb in self.gnb:
            self.start_gnb(gnb)

    def stop_gnb(self):
        stop_docker_compose(self.gnb_docker_compose_path)

    def down_gnb(self):
        down_docker_compose(self.gnb_docker_compose_path)

    def start_nr_ue(self, nr_ue_name):
        start_docker_compose(self.ues_docker_compose_path, container=nr_ue_name)
        
    def start_all_nr_ue(self):
        start_docker_compose(self.ues_docker_compose_path)
            
    def stop_nr_ue(self):
        stop_docker_compose(self.ues_docker_compose_path)
        
    def down_nr_ue(self):
        down_docker_compose(self.ues_docker_compose_path)
    
    def create_ran_docu(self):
        if len(self.gnb + self.nr_ue) == 0:
            return ""
        docu = " = RAN Tester Image = \n"
        docu += create_image_info_header()
        size, date = self.docker_api.get_image_info(get_image_tag("oai-gnb"))
        docu += create_image_info_line("oai-gnb", get_image_tag("oai-gnb"), date, size)
        size, date = self.docker_api.get_image_info(get_image_tag("oai-nr-ue"))
        docu += create_image_info_line("oai-nr-ue", get_image_tag("oai-nr-ue"), date, size)
        return docu
    
    def get_ue_container_names(self):
        return self.nr_ue
    
    def get_gnb_container_names(self):
        return self.gnb
    
    def get_ue_IP_address(self, container):
        log = self.docker_api.get_log(container)
        for line in log.split("\n"):
            if " IPv4 " in line:
                parts = line.split(",")
                for part in parts:
                    if " IPv4 " in part:
                        ip_part = part.strip().split(" ")
                        ip_address = ip_part[-1].strip()
                        logging.info("PDU session establishment successful")
                        return ip_address
        raise Exception(f"PDU session establishment ongoing for {container}, UE logs format changed ")

    def get_ue_IMSI(self, container):
        log = self.docker_api.get_log(container)
        for line in log.split("\n"):
           if "uicc0.imsi" in line.lower():
              parts = line.split(" ")
              # location of imsi in logs
              loc = [i for i in range(0,len(parts)) if "uicc0.imsi" in parts[i]]
              imsi = parts[loc[0]+1]
              if int(imsi):
                  return str(imsi)
        raise Exception(f"IMSI not found for {container}")

    def get_ue_SUPI(self, container):
        log = self.docker_api.get_log(container)
        for line in log.split("\n"):
           if "uicc0.imsi" in line.lower():
              parts = line.split(" ")
              # location of imsi in logs
              loc = [i for i in range(0,len(parts)) if "uicc0.imsi" in parts[i]]
              imsi = parts[loc[0]+1]
              if int(imsi):
                  return str(imsi)
        raise Exception(f"IMSI not found for {container}")
