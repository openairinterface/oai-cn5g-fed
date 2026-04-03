# SPDX-License-Identifier: LicenseRef-CSSL-1.0

import shutil
import os
import ipaddress
import yaml
from common import *
from docker_api import DockerApi
from copy import deepcopy

# Initial IP Addresses and Paths
MOBSIM_GNB_FIRST_IP = "192.168.79.150"
MOBSIM_GNB_N3_FIRST_IP = "192.168.80.150"
MOBSIM_GNB_RADIO_FIRST_IP = "192.168.15.10"
MOBSIM_UE_RADIO_FIRST_IP = "192.168.15.3"
MOBSIM_UE_FIRST_DNS = "192.168.78.20"
ENG_IP = "192.168.79.240"
ENG_RADIO_IP = "192.168.15.2"
MOBSIM_TEMPLATE = "template/docker-compose-mobsim.yaml"
MOBSIM_NR_UE_CONFIG_TEMPLATE = "template/mobsim-ue.yaml"
MOBSIM_GNB_CONFIG_TEMPLATE = "template/mobsim-gnb.yaml"
MOBSIM_ENG_CONFIG_TEMPLATE = "template/mobsim-eng.yaml"

class MobSimTestLib:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.docker_api = DockerApi()
        self.mobsim_gnb = []
        self.mobsim_nr_ue = []
        self.mobsim_eng = None
        self.start_imsi = 208950000000031
        self.docker_compose_path = "" 
        self.eng_config_path = ""
        prepare_folders()

    def __generate_ip(self, first_ip, count):
        ip = ipaddress.ip_address(first_ip) + count
        return str(ip)

    def __generate_mobsim_gnb_name(self):
        return f"mobsim-gnb-208-95-{len(self.mobsim_gnb) + 1}"
    
    def __generate_mobsim_nr_ue_name(self):
        return f"mobsim-nr-ue-{len(self.mobsim_nr_ue) + 1}"
    
    def __generate_mobsim_eng_name(self):
        return "mobsim-eng"
    
    def __generate_mobsim_nr_ue_imsi(self):
        return str(self.start_imsi + len(self.mobsim_nr_ue))

    def __get_docker_compose_path(self, name):
        return os.path.join(get_out_dir(), f"docker-compose-{name}.yaml")

    def __generate_config_file(self, template_path, output_path):
        """Copy and modify the config file from template."""
        template_path = os.path.join(DIR_PATH, template_path)
        shutil.copy(template_path, output_path)
    
    def __update_config_file(self,config_path, update_dict):
        """
        Update a YAML configuration file with specified key-value pairs.
        
        :param config_path: Path to the configuration file.
        :param update_dict: Dictionary with keys as configuration fields and values as the updates.
        """
        with open(config_path, 'r') as file:
            config_data = yaml.safe_load(file)
        
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in config_data:
                config_data[key].update(value)
            else:
                config_data[key] = value
                
        with open(config_path, 'w') as file:
            yaml.dump(config_data, file)

    def prepare_mobsim(self, num_gnb, num_nr_ue):
        output_path = self.__get_docker_compose_path("mobsim")

        with open(os.path.join(DIR_PATH, MOBSIM_TEMPLATE)) as f:
            parsed = yaml.safe_load(f)
            gnb_template = parsed["services"]["gnb"]
            nr_ue_template = parsed["services"]["ue"]
            eng_template = parsed["services"]["eng"]
            eng_name = self.__generate_mobsim_eng_name()
            eng_service = deepcopy(eng_template)
            eng_service["container_name"] = eng_service["container_name"].replace("REPLACE_NAME", eng_name)
            eng_service["networks"]["default"]["ipv4_address"] = eng_service["networks"]["default"]["ipv4_address"].replace("REPLACE_IP", ENG_IP)
            eng_service["networks"]["radio"]["ipv4_address"] = eng_service["networks"]["radio"]["ipv4_address"].replace("REPLACE_IP", ENG_RADIO_IP)
            eng_config_path = os.path.join(get_out_dir(), 'mobsim-eng.conf')
            self.__generate_config_file(MOBSIM_ENG_CONFIG_TEMPLATE, eng_config_path)
            self.eng_config_path = eng_config_path
            eng_service["volumes"][0] = eng_service["volumes"][0].replace("REPLACE_CONFIG", eng_config_path)

            parsed["services"][eng_name] = eng_service
            self.mobsim_eng = eng_name

            nci = 0x000000010
            gnb_list = []
            gnb_radio_ip_list = []
            for i in range(num_gnb):
                gnb_name = self.__generate_mobsim_gnb_name()
                gnb_ip = self.__generate_ip(MOBSIM_GNB_FIRST_IP, i)
                gnb_n3_ip = self.__generate_ip(MOBSIM_GNB_N3_FIRST_IP, i)
                gnb_radio_ip = self.__generate_ip(MOBSIM_GNB_RADIO_FIRST_IP, i)
                gnb_radio_ip_list.append(gnb_radio_ip)
                gnb_service = deepcopy(gnb_template)
                gnb_service["container_name"] = gnb_service["container_name"].replace("REPLACE_NAME", gnb_name)
                gnb_service["networks"]["default"]["ipv4_address"] = gnb_service["networks"]["default"]["ipv4_address"].replace("REPLACE_IP", gnb_ip)
                gnb_service["networks"]["access"]["ipv4_address"] = gnb_service["networks"]["access"]["ipv4_address"].replace("REPLACE_IP", gnb_n3_ip)
                gnb_service["networks"]["radio"]["ipv4_address"] = gnb_service["networks"]["radio"]["ipv4_address"].replace("REPLACE_IP", gnb_radio_ip)
                gnb_config_path = os.path.join(get_out_dir(), f'mobsim-gnb-{i + 1}.conf')
                self.__generate_config_file(MOBSIM_GNB_CONFIG_TEMPLATE, gnb_config_path)
                gnb_service['volumes'][0] = gnb_service['volumes'][0].replace("REPLACE_CONFIG", gnb_config_path)
                parsed["services"][gnb_name] = gnb_service
                self.mobsim_gnb.append(gnb_name)

                
                gnb_update_dict = {
                    "nci": str(nci),
                    "linkIp": gnb_radio_ip,
                    "ngapIp": gnb_ip,
                    "gtpIp": gnb_n3_ip
                }
                nci = nci + 0x000000010
                self.__update_config_file(gnb_config_path, gnb_update_dict)

                # Update ENG configuration with gNB info
                gnb_list.append({
                    "gnbIP": gnb_radio_ip,
                    "gnbPort": 6969,
                    "name": gnb_name,
                })

            self.__update_config_file(eng_config_path, {"gnbList": gnb_list})

            # Add NR-UE containers
            ue_list = []
            for j in range(num_nr_ue):
                nr_ue_name = self.__generate_mobsim_nr_ue_name()
                nr_ue_ip = self.__generate_ip(MOBSIM_UE_RADIO_FIRST_IP, j)
                nr_ue_imsi = self.__generate_mobsim_nr_ue_imsi()
                nr_ue_service = deepcopy(nr_ue_template)
                nr_ue_service["container_name"] = nr_ue_service["container_name"].replace("REPLACE_NAME", nr_ue_name)
                nr_ue_service["networks"]["radio"]["ipv4_address"] = nr_ue_service["networks"]["radio"]["ipv4_address"].replace("REPLACE_IP", nr_ue_ip)

                nr_ue_config_path = os.path.join(get_out_dir(), f'mobsim-nr-ue-{j + 1}.conf')
                self.__generate_config_file(MOBSIM_NR_UE_CONFIG_TEMPLATE, nr_ue_config_path)
                nr_ue_service['volumes'][0] = nr_ue_service['volumes'][0].replace("REPLACE_CONFIG", nr_ue_config_path)
                nr_ue_service['dns'][0] = nr_ue_service['dns'][0].replace("REPLACE_DNS", MOBSIM_UE_FIRST_DNS)
                parsed["services"][nr_ue_name] = nr_ue_service
                self.mobsim_nr_ue.append(nr_ue_name)
                ue_update_dict = {
                    "supi": f"imsi-{nr_ue_imsi}",
                    "gnbSearchList": gnb_radio_ip_list
                }
                self.__update_config_file(nr_ue_config_path, ue_update_dict)

                # Update ueList in eng.conf
                ue_list.append({
                    "gnbPort": 5959,
                    "name": f"imsi-{nr_ue_imsi}",
                    "ueIP": nr_ue_ip
                })

            # Write the updated ueList to eng.conf
            self.__update_config_file(eng_config_path, {"ueList": ue_list})

            # Remove placeholders from parsed data
            parsed["services"].pop("gnb", None)
            parsed["services"].pop("ue", None)
            parsed["services"].pop("eng", None)

            # Write final Docker Compose configuration
            with open(output_path, "w") as out_file:
                yaml.dump(parsed, out_file)

        self.docker_compose_path = output_path

        return self.mobsim_eng, self.mobsim_gnb, self.mobsim_nr_ue
    
    def update_event_rate(self,rate):
        update_dict = {
            "eventRate": rate
        }
        self.__update_config_file(self.eng_config_path, update_dict)
    
    def start_mobsim_eng(self):
        start_docker_compose(self.docker_compose_path, self.mobsim_eng)
    
    def start_mobsim_gnb(self):
        start_docker_compose(self.docker_compose_path, self.mobsim_gnb)
    
    def start_mobsim_nr_ues(self):
        start_docker_compose(self.docker_compose_path, self.mobsim_nr_ue)
    
    def stop_mobsim_eng(self):
        stop_docker_compose(self.docker_compose_path, self.mobsim_eng)
        
    def start_mobsim(self):
        start_docker_compose(self.docker_compose_path)
        
    def stop_mobsim(self):
        stop_docker_compose(self.docker_compose_path)
    def down_mobsim(self):
        down_docker_compose(self.docker_compose_path)
        
    def create_mobsim_docu(self):
        if len(self.mobsim_gnb + self.mobsim_nr_ue) == 0:
            return ""
        docu = " = Mobsim Tester Image = \n"
        docu += create_image_info_header()
        size, date = self.docker_api.get_image_info(get_image_tag("mobsim"))
        docu += create_image_info_line("mobsim", get_image_tag("mobsim"), date, size)
        return docu

    def collect_all_mobsim_logs(self):
        self.docker_api.store_all_logs(get_log_dir(), self.mobsim_gnb + self.mobsim_nr_ue + ["mobsim-eng"])