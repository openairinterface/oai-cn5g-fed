# SPDX-License-Identifier: LicenseRef-CSSL-1.0

import os
import shutil
import subprocess
import urllib.request

import yaml

from common import (
    create_image_info_header,
    create_image_info_line,
    down_docker_compose,
    get_image_tag,
    get_log_dir,
    get_out_dir,
    prepare_folders,
    speed_up_healthchecks,
    start_docker_compose,
    stop_docker_compose,
)
from docker_api import DockerApi


COMPOSE_TEMPLATE = "template/docker-compose-ocudu.yaml"
OCUDU_CONFIG_TEMPLATE = "template/ocudu.yml"
NR_UE_CONFIG_TEMPLATE = "../docker-compose/ran-conf/nr-ue.conf"
OAI_RAN_REPOSITORY = "https://github.com/duranta-project/openairinterface5g.git"
OAI_RAN_BRANCH = "develop"
OAI_RAN_RAW_URL = "https://raw.githubusercontent.com/duranta-project/openairinterface5g"
UE_CAPABILITY_PATH = "targets/PROJECTS/GENERIC-NR-5GC/CONF/uecap_ports1.xml"
OCUDU_CONTAINER = "ocudu-gnb"
NR_UE_CONTAINER = "ocudu-oai-nr-ue"


class OcuDuLib:
    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self):
        self.docker_api = DockerApi()
        self.docker_compose_path = ""
        self.oai_ran_commit = ""
        prepare_folders()

    def _resolve_oai_ran_commit(self):
        ref = f"refs/heads/{OAI_RAN_BRANCH}"
        try:
            result = subprocess.run(
                ["git", "ls-remote", OAI_RAN_REPOSITORY, ref],
                capture_output=True,
                check=True,
                text=True,
                timeout=30,
            )
            commit, resolved_ref = result.stdout.strip().split()
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            raise Exception(
                f"Cannot resolve {OAI_RAN_REPOSITORY} {OAI_RAN_BRANCH}: {error}"
            ) from error
        if resolved_ref != ref or len(commit) != 40:
            raise Exception(f"Unexpected git ls-remote output: {result.stdout.strip()}")
        return commit

    def prepare_ocudu_ran(self):
        """Prepare one O-CU/DU gNB and one OAI NR UE."""
        self.docker_compose_path = os.path.join(
            get_out_dir(), "docker-compose-ocudu-ran.yaml"
        )
        shutil.copy(
            os.path.join(os.path.dirname(__file__), OCUDU_CONFIG_TEMPLATE),
            os.path.join(get_out_dir(), "ocudu.yml"),
        )
        shutil.copy(
            os.path.join(os.path.dirname(__file__), NR_UE_CONFIG_TEMPLATE),
            os.path.join(get_out_dir(), "nr-ue.conf"),
        )
        self.oai_ran_commit = self._resolve_oai_ran_commit()
        ue_capability_url = (
            f"{OAI_RAN_RAW_URL}/{self.oai_ran_commit}/{UE_CAPABILITY_PATH}"
        )
        try:
            with urllib.request.urlopen(ue_capability_url, timeout=30) as response:
                ue_capability = response.read()
        except OSError as error:
            raise Exception(
                f"Cannot download the UE capabilities from {ue_capability_url}: {error}"
            ) from error
        with open(os.path.join(get_out_dir(), "uecap_ports1.xml"), "wb") as output:
            output.write(ue_capability)

        with open(
            os.path.join(os.path.dirname(__file__), COMPOSE_TEMPLATE),
            encoding="utf-8",
        ) as template:
            parsed = yaml.safe_load(template)

        parsed["services"][OCUDU_CONTAINER]["image"] = get_image_tag(OCUDU_CONTAINER)
        parsed["services"]["oai-nr-ue"]["image"] = get_image_tag("oai-nr-ue")
        speed_up_healthchecks(parsed["services"])

        with open(self.docker_compose_path, "w", encoding="utf-8") as output:
            yaml.safe_dump(parsed, output, sort_keys=False)

        return self.docker_compose_path

    def start_ocudu_gnb(self):
        start_docker_compose(self.docker_compose_path, container=OCUDU_CONTAINER)

    def start_ocudu_nr_ue(self):
        start_docker_compose(self.docker_compose_path, container="oai-nr-ue")

    def check_ocudu_gnb_health_status(self):
        self.docker_api.check_health_status([OCUDU_CONTAINER])

    def check_ocudu_ran_health_status(self):
        self.docker_api.check_health_status([OCUDU_CONTAINER, NR_UE_CONTAINER])

    def get_ocudu_ue_ip_address(self):
        log = self.docker_api.get_log(NR_UE_CONTAINER)
        for line in log.splitlines():
            if " IPv4 " not in line:
                continue
            for part in line.split(","):
                if " IPv4 " in part:
                    return part.strip().split()[-1]
        raise Exception("PDU session establishment is still ongoing for the O-CU/DU UE")

    def ping_from_ocudu_ue(self, target, count=4):
        count = int(count)
        return self.docker_api.exec_on_container(
            NR_UE_CONTAINER,
            f"ping -I oaitun_ue1 -c {count} -W 2 {target}",
        )

    def collect_all_ocudu_logs(self):
        return self.docker_api.store_all_logs(
            get_log_dir(), [OCUDU_CONTAINER, NR_UE_CONTAINER]
        )

    def stop_ocudu_ran(self):
        if self.docker_compose_path:
            stop_docker_compose(self.docker_compose_path)

    def down_ocudu_ran(self):
        if self.docker_compose_path:
            down_docker_compose(self.docker_compose_path)

    def create_ocudu_docu(self):
        docu = " = O-CU/DU RAN Images = \n"
        docu += create_image_info_header()
        for container in (OCUDU_CONTAINER, "oai-nr-ue"):
            image = get_image_tag(container)
            size, date = self.docker_api.get_image_info(image)
            docu += create_image_info_line(container, image, date, size)
        docu += f"\nOAI RAN {OAI_RAN_BRANCH} commit: {self.oai_ran_commit}\n"
        return docu
