# SPDX-License-Identifier: LicenseRef-CSSL-1.0

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

            # trace_dummy is a one-shot container and is excluded from the health check
            speed_up_healthchecks(parsed["services"], skip=(TRACE_DUMMY_CONTAINER_NAME,))

            with open(self.docker_compose_path, "w") as out_file:
                yaml.dump(parsed, out_file)
        logging.info(f"Successfully prepared scenario for TC {tc_name}")

    def add_subscribers_to_database(self, count, start_imsi="208950000000031"):
        """
        Extends the generated MySQL seed so `count` consecutive IMSIs can authenticate.

        The committed oai_db2.sql carries ~100 subscribers, which is enough for the
        functional suites but not for scale runs. Rather than committing thousands of
        rows, the missing AuthenticationSubscription entries are generated into the
        per-scenario copy of the seed. Only that table is needed: the SMF runs with
        use_local_subscription_info, so session data comes from the NF config, and the
        AMF tolerates a missing AccessAndMobilitySubscriptionData row.

        Must be called after Prepare Scenario (which copies the seed) and before Start CN
        (mysql reads it once, on first boot).

        :param count: number of consecutive IMSIs required, starting at start_imsi
        :param start_imsi: first IMSI
        :return: number of rows added
        """
        count = int(count)
        db_path = os.path.join(get_out_dir(), "mysql", "oai_db2.sql")
        if not os.path.isfile(db_path):
            raise Exception(f"{db_path} not found. Call Prepare Scenario with mysql first.")

        with open(db_path) as f:
            content = f.read()

        # Take an existing row as the template so keys, OPc and SQN stay in sync
        # with whatever the committed seed uses.
        row_re = re.compile(r"^\('(?P<imsi>\d+)', '5G_AKA'.*\)[,;]$", re.MULTILINE)
        rows = list(row_re.finditer(content))
        if not rows:
            raise Exception("No AuthenticationSubscription rows found to use as a template")
        existing = {m.group("imsi") for m in rows}
        template_row = rows[0].group(0)
        template_imsi = rows[0].group("imsi")

        wanted = [str(int(start_imsi) + i) for i in range(count)]
        missing = [imsi for imsi in wanted if imsi not in existing]
        if not missing:
            logging.info(f"Database already covers {count} subscribers from {start_imsi}")
            return 0

        # A fresh INSERT rather than editing the existing block, so the committed
        # statement and its terminator are left untouched.
        header = ("INSERT INTO `AuthenticationSubscription` (`ueid`, `authenticationMethod`, "
                  "`encPermanentKey`, `protectionParameterId`, `sequenceNumber`, "
                  "`authenticationManagementField`, `algorithmId`, `encOpcKey`, `encTopcKey`, "
                  "`vectorGenerationInHss`, `n5gcAuthMethod`, `rgAuthenticationInd`, `supi`) VALUES\n")
        generated = []
        for imsi in missing:
            generated.append(template_row.rstrip(",;").replace(template_imsi, imsi))

        with open(db_path, "a") as f:
            f.write(f"\n-- {len(generated)} subscribers generated for the scale tests\n")
            f.write(header)
            f.write(",\n".join(generated))
            f.write(";\n")

        logging.info(f"Added {len(generated)} subscribers to {db_path} "
                     f"(IMSI {missing[0]}..{missing[-1]})")
        return len(generated)

    def set_ext_dn_ue_subnet(self, subnet):
        """
        Points the ext-DN's route towards the UE pool at `subnet`.

        The template hardcodes 12.1.1.0/24, which caps a scale run at 254 PDU
        sessions. The healthcheck greps the routing table for that same prefix, so
        both have to move together.

        Must be called after Prepare Scenario and before Start CN.

        :param subnet: UE subnet in CIDR, e.g. 12.1.0.0/16
        """
        with open(self.docker_compose_path) as f:
            parsed = yaml.safe_load(f)

        service = parsed["services"].get("oai-ext-dn")
        if service is None:
            raise Exception("oai-ext-dn is not part of this scenario")

        old_prefix = "12.1.1.0/24"
        service["entrypoint"] = service["entrypoint"].replace(old_prefix, subnet)
        # grep on the network part only, so it still matches once the route is installed
        network = subnet.split("/")[0].rsplit(".", 1)[0]
        service["healthcheck"]["test"] = f'/bin/bash -c "ip r | grep {network}"'

        with open(self.docker_compose_path, "w") as f:
            yaml.dump(parsed, f)
        logging.info(f"ext-DN now routes the UE pool {subnet}")

    def amf_ue_context_count(self, container="oai-amf"):
        """
        Number of UEs the AMF still holds, read from its periodic statistics table.

        The AMF prints a "UEs' Information" table every statistics_timer_interval
        seconds (20 by default). Only the most recent table is counted, so the answer
        reflects the AMF's current state rather than the whole history.

        Useful for leak detection: after every UE has deregistered the table should be
        empty, and a count that grows across repeated attach/detach cycles means the
        AMF is not releasing contexts.

        :return: number of distinct SUPIs in the latest statistics table
        """
        log = self.docker_api.get_log(container)
        marker = "UEs' Information"
        if marker not in log:
            raise Exception(
                f"{container} has not printed a '{marker}' table yet. It is emitted "
                f"every statistics_timer_interval seconds, so allow one interval.")

        # From the last table header up to the dashed line that closes it
        tail = log[log.rindex(marker):]
        body = re.split(r"\n-{20,}", tail, maxsplit=2)
        table = body[1] if len(body) > 1 else tail

        # The AMF does NOT drop rows when a UE deregisters: it keeps them with state
        # 5GMM-DEREGISTERED. Counting rows would therefore never reach zero, so only
        # UEs still in an active state are counted. Row layout is
        #   | Index | 5GMM State | IMSI/SUPI | GUTI | RAN UE NGAP ID | ...
        active = []
        for line in table.splitlines():
            fields = [f.strip() for f in line.split("|")]
            if len(fields) < 4:
                continue
            state, supi = fields[2], fields[3]
            if not re.fullmatch(r"\d{15}", supi):
                continue  # header or padding row
            if "DEREGISTERED" not in state.upper():
                active.append(f"{supi} ({state})")

        if active:
            logging.info(f"{container} still holds {len(active)} active UE context(s): "
                         f"{active[:5]}{' ...' if len(active) > 5 else ''}")
        else:
            logging.info(f"{container} holds no active UE context")
        return len(active)

    def core_should_have_no_ue_context(self, container="oai-amf"):
        """
        Fails unless the AMF's latest statistics table is empty.

        Call after every UE has deregistered. Give the AMF one statistics interval
        first, e.g. with Wait Until Keyword Succeeds, since the table is only
        refreshed periodically.
        """
        count = self.amf_ue_context_count(container)
        if count != 0:
            raise Exception(
                f"{container} still holds {count} UE context(s) after every UE "
                f"deregistered; contexts are leaking")
        logging.info(f"{container} released every UE context")
        return 0

    def ext_dn_route_should_exist(self, subnet, container="oai-ext-dn"):
        """
        Fails unless the ext-DN actually has a route to the UE pool.

        Set Ext Dn Ue Subnet rewrites the entrypoint before the container starts, but
        the route is only installed at runtime and a failure there is easy to miss:
        downlink traffic towards the UEs would simply be dropped. Worth asserting
        explicitly for tests that send traffic towards a UE, such as paging.

        :param subnet: expected UE subnet in CIDR, e.g. 12.1.0.0/16
        :param container: container to check, normally the ext-DN
        """
        routes = self.docker_api.exec_on_container(container, "/bin/bash -c 'ip route'")
        if subnet not in routes:
            raise Exception(
                f"{container} has no route to the UE pool {subnet}. Routes are:\n{routes}")
        logging.info(f"{container} routes the UE pool {subnet}")
        return routes

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
