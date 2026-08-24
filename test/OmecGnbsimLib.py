# SPDX-License-Identifier: LicenseRef-CSSL-1.0

"""
Robot Framework library driving omec-project gnbsim (https://github.com/omec-project/gnbsim).

gnbsim is a run-to-completion tester: it executes one enabled profile against the
core network, prints a pass/fail summary, dumps per-UE procedure latencies and
exits. This library therefore follows the same shape as NGAPTesterLib rather than
GNBSimTestLib: start the container, wait for it to exit, then read the results out
of its log.

What it gives the suites that the legacy gnbsim image cannot:
  - ueCount / execInParallel, i.e. many UEs registered sequentially or all at once
  - the registration, service request and deregistration procedures as first class
    profiles instead of only "attach and ping"
  - per-UE latency for each of those procedures, in microseconds
"""

import re
import shutil

from common import *
from docker_api import DockerApi

TEMPLATE_DOCKER_COMPOSE = "template/docker-compose-omec-gnbsim.yaml"
TEMPLATE_CONFIG = "template/omec_gnbsim_template_config.yaml"

GNBSIM_N2_IP = "192.168.79.171"
GNBSIM_N3_IP = "192.168.80.171"

# gnbsim does not handle SIGTERM, and by the time we stop it the run is over.
STOP_TIMEOUT = 2

# "UE: imsi-208950000000031, TotalRegTime[us]: 21514, RegReqAuthReq[us]: 8801, ..."
STATS_LINE = re.compile(r"UE:\s*(?P<supi>\S+?),\s*(?P<metrics>Total\S+\[us\]:.*)$")
STATS_METRIC = re.compile(r"(?P<name>\w+)\[us\]:\s*(?P<value>-?\d+)")

PROFILE_STATUS = re.compile(r"Profile Status:\s*(?P<status>PASS|FAIL)")
UE_COUNTS = re.compile(r"Ue's Passed:\s*(?P<passed>\d+),\s*Ue's Failed:\s*(?P<failed>\d+)")


class OmecGnbsimLib:
    ROBOT_LIBRARY_SCOPE = 'SUITE'

    def __init__(self):
        self.docker_api = DockerApi()
        self.docker_compose_path = ""
        self.conf_path = ""
        self.name = ""
        self.profile_name = ""
        # {test name: {"profile": str, "ue_count": int, "metrics": {name: [us, ...]}}}
        # Populated per test so the suite can report on whichever subset was run.
        self.metrics_by_test = {}
        prepare_folders()

    @staticmethod
    def __percentile(sorted_values, fraction):
        return sorted_values[min(len(sorted_values) - 1, int(len(sorted_values) * fraction))]

    @staticmethod
    def __as_bool(value):
        # Robot passes ${TRUE}/${FALSE} as bool, but a bare string from the CLI is
        # also accepted so the library stays usable outside Robot.
        if isinstance(value, str):
            return value.strip().lower() in ("true", "yes", "1")
        return bool(value)

    def prepare_omec_gnbsim(self, profile_name, ue_count=1, exec_in_parallel=False, single_interface=True):
        """
        Generates the docker-compose file and the gnbsim config for one run.

        Exactly one profile is enabled, so the container executes only the
        procedure under test.

        :param profile_name: profileName from the config template, e.g. reg, dereg,
                             pdusess, anrel, servicereq
        :param ue_count: number of UEs the profile runs for
        :param exec_in_parallel: False registers the UEs one after another,
                                 True registers them all at the same time
        :param single_interface: True runs N2 and N3 over the same network. The
                                 default CN attaches oai-upf to the public network
                                 only, so the dedicated N3 network does not exist
                                 unless a UPF that uses it (vpp-upf, eBPF UPF) is
                                 deployed. Pass False only in those scenarios.
        :return: container name
        """
        ue_count = int(ue_count)
        exec_in_parallel = self.__as_bool(exec_in_parallel)
        single_interface = self.__as_bool(single_interface)

        self.profile_name = profile_name
        self.name = f"omec-gnbsim-{profile_name}"
        self.docker_compose_path = os.path.join(get_out_dir(), f"docker-compose-{self.name}.yaml")
        self.conf_path = os.path.join(get_out_dir(), f"gnbsim-{profile_name}.yaml")

        shutil.copy(os.path.join(DIR_PATH, TEMPLATE_CONFIG), self.conf_path)

        with open(self.conf_path) as f:
            parsed = yaml.safe_load(f)

        # Predefined profiles are a list under "profiles"; custom ones are a map under
        # "customProfiles" that gnbsim appends to the same list at load time. Both have
        # to be walked so exactly one profile ends up enabled.
        all_profiles = list(parsed["configuration"].get("profiles") or [])
        all_profiles += list((parsed["configuration"].get("customProfiles") or {}).values())

        selected = None
        for profile in all_profiles:
            if profile["profileName"] == profile_name:
                profile["enable"] = True
                profile["ueCount"] = ue_count
                profile["execInParallel"] = bool(exec_in_parallel)
                selected = profile
            else:
                profile["enable"] = False
        if selected is None:
            names = [p["profileName"] for p in all_profiles]
            raise Exception(f"Unknown gnbsim profile '{profile_name}'. Available: {names}")

        # gnbsim fails a UE once perUserTimeout expires. That budget is per UE but the
        # wait is wall-clock, so under a large parallel run every UE is queued behind
        # the others and a fixed 30s starts failing UEs that were merely waiting.
        # Deregistration is the procedure that degrades worst under concurrency, so the
        # budget scales one-for-one with the run size rather than by a fraction.
        selected["perUserTimeout"] = max(60, ue_count)

        parsed["configuration"]["singleInterface"] = single_interface
        if single_interface:
            # N3 rides on the N2 address; there is no separate N3 network to join.
            # Every gNB keeps its own address: GTP-U is fixed at port 2152, so two
            # gNBs cannot share one IP and still both carry user plane.
            for gnb in parsed["configuration"]["gnbs"].values():
                gnb["n3IpAddr"] = gnb["n2IpAddr"]

        for gnb_name in (selected.get("gnbName"), selected.get("targetGnbName")):
            if gnb_name and gnb_name not in parsed["configuration"]["gnbs"]:
                raise Exception(f"Profile '{profile_name}' references unknown gNB '{gnb_name}'")

        # Addresses the container has to own. gnbsim initialises every gNB in the
        # config, not only the ones the enabled profile uses, and binds GTP-U on each,
        # so all of their addresses must exist or start-up fails. compose can pin only
        # one, so the rest are added to the interface at start-up (the container is
        # privileged and carries iproute2).
        extra_ips = []
        for gnb in parsed["configuration"]["gnbs"].values():
            for addr in (gnb["n2IpAddr"], gnb["n3IpAddr"]):
                if addr != GNBSIM_N2_IP and addr not in extra_ips:
                    extra_ips.append(addr)

        with open(self.conf_path, "w") as f:
            yaml.dump(parsed, f)

        with open(os.path.join(DIR_PATH, TEMPLATE_DOCKER_COMPOSE)) as f:
            compose = yaml.safe_load(f)

        for service in list(compose["services"]):
            svc = compose["services"].pop(service)
            svc["container_name"] = self.name
            svc["volumes"] = [v.replace("REPLACE_CONFIG", self.conf_path) for v in svc["volumes"]]
            svc["networks"]["public_test_net"]["ipv4_address"] = GNBSIM_N2_IP
            if single_interface:
                svc["networks"].pop("n3_test_net", None)
                compose["networks"].pop("n3_test_net", None)
            else:
                svc["networks"]["n3_test_net"]["ipv4_address"] = GNBSIM_N3_IP
            if get_image_tag("omec-gnbsim"):
                svc["image"] = get_image_tag("omec-gnbsim")
            if extra_ips:
                add_ips = " ".join(f"ip addr add {ip}/25 dev eth0;" for ip in extra_ips)
                svc.pop("command", None)
                svc["entrypoint"] = ["/bin/bash", "-c",
                                     f"{add_ips} exec /usr/local/bin/gnbsim --cfg /gnbsim/config/gnbsim.yaml"]
                logging.info(f"gnbsim will also own {extra_ips} (additional gNB addresses)")
            compose["services"][self.name] = svc

        with open(self.docker_compose_path, "w") as f:
            yaml.dump(compose, f)

        logging.info(f"Prepared gnbsim profile {profile_name}: {ue_count} UE(s), "
                     f"{'parallel' if exec_in_parallel else 'sequential'}")
        return self.name

    def replace_in_gnbsim_config(self, path, value):
        """
        Sets and replaces YAML values in the generated gnbsim config.

        :param path: list of keys, e.g. configuration, gnbs, gnb1, n3IpAddr
        :param value: value to set
        """
        replace_in_config_generic(path, value, self.conf_path)

    def start_omec_gnbsim(self):
        start_docker_compose(self.docker_compose_path)

    def stop_omec_gnbsim(self):
        stop_docker_compose(self.docker_compose_path, timeout=STOP_TIMEOUT)

    def down_omec_gnbsim(self):
        down_docker_compose(self.docker_compose_path, timeout=STOP_TIMEOUT)

    def check_omec_gnbsim_done(self):
        """Fails until the gnbsim container has finished its run."""
        self.docker_api.check_container_stopped(self.name)

    def __get_log(self):
        return self.docker_api.get_log(self.name)

    def check_omec_gnbsim_result(self):
        """
        Fails unless gnbsim reported the profile as passed for every UE.

        Checked separately from the UE counters because gnbsim reports
        "Profile Status: FAIL" via its error list, which is the authoritative
        verdict, while the counters tell us how many UEs got through.
        """
        self.check_omec_gnbsim_done()
        log = self.__get_log()

        status = PROFILE_STATUS.search(log)
        if status is None:
            raise Exception(
                f"gnbsim did not report a profile status for '{self.profile_name}'. "
                f"The run probably did not start - check the container log.")
        counts = UE_COUNTS.search(log)
        passed = int(counts.group("passed")) if counts else 0
        failed = int(counts.group("failed")) if counts else 0

        if status.group("status") != "PASS" or failed != 0:
            raise Exception(
                f"gnbsim profile '{self.profile_name}' failed "
                f"(UEs passed: {passed}, failed: {failed}). See {self.name} log.")
        logging.info(f"gnbsim profile '{self.profile_name}' passed for {passed} UE(s)")
        return passed

    def get_omec_gnbsim_stats(self):
        """
        Parses the per-UE procedure latencies gnbsim dumps at the end of a run.

        :return: {supi: {metric: microseconds}}, e.g.
                 {"imsi-208950000000031": {"TotalRegTime": 21514, "RegReqAuthReq": 8801}}
        """
        self.check_omec_gnbsim_done()
        stats = {}
        for line in self.__get_log().splitlines():
            match = STATS_LINE.search(line)
            if match is None:
                continue
            supi = match.group("supi")
            metrics = stats.setdefault(supi, {})
            for metric in STATS_METRIC.finditer(match.group("metrics")):
                metrics[metric.group("name")] = int(metric.group("value"))
        if not stats:
            raise Exception("gnbsim reported no per-UE statistics. Is the stats logger enabled?")
        return stats

    def get_procedure_time(self, metric, supi=None):
        """
        Returns one latency in microseconds.

        :param metric: e.g. TotalRegTime, TotalDeregistrationTime, TotalServiceReqTime,
                       TotalPduEstTime, TotalCtxReleaseTime
        :param supi: UE to read; defaults to the first one reported
        """
        stats = self.get_omec_gnbsim_stats()
        if supi is None:
            supi = sorted(stats)[0]
        if supi not in stats:
            raise Exception(f"No statistics for {supi}. Known UEs: {sorted(stats)}")
        if metric not in stats[supi]:
            raise Exception(f"No metric {metric} for {supi}. Available: {sorted(stats[supi])}")
        return stats[supi][metric]

    def procedure_should_be_reported_for_all_ues(self, metric, ue_count):
        """
        Fails unless `metric` was reported for exactly `ue_count` UEs.

        This is what makes a multi-UE test meaningful: gnbsim can report
        "Profile Status: PASS" while having run fewer UEs than asked for.
        """
        ue_count = int(ue_count)
        stats = self.get_omec_gnbsim_stats()
        with_metric = [supi for supi, m in stats.items() if metric in m]
        if len(with_metric) != ue_count:
            raise Exception(
                f"Expected {metric} for {ue_count} UE(s), got {len(with_metric)}: {sorted(with_metric)}")
        logging.info(f"{metric} reported for all {ue_count} UE(s)")
        return sorted(with_metric)

    def procedure_time_should_be_below(self, metric, max_ms, supi=None):
        """
        Fails if a procedure took longer than max_ms milliseconds.

        gnbsim reports microseconds; the threshold is in milliseconds because that
        is the useful scale for a registration against a local core.
        """
        max_us = float(max_ms) * 1000
        value = self.get_procedure_time(metric, supi)
        if value > max_us:
            raise Exception(f"{metric} was {value / 1000:.1f} ms, expected below {float(max_ms):.1f} ms")
        logging.info(f"{metric}: {value / 1000:.1f} ms (limit {float(max_ms):.1f} ms)")
        return value

    # Above this, per-UE lines are suppressed: Robot copies every log line into
    # output.xml, so a 5000 UE run would otherwise add 5000 lines per call and
    # bloat the report to the point of killing the run.
    MAX_PER_UE_LOG_LINES = 20

    def log_procedure_times(self, metric):
        """
        Logs a distribution for `metric` and returns it.

        :return: dict with count and min/p50/p95/max in milliseconds
        """
        stats = self.get_omec_gnbsim_stats()
        values = sorted(m[metric] for m in stats.values() if metric in m)
        if not values:
            raise Exception(f"No UE reported {metric}")

        if len(values) <= self.MAX_PER_UE_LOG_LINES:
            for supi in sorted(stats):
                if metric in stats[supi]:
                    logging.info(f"  {supi}: {metric} = {stats[supi][metric] / 1000:.1f} ms")
        else:
            logging.info(f"  (per-UE lines suppressed for {len(values)} UEs)")

        def pct(p):
            return values[min(len(values) - 1, int(len(values) * p))] / 1000

        summary = {
            "count": len(values),
            "min_ms": values[0] / 1000,
            "p50_ms": pct(0.50),
            "p95_ms": pct(0.95),
            "max_ms": values[-1] / 1000,
        }
        logging.info(f"{metric} over {summary['count']} UE(s): "
                     f"min {summary['min_ms']:.1f} ms, p50 {summary['p50_ms']:.1f} ms, "
                     f"p95 {summary['p95_ms']:.1f} ms, max {summary['max_ms']:.1f} ms")
        return summary

    def procedure_should_pass_for_all_ues(self, procedure, ue_count,
                                          times_per_ue=1):
        """
        Fails unless `procedure` completed successfully for exactly `ue_count` UEs.

        Needed for the steps gnbsim publishes no statistics for, above all user data
        generation: a UE whose ICMP does not come back fails the profile, so the test
        would go red, but nothing in the report would say the ping was checked at all.
        This makes that explicit.

        gnbsim logs the outcome as a bare "Procedure Result: PASS" without naming the
        procedure, so the procedure each result belongs to is tracked per SUPI from
        the preceding "execute procedure" line.

        :param procedure: gnbsim procedure name, e.g. USER-DATA-PACKET-GENERATION-PROCEDURE
        :param ue_count: number of UEs expected to have completed it
        :param times_per_ue: how often each UE is expected to have completed it.
                             Profiles that run a procedure more than once per
                             iteration, such as relcycle establishing a second PDU
                             session, need this: without it a UE that gave up after
                             the first run still counts as a pass.
        :return: sorted list of the SUPIs that passed
        """
        ue_count = int(ue_count)
        times_per_ue = int(times_per_ue)
        current = {}
        passed = {}
        total_passes = 0

        for line in self.__get_log().splitlines():
            supi_match = re.search(r'"supi": "(imsi-\d+)"', line)
            if supi_match is None:
                continue
            supi = supi_match.group(1)
            step = re.search(r"execute procedure\s+([A-Z0-9-]+)", line)
            if step is not None:
                current[supi] = step.group(1)
            elif "Procedure Result: PASS" in line and current.get(supi) == procedure:
                passed[supi] = passed.get(supi, 0) + 1
                total_passes += 1

        if len(passed) != ue_count:
            raise Exception(
                f"{procedure} passed for {len(passed)} UE(s), expected {ue_count}")

        # A UE that completed the procedure once but gave up before a later run of
        # it is still in `passed`, so the per-UE count has to be checked separately
        short = {supi: count for supi, count in passed.items()
                 if count != times_per_ue}
        if short:
            detail = ", ".join(f"{supi}: {count}" for supi, count in
                               sorted(short.items())[:10])
            raise Exception(
                f"{procedure} was expected to pass {times_per_ue} time(s) per UE, "
                f"but {len(short)} UE(s) differ ({detail})")

        logging.info(f"{procedure} passed for all {ue_count} UE(s), "
                     f"{times_per_ue} time(s) each "
                     f"({total_passes} successful run(s) in total)")
        return sorted(passed)

    def collect_gnbsim_metrics(self, test_name):
        """
        Records everything gnbsim measured for one test, for the end of run report.

        Call from the test teardown, before the container is removed. Never raises:
        a test that failed before gnbsim produced statistics still has to tear down.

        :param test_name: name the metrics are reported under
        :return: number of metrics recorded
        """
        try:
            stats = self.get_omec_gnbsim_stats()
        except Exception as error:
            # Container already gone, e.g. a test that collected its own metrics and
            # removed it before the teardown ran. Nothing to record rather than a
            # misleading empty row.
            logging.warning(f"No gnbsim metrics for '{test_name}': {error}")
            return 0

        metrics = {}
        for per_ue in stats.values():
            for name, value in per_ue.items():
                metrics.setdefault(name, []).append(value)

        self.metrics_by_test[test_name] = {
            "profile": self.profile_name,
            "ue_count": len(stats),
            "metrics": {name: sorted(values) for name, values in metrics.items()},
        }
        logging.info(f"Recorded {len(metrics)} metric(s) over {len(stats)} UE(s) for '{test_name}'")
        return len(metrics)

    def create_gnbsim_metrics_report(self):
        """
        Builds the end of run metrics table and writes it as CSV next to the logs.

        Covers only the tests that actually ran, so it works for a filtered run as
        well as for the full suite.

        :return: the table as Robot Framework documentation markup
        """
        if not self.metrics_by_test:
            return ""

        csv_path = os.path.join(get_out_dir(), "gnbsim_metrics.csv")
        rows = []
        docu = " = GNBSIM Metrics (all times in ms) = \n"
        docu += "| =Test= | =Profile= | =UEs= | =Metric= | =min= | =p50= | =p95= | =max= | \n"

        for test_name, result in self.metrics_by_test.items():
            if not result["metrics"]:
                docu += f"| {test_name} | {result['profile']} | - | no metrics reported | | | | | \n"
                continue
            for name, values in sorted(result["metrics"].items()):
                stat = (values[0] / 1000,
                        self.__percentile(values, 0.50) / 1000,
                        self.__percentile(values, 0.95) / 1000,
                        values[-1] / 1000)
                docu += (f"| {test_name} | {result['profile']} | {result['ue_count']} | {name} | "
                         f"{stat[0]:.1f} | {stat[1]:.1f} | {stat[2]:.1f} | {stat[3]:.1f} | \n")
                rows.append([test_name, result["profile"], result["ue_count"], name,
                             f"{stat[0]:.3f}", f"{stat[1]:.3f}", f"{stat[2]:.3f}", f"{stat[3]:.3f}"])

        with open(csv_path, "w") as f:
            f.write("test,profile,ue_count,metric,min_ms,p50_ms,p95_ms,max_ms\n")
            for row in rows:
                f.write(",".join(str(field) for field in row) + "\n")
        logging.info(f"Wrote gnbsim metrics for {len(self.metrics_by_test)} test(s) to {csv_path}")

        return docu

    def collect_all_omec_gnbsim_logs(self):
        self.docker_api.store_all_logs(get_log_dir(), [self.name])

    def create_omec_gnbsim_docu(self):
        if not self.name:
            return ""
        image = get_image_tag("omec-gnbsim")
        docu = " = OMEC GNBSIM Image = \n"
        docu += create_image_info_header()
        size, date = self.docker_api.get_image_info(image)
        docu += create_image_info_line("omec-gnbsim", image, date, size)
        return docu
