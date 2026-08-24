# SPDX-License-Identifier: LicenseRef-CSSL-1.0

"""
Robot Framework library driving PacketRusher (https://github.com/HewlettPackard/PacketRusher).

Complements OmecGnbsimLib rather than replacing it. PacketRusher covers what gnbsim
cannot: working N2 handover, Xn handover, and scale beyond gnbsim's user plane
ceiling. gnbsim keeps the lifecycle and idle-cycle tests because it reports
per-procedure latencies directly.

Two structural differences from gnbsim drive the design here:

  - PacketRusher does not exit. `multi-ue` keeps the UEs registered until stopped,
    so a test runs it for a bounded time and then inspects it, instead of waiting
    for the container to finish.
  - PacketRusher has no latency instrumentation at all: no metrics, no summary, and
    the logs carry no per-UE completion timestamps. It still writes a pcap with
    --pcap, kept as a debugging artefact, but no timings are derived from it:
    pairing NGAP request and response per UE is unreliable because NAS is ciphered
    and PacketRusher batches many NGAP messages into one SCTP frame. Use gnbsim
    when per-procedure latencies are what you need.
"""

import re
import shutil

from common import *
from docker_api import DockerApi

TEMPLATE_DOCKER_COMPOSE = "template/docker-compose-packetrusher.yaml"
TEMPLATE_CONFIG = "template/packetrusher_config.yaml"

# Two addresses: handover needs two gNodeBs and compose can pin only one.
PR_IP_1 = "192.168.79.181"
PR_IP_2 = "192.168.79.182"

# PacketRusher does not handle SIGTERM meaningfully and the run is over by the
# time we stop it.
STOP_TIMEOUT = 3

# Log markers. PacketRusher reports progress only through these.
MARKER_REGISTERED = "Registration Accept"
MARKER_PDU_SESSION = "PDU Session Establishment Accept"
MARKER_HANDOVER_SENT = "Initiating NGAP UE Handover"
MARKER_HANDOVER_XN = "Initiating Xn UE Handover"
MARKER_HANDOVER_REQ = "Receive Handover Request"
MARKER_HANDOVER_ACK = "Initiating Handover Request Acknowledge"


class PacketRusherLib:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.docker_api = DockerApi()
        self.docker_compose_path = ""
        self.conf_path = ""
        self.pcap_dir = ""
        self.name = ""
        self.test_name = ""
        prepare_folders()

    def prepare_packet_rusher(self, test_name, command):
        """
        Generates the compose file and config for one PacketRusher run.

        :param test_name: used for the container name and the metrics report
        :param command: everything after the binary, e.g.
                        "multi-ue -n 500 --tr 0 --timeBeforeDeregistration 5000"
                        The --pcap argument is appended automatically.
        :return: container name
        """
        self.test_name = test_name
        slug = re.sub(r"[^a-z0-9]+", "-", test_name.lower()).strip("-")
        self.name = f"packetrusher-{slug}"
        self.docker_compose_path = os.path.join(get_out_dir(), f"docker-compose-{self.name}.yaml")
        self.conf_path = os.path.join(get_out_dir(), f"packetrusher-{slug}.yaml")
        self.pcap_dir = os.path.join(get_out_dir(), f"pcap-{slug}")
        os.makedirs(self.pcap_dir, exist_ok=True)

        shutil.copy(os.path.join(DIR_PATH, TEMPLATE_CONFIG), self.conf_path)

        # PacketRusher writes the capture itself, which avoids needing capture
        # privileges on the host: the suite's tshark based Start Trace cannot run
        # without membership of the wireshark group.
        full_command = f"{command} --pcap /pcap/{slug}.pcap"

        with open(os.path.join(DIR_PATH, TEMPLATE_DOCKER_COMPOSE)) as f:
            compose = yaml.safe_load(f)

        for service in list(compose["services"]):
            svc = compose["services"].pop(service)
            svc["container_name"] = self.name
            svc["volumes"] = [
                v.replace("REPLACE_CONFIG", self.conf_path).replace("REPLACE_PCAP_DIR", self.pcap_dir)
                for v in svc["volumes"]
            ]
            svc["entrypoint"] = [
                part.replace("REPLACE_COMMAND", full_command).replace("REPLACE_IP_2", PR_IP_2)
                for part in svc["entrypoint"]
            ]
            svc["networks"]["public_test_net"]["ipv4_address"] = PR_IP_1
            if get_image_tag("packetrusher"):
                svc["image"] = get_image_tag("packetrusher")
            compose["services"][self.name] = svc

        with open(self.docker_compose_path, "w") as f:
            yaml.dump(compose, f)

        logging.info(f"Prepared PacketRusher '{test_name}': {full_command}")
        return self.name

    def replace_in_packet_rusher_config(self, path, value):
        """Sets and replaces YAML values in the generated PacketRusher config."""
        replace_in_config_generic(path, value, self.conf_path)

    def start_packet_rusher(self):
        start_docker_compose(self.docker_compose_path)

    def stop_packet_rusher(self):
        stop_docker_compose(self.docker_compose_path, timeout=STOP_TIMEOUT)

    def down_packet_rusher(self):
        down_docker_compose(self.docker_compose_path, timeout=STOP_TIMEOUT)

    def __get_log(self):
        return self.docker_api.get_log(self.name)

    def check_packet_rusher_running(self):
        """Fails if PacketRusher has exited, which for multi-ue means it died."""
        self.docker_api.check_container_running(self.name)

    def packet_rusher_log_should_contain(self, marker, count=1):
        """
        Fails unless `marker` appears at least `count` times in the log.

        This is how PacketRusher reports progress: it has no summary and no exit
        code to inspect while multi-ue is running.
        """
        count = int(count)
        found = self.__get_log().count(marker)
        if found < count:
            raise Exception(f"Expected '{marker}' at least {count} time(s) in {self.name} log, found {found}")
        logging.info(f"'{marker}' seen {found} time(s)")
        return found

    def count_registered_ues(self):
        """Number of UEs that reached Registration Accept."""
        return self.__get_log().count(MARKER_REGISTERED)

    def count_pdu_sessions(self):
        """Number of PDU sessions established."""
        return self.__get_log().count(MARKER_PDU_SESSION)

    def registered_ues_should_be(self, expected):
        """Fails unless exactly `expected` UEs registered."""
        expected = int(expected)
        found = self.count_registered_ues()
        if found != expected:
            raise Exception(f"Expected {expected} registered UE(s), got {found}")
        logging.info(f"All {expected} UE(s) registered")
        return found

    def handover_should_have_completed(self):
        """
        Fails unless the full N2 handover exchange is visible.

        Checked as a sequence because a HandoverRequired that the AMF cannot encode
        produces the first marker but never the rest: that is exactly the gnbsim
        failure mode this test exists to avoid regressing into.
        """
        log = self.__get_log()
        for marker in (MARKER_HANDOVER_SENT, MARKER_HANDOVER_REQ, MARKER_HANDOVER_ACK):
            if marker not in log:
                raise Exception(
                    f"Handover did not complete: '{marker}' missing from {self.name} log")
        logging.info("N2 handover completed: required, request and acknowledge all seen")
        return True

    def run_iperf3_from_ue(self, imsi, server, duration=10, reverse=False, port=39265, bitrate=""):
        """
        Runs iperf3 through the UE's GTP-U tunnel and returns the throughput in Mbit/s.

        This is the UPF stress test: every byte traverses the N3 tunnel and the UPF's
        datapath, so the number is a measure of the UPF rather than of the simulator.
        PacketRusher suggests this pattern itself in its tunnel setup log.

        Blocking on purpose, like ping_across_handover: the background exec helpers in
        docker_api cannot reliably stop a process afterwards.

        :param imsi: UE whose tunnel VRF to use
        :param server: address of the iperf3 server, normally the ext-DN
        :param duration: seconds to run
        :param reverse: True measures downlink (server to UE), False uplink
        :param port: iperf3 server port
        :param bitrate: optional target such as "100M"; empty means unlimited
        :return: throughput in Mbit/s as measured at the receiver
        """
        if isinstance(reverse, str):
            reverse = reverse.strip().lower() in ("true", "yes", "1")
        vrf = f"vrf{str(imsi)[-10:]}"
        direction = "downlink" if reverse else "uplink"

        cmd = f"ip vrf exec {vrf} iperf3 -c {server} -p {int(port)} -t {int(duration)}"
        if reverse:
            cmd += " -R"
        if bitrate:
            cmd += f" -b {bitrate}"

        logging.info(f"iperf3 {direction} through the tunnel: {cmd}")
        result = self.docker_api.exec_on_container(self.name, f"/bin/bash -c '{cmd}'")

        # Take the receiver summary: it is what actually arrived, whereas the sender
        # line counts what was handed to the socket.
        match = re.search(r"([\d.]+)\s+([KMG])bits/sec\s+.*receiver", result)
        if match is None:
            raise Exception(f"Could not parse iperf3 output:\n{result[-500:]}")

        value, unit = float(match.group(1)), match.group(2)
        mbps = {"K": value / 1000, "M": value, "G": value * 1000}[unit]
        logging.info(f"iperf3 {direction}: {mbps:.1f} Mbit/s")
        return mbps

    def throughput_should_be_above(self, minimum_mbps, actual_mbps):
        """
        Fails if the measured throughput is below `minimum_mbps`.

        A floor rather than a target: this catches a UPF datapath that has fallen over
        or is forwarding at a fraction of its normal rate, without turning normal
        variation between runs into a failure.
        """
        minimum_mbps = float(minimum_mbps)
        actual_mbps = float(actual_mbps)
        if actual_mbps < minimum_mbps:
            raise Exception(
                f"Throughput was {actual_mbps:.1f} Mbit/s, expected at least {minimum_mbps:.1f} Mbit/s")
        logging.info(f"Throughput {actual_mbps:.1f} Mbit/s is above the {minimum_mbps:.1f} Mbit/s floor")
        return actual_mbps

    def get_ue_ip_from_log(self):
        """
        Returns the address the UE was given, read from the tunnel setup line.

        PacketRusher logs it as
          [UE][GTP] Interface valXXXXXXXXXX has successfully been configured for UE 12.1.1.2
        Needed for paging: the downlink traffic that triggers the page has to be
        aimed at the UE's own address.
        """
        match = re.search(r"has successfully been configured for UE ([\d.]+)", self.__get_log())
        if match is None:
            raise Exception(
                f"No UE address in {self.name} log. Was the run started with --tunnel?")
        ue_ip = match.group(1)
        logging.info(f"UE address is {ue_ip}")
        return ue_ip

    def trigger_downlink_traffic(self, container, ue_ip, count=4):
        """
        Sends downlink traffic towards an idle UE from outside the RAN.

        This is what makes the core page: PacketRusher can put a UE into CM-IDLE but
        cannot make the network originate traffic towards it, so the ext-DN has to
        do it. The ping is expected to lose its first packets while the UE is being
        paged and brought back, so failure is not treated as an error here.

        :param container: container to send from, normally the ext-DN
        :param ue_ip: UE address to target
        :param count: echo requests to send
        """
        cmd = f"ping -c {int(count)} -W 3 {ue_ip}"
        logging.info(f"Triggering downlink traffic from {container} to {ue_ip}")
        try:
            result = self.docker_api.exec_on_container(container, f"/bin/bash -c '{cmd}'")
        except Exception as error:
            # Loss here is expected while the UE is idle; the paging is the signal
            result = str(error)
        logging.info(result)
        return result

    def ping_across_handover(self, imsi, target, duration=40, interval=0.1):
        """
        Runs a continuous ping that spans the handover and reports the loss.

        A ping taken after the handover only shows the tunnel works on the target
        gNB; it says nothing about what happened during the switch. Running it
        across the handover turns the gap into a measurement: with a fixed send
        interval, lost packets x interval approximates the user plane interruption.

        Blocking on purpose. The background exec helpers in docker_api are unreliable
        for stopping a process later (see the TODO in qos_tests.robot), so a bounded
        run that outlives the handover is used instead of start/stop.

        Sub 200ms intervals need root, which the privileged container has.

        :param imsi: UE whose tunnel VRF to use
        :param target: address to ping, normally the ext-DN
        :param duration: seconds to keep pinging; must outlast the handover trigger
        :param interval: seconds between echo requests, i.e. the measurement resolution
        :return: dict with transmitted, received, loss_pct and interruption_ms
        """
        duration = float(duration)
        interval = float(interval)
        count = int(duration / interval)
        vrf = f"vrf{str(imsi)[-10:]}"

        cmd = f"ip vrf exec {vrf} ping -i {interval} -c {count} -W 2 {target}"
        logging.info(f"Pinging across the handover for {duration}s at {interval}s intervals")
        result = self.docker_api.exec_on_container(self.name, f"/bin/bash -c '{cmd}'")

        match = re.search(
            r"(?P<tx>\d+) packets transmitted, (?P<rx>\d+) received.*?(?P<loss>[\d.]+)% packet loss",
            result, re.DOTALL)
        if match is None:
            raise Exception(f"Could not parse ping output:\n{result[-400:]}")

        transmitted = int(match.group("tx"))
        received = int(match.group("rx"))
        stats = {
            "transmitted": transmitted,
            "received": received,
            "loss_pct": float(match.group("loss")),
            "interruption_ms": (transmitted - received) * interval * 1000,
        }
        logging.info(
            f"User plane across handover: {received}/{transmitted} replies, "
            f"{stats['loss_pct']:.1f}% loss, interruption approx {stats['interruption_ms']:.0f} ms")
        return stats

    def handover_interruption_should_be_below(self, max_ms, stats):
        """
        Fails if the user plane gap across the handover exceeded max_ms.

        Also fails if nothing came back at all: 100% loss means the tunnel never
        worked, which is a different fault from a long interruption.
        """
        max_ms = float(max_ms)
        if stats["received"] == 0:
            raise Exception(
                f"No ICMP replies at all ({stats['transmitted']} sent). The user plane "
                f"never worked, so this is not a handover interruption measurement.")
        if stats["interruption_ms"] > max_ms:
            raise Exception(
                f"User plane interrupted for approx {stats['interruption_ms']:.0f} ms "
                f"({stats['loss_pct']:.1f}% loss), expected below {max_ms:.0f} ms")
        logging.info(f"Interruption {stats['interruption_ms']:.0f} ms is within {max_ms:.0f} ms")
        return stats["interruption_ms"]

    def ping_from_ue(self, imsi, target, count=4):
        """
        Pings `target` through the UE's GTP-U tunnel.

        PacketRusher puts each UE's tunnel in its own VRF, so traffic has to be run
        inside it. Requires the run to have used --tunnel (and therefore
        --dedicatedGnb, which PacketRusher enforces).
        """
        count = int(count)
        vrf = f"vrf{str(imsi)[-10:]}"
        cmd = f"ip vrf exec {vrf} ping -c {count} -W 2 {target}"
        result = self.docker_api.exec_on_container(self.name, f"/bin/bash -c '{cmd}'")
        logging.info(result)
        return result

    def collect_all_packet_rusher_logs(self):
        self.docker_api.store_all_logs(get_log_dir(), [self.name])

    def create_packet_rusher_docu(self):
        if not self.name:
            return ""
        image = get_image_tag("packetrusher")
        docu = " = PacketRusher Image = \n"
        docu += create_image_info_header()
        size, date = self.docker_api.get_image_info(image)
        docu += create_image_info_line("packetrusher", image, date, size)
        return docu
