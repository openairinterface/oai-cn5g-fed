#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for the Npcf_PolicyAuthorization app-sessions API [TS 29.514 §4.2]:
POST (create), GET (read), PATCH (modify), and terminate (delete).

The PCF's HTTP/2 server speaks h2c *with prior knowledge* (cleartext HTTP/2,
no TLS/ALPN, no Upgrade dance). Neither packages `requests` (HTTP/1.1 only) nor
`httpx`/`httpcore` (HTTP/2 only via TLS ALPN) can produce that request, so
requests are shelled out to `curl --http2-prior-knowledge` for transport;
everything else -- building request bodies, parsing responses, asserting on
them -- is plain Python/`json`. No pip dependencies.

Configuration (environment variables):
    PCF_HOST      PCF SBI address                        (default: 192.168.70.139)
    PCF_PORT      PCF SBI port                            (default: 8080)
    AF_CONTAINER  If set, curl runs as `docker exec $AF_CONTAINER curl ...`
                  (matches the demo topology, where the AF is a separate
                  container on the PCF's Docker network). If unset, curl
                  runs directly on whatever host invokes this script.
    UE_IPV4       UE address used to bind app sessions    (default: 12.1.1.10)
    DNN           DNN of the UE's PDU session              (default: internet)
    SNSSAI_SST    Slice SST the session runs on            (default: 1)
    SNSSAI_SD     Slice SD (hex, optional)                 (default: unset)
    QOS_REFERENCE Operator qosReference to request         (default: OAI_QOS_GBR_VIDEO_1)
    NOTIF_URI     AF notification URI                      (default: http://192.168.70.144/notifications)

Usage:
    ./pa_app_session_tests.py lifecycle
    ./pa_app_session_tests.py create --af-app-id my-test
    ./pa_app_session_tests.py get <app_session_id>
    ./pa_app_session_tests.py patch <app_session_id> --scenario {modify,add,remove,reject}
    ./pa_app_session_tests.py delete <app_session_id>

Every subcommand exits 0 if all its assertions passed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field

# ===========================================================================
# CONFIG
# ===========================================================================

PCF_HOST = os.environ.get("PCF_HOST", "192.168.70.139")
PCF_PORT = os.environ.get("PCF_PORT", "8080")
AF_CONTAINER = os.environ.get("AF_CONTAINER", "")
UE_IPV4 = os.environ.get("UE_IPV4", "12.1.1.10")

# Values the app-session must line up with the UE's live PDU session and the PCF's
# operator policy. Defaults reproduce the standalone demo topology; the fed robot
# suite overrides them to match the deployed slice/DNN and the shipped qosReference.
DNN = os.environ.get("DNN", "internet")
SNSSAI_SST = int(os.environ.get("SNSSAI_SST", "1"))
SNSSAI_SD = os.environ.get("SNSSAI_SD", "")
QOS_REFERENCE = os.environ.get("QOS_REFERENCE", "OAI_QOS_GBR_VIDEO_1")
NOTIF_URI = os.environ.get("NOTIF_URI", "http://192.168.70.144/notifications")


def _slice_info() -> dict:
    info: dict = {"sst": SNSSAI_SST}
    if SNSSAI_SD:
        info["sd"] = SNSSAI_SD
    return info

BASE_URL = f"http://{PCF_HOST}:{PCF_PORT}/npcf-policyauthorization/v1/app-sessions"

# Unlikely to collide with any real header/body content; marks where curl's
# -w status-code output starts so it can be split off the captured stdout.
_STATUS_MARKER = "###PA_TEST_STATUS###"


# ===========================================================================
# TRANSPORT -- curl over HTTP/2 prior-knowledge
# ===========================================================================


@dataclass
class Response:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""

    def header(self, name: str) -> str | None:
        return self.headers.get(name.lower())

    def json(self) -> dict | None:
        if not self.body.strip():
            return None
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None


def curl_request(
    method: str,
    path: str = "",
    content_type: str | None = None,
    body: dict | str | None = None,
) -> Response:
    """Issue one request to BASE_URL + path over HTTP/2 prior-knowledge.

    `body`, if a dict, is JSON-encoded. Returns a Response with the parsed
    status code, headers (lower-cased names), and raw body text.
    """
    url = f"{BASE_URL}{path}"
    argv = ["curl", "--http2-prior-knowledge", "-s", "-D", "-", "-X", method]

    if content_type:
        argv += ["-H", f"Content-Type: {content_type}"]
    if body is not None:
        payload = json.dumps(body) if isinstance(body, dict) else body
        argv += ["-d", payload]
    argv += ["-w", f"\n{_STATUS_MARKER}%{{http_code}}\n", url]

    full_argv = ["docker", "exec", AF_CONTAINER] + argv if AF_CONTAINER else argv

    result = subprocess.run(full_argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"curl failed (exit {result.returncode}) for {method} {url}: "
            f"{result.stderr.strip()}"
        )

    return _parse_response(result.stdout)


def _parse_response(raw: str) -> Response:
    marker_pos = raw.rfind(_STATUS_MARKER)
    if marker_pos == -1:
        raise RuntimeError(f"curl output missing status marker; got: {raw!r}")
    head_and_body = raw[:marker_pos]
    status_text = raw[marker_pos + len(_STATUS_MARKER) :].strip()
    status = int(status_text)

    # curl's `-D -` prints the synthesized status line ("HTTP/2 201"), then
    # header lines, then a blank line, then (since -o wasn't given) the body.
    if "\r\n\r\n" in head_and_body:
        header_block, _, body = head_and_body.partition("\r\n\r\n")
    else:
        header_block, _, body = head_and_body.partition("\n\n")

    headers: dict[str, str] = {}
    for line in header_block.splitlines()[1:]:  # skip the "HTTP/2 NNN" line
        if ":" in line:
            name, _, value = line.partition(":")
            headers[name.strip().lower()] = value.strip()

    return Response(status=status, headers=headers, body=body.strip())


def app_session_id_from_location(location: str) -> str:
    """Extract the trailing {appSessionId} path segment from a Location header."""
    return location.rstrip("/").rsplit("/", 1)[-1]


# ===========================================================================
# ASSERTIONS / REPORTING
# ===========================================================================


class TestReport:
    """Accumulates pass/fail assertions without raising, so one failed check
    doesn't stop the rest of a scenario from running and reporting."""

    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0

    def check(self, description: str, condition: bool, detail: str = "") -> bool:
        if condition:
            self.passed += 1
            print(f"  [PASS] {description}")
        else:
            self.failed += 1
            suffix = f" -- {detail}" if detail else ""
            print(f"  [FAIL] {description}{suffix}")
        return condition

    def check_eq(self, description: str, expected, actual) -> bool:
        return self.check(
            description, expected == actual, f"expected {expected!r}, got {actual!r}"
        )

    def check_in(self, description: str, item, container) -> bool:
        return self.check(
            description, item in container, f"expected {item!r} in {container!r}"
        )

    def check_not_in(self, description: str, item, container) -> bool:
        return self.check(
            description, item not in container, f"expected {item!r} not in {container!r}"
        )

    def summary(self) -> bool:
        print(f"\n== {self.name}: {self.passed} passed, {self.failed} failed ==")
        return self.failed == 0

    def merge(self, other: "TestReport") -> None:
        self.passed += other.passed
        self.failed += other.failed


# ===========================================================================
# REQUEST BODIES -- one validated source of truth per scenario
# ===========================================================================


def guaranteed_video_request_body(
    ue_ipv4: str | None = None,
    notif_uri: str | None = None,
    af_app_id: str = "pa-test-create",
) -> dict:
    """A create request for guaranteed-QoS video via an operator qosReference
    [TS 29.514 §4.2.2.2]. Component 1 carries a single downlink SDF filter."""
    ue_ipv4 = ue_ipv4 or UE_IPV4
    notif_uri = notif_uri or NOTIF_URI
    return {
        "ascReqData": {
            "notifUri": notif_uri,
            "suppFeat": "0",
            "ueIpv4": ue_ipv4,
            "dnn": DNN,
            "sliceInfo": _slice_info(),
            "afAppId": af_app_id,
            "medComponents": {
                "1": {
                    "medCompN": 1,
                    "qosReference": QOS_REFERENCE,
                    "fStatus": "ENABLED",
                    "medSubComps": {
                        "1": {
                            "fNum": 1,
                            "fDescs": [f"permit out ip from any to {ue_ipv4} 5000"],
                            "fStatus": "ENABLED",
                        }
                    },
                }
            },
        }
    }


def patch_modify_body(ue_ipv4: str | None = None, uplink_filter: bool = True) -> dict:
    """PATCH modifying component 1 to an explicit GBR flow (10/8 Mbps, 40ms).

    Deliberately reuses medCompN 1 -- the same number guaranteed_video_request_body()
    used to create the session -- rather than a fresh one. This is what makes the PCF
    treat the request as a MODIFY of the existing flow instead of installing a second,
    duplicate one. That behaviour is not one explicit sentence in the spec; it follows
    from combining: (1) "medComponents" is a map keyed by "medCompN" in both the create
    and PATCH request bodies [TS 29.514 tables 5.6.2.3-1, 5.6.2.5-1], and (2) the PATCH
    body must be an RFC 7396 JSON Merge Patch [TS 29.514 §4.2.3.2] -- RFC 7396's merge
    semantics are what turn "same key" into "replace/merge that member". See the fuller
    citation trail (incl. TS 29.514 §4.2.3.13, §4.2.3.41) at the PCF's own id-derivation
    site: src/pcf_app/policy_auth/app_session.cpp, create_qos_data_from_media_component().
    Contrast with patch_add_body() below, which uses an unseen medCompN to add.

    `uplink_filter=False` reproduces the rejection case: uplink GBR is
    requested but no uplink SDF filter is present, so per-SDF uplink MBR
    aggregates to 0 and GBR(8Mbps) > MBR(0) fails check E -- 403
    INVALID_SERVICE_INFORMATION [TS 29.512 §4.2.6.6.2].
    """
    ue_ipv4 = ue_ipv4 or UE_IPV4
    fdescs = [f"permit out ip from any to {ue_ipv4} 5000"]
    if uplink_filter:
        fdescs.append(f"permit in ip from {ue_ipv4} 5000 to any")
    return {
        "ascReqData": {
            "medComponents": {
                "1": {
                    "medCompN": 1,
                    "marBwUl": "10 Mbps",
                    "marBwDl": "10 Mbps",
                    "mirBwUl": "8 Mbps",
                    "mirBwDl": "8 Mbps",
                    "desMaxLatency": 40,
                    "fStatus": "ENABLED",
                    "medSubComps": {
                        "1": {"fNum": 1, "fStatus": "ENABLED", "fDescs": fdescs}
                    },
                }
            }
        }
    }


def patch_add_body(ue_ipv4: str | None = None) -> dict:
    """PATCH adding a new media component (medCompN 2, 5 Mbps downlink).

    medCompN 2 has not appeared in this app-session before (creation and
    patch_modify_body() above both used 1), so the PCF installs a new QoS
    flow/PCC rule rather than modifying an existing one -- see the ADD side of
    the same medCompN-as-map-key + RFC 7396 mechanism documented at
    patch_modify_body() above.
    """
    ue_ipv4 = ue_ipv4 or UE_IPV4
    return {
        "ascReqData": {
            "medComponents": {
                "2": {
                    "medCompN": 2,
                    "marBwDl": "5 Mbps",
                    "fStatus": "ENABLED",
                    "medSubComps": {
                        "1": {
                            "fNum": 1,
                            "fStatus": "ENABLED",
                            "fDescs": [f"permit out ip from any to {ue_ipv4} 8000"],
                        }
                    },
                }
            }
        }
    }


def patch_remove_body(med_comp_n: int = 2) -> dict:
    """PATCH removing a media component via fStatus=REMOVED [TS 29.514 §5.6.2.9]."""
    return {
        "ascReqData": {
            "medComponents": {
                str(med_comp_n): {"medCompN": med_comp_n, "fStatus": "REMOVED"}
            }
        }
    }


# ===========================================================================
# CREATE -- POST /app-sessions [TS 29.514 §4.2.2]
# ===========================================================================


def create_app_session(
    report: TestReport | None = None,
    ue_ipv4: str | None = None,
    af_app_id: str = "pa-test-create",
) -> tuple[str | None, Response]:
    """POST a guaranteed-video app session. Returns (app_session_id, Response).

    app_session_id is None if the create failed (no Location header) so
    callers can bail out cleanly instead of chaining onto a bad id.
    """
    own_report = report or TestReport("create_app_session")
    body = guaranteed_video_request_body(ue_ipv4=ue_ipv4, af_app_id=af_app_id)

    resp = curl_request("POST", content_type="application/json", body=body)

    own_report.check_eq("POST returns 201 Created", 201, resp.status)
    location = resp.header("location") or ""
    own_report.check("Location header is present", bool(location), f"got: {location!r}")

    data = resp.json() or {}
    resp_data = data.get("ascRespData", {})
    own_report.check_in("ascRespData.suppFeat is present", "suppFeat", resp_data)

    app_session_id = app_session_id_from_location(location) if location else None
    if report is None:
        own_report.summary()
    return app_session_id, resp


# ===========================================================================
# GET -- GET /app-sessions/{appSessionId} [TS 29.514 §4.2.5]
# ===========================================================================


def get_app_session(
    app_session_id: str, report: TestReport | None = None, expect_status: int = 200
) -> Response:
    """GET the app session context. Returns the Response."""
    own_report = report or TestReport("get_app_session")
    resp = curl_request("GET", path=f"/{app_session_id}")

    own_report.check_eq(
        f"GET /app-sessions/{app_session_id} returns {expect_status}", expect_status, resp.status
    )
    if expect_status == 200:
        data = resp.json() or {}
        own_report.check_in("response has ascReqData", "ascReqData", data)
        own_report.check_in("response has ascRespData", "ascRespData", data)

    if report is None:
        own_report.summary()
    return resp


# ===========================================================================
# PATCH -- PATCH /app-sessions/{appSessionId} [TS 29.514 §4.2.3]
# ===========================================================================

MERGE_PATCH_CONTENT_TYPE = "application/merge-patch+json"


def _patch(app_session_id: str, body: dict) -> Response:
    return curl_request(
        "PATCH",
        path=f"/{app_session_id}",
        content_type=MERGE_PATCH_CONTENT_TYPE,
        body=body,
    )


def patch_modify(app_session_id: str, report: TestReport | None = None) -> Response:
    """Modify component 1 in place (new bandwidth/latency, same qosId/pccRuleId)."""
    own_report = report or TestReport("patch_modify")
    resp = _patch(app_session_id, patch_modify_body())

    own_report.check_eq("PATCH modify returns 200", 200, resp.status)
    data = resp.json() or {}
    comp1 = data.get("ascReqData", {}).get("medComponents", {}).get("1", {})
    own_report.check_eq("component 1 marBwDl updated to 10 Mbps", "10 Mbps", comp1.get("marBwDl"))
    own_report.check_eq("component 1 mirBwDl updated to 8 Mbps", "8 Mbps", comp1.get("mirBwDl"))

    if report is None:
        own_report.summary()
    return resp


def patch_add(app_session_id: str, report: TestReport | None = None) -> Response:
    """Add a new media component (medCompN 2) alongside the existing one(s)."""
    own_report = report or TestReport("patch_add")
    resp = _patch(app_session_id, patch_add_body())

    own_report.check_eq("PATCH add returns 200", 200, resp.status)
    data = resp.json() or {}
    components = data.get("ascReqData", {}).get("medComponents", {})
    own_report.check_in("component 2 was added", "2", components)
    if "2" in components:
        own_report.check_eq("component 2 marBwDl is 5 Mbps", "5 Mbps", components["2"].get("marBwDl"))

    if report is None:
        own_report.summary()
    return resp


def patch_remove(
    app_session_id: str, report: TestReport | None = None, med_comp_n: int = 2
) -> Response:
    """Remove a media component via fStatus=REMOVED."""
    own_report = report or TestReport("patch_remove")
    resp = _patch(app_session_id, patch_remove_body(med_comp_n))

    own_report.check_eq("PATCH remove returns 200", 200, resp.status)
    data = resp.json() or {}
    components = data.get("ascReqData", {}).get("medComponents", {})
    own_report.check_not_in(f"component {med_comp_n} was removed", str(med_comp_n), components)

    if report is None:
        own_report.summary()
    return resp


def patch_reject(app_session_id: str, report: TestReport | None = None) -> Response:
    """A deliberately invalid PATCH: uplink GBR requested with no matching
    uplink SDF filter -- must be rejected 403 INVALID_SERVICE_INFORMATION
    and must leave the session's stored context untouched."""
    own_report = report or TestReport("patch_reject")

    before = get_app_session(app_session_id).json()

    resp = _patch(app_session_id, patch_modify_body(uplink_filter=False))

    own_report.check_eq("invalid PATCH returns 403", 403, resp.status)
    data = resp.json() or {}
    own_report.check_eq(
        "cause is INVALID_SERVICE_INFORMATION", "INVALID_SERVICE_INFORMATION", data.get("cause")
    )

    after = get_app_session(app_session_id).json()
    own_report.check_eq("session is left untouched by the rejected PATCH", before, after)

    if report is None:
        own_report.summary()
    return resp


PATCH_SCENARIOS = {
    "modify": patch_modify,
    "add": patch_add,
    "remove": patch_remove,
    "reject": patch_reject,
}


# ===========================================================================
# DELETE -- POST /app-sessions/{appSessionId}/delete [TS 29.514 §4.2.4]
# ===========================================================================


def delete_app_session(app_session_id: str, report: TestReport | None = None) -> Response:
    """Terminate the app session. Returns the Response.

    EventsSubscReqData is optional on terminate [TS 29.514 §4.2.4.2], so no
    body is sent here. Event-subscription coverage (a body carrying a real
    AfEventSubscription) is disabled until the notification service lands --
    see the TODO [QOS-SUB] in
    individual_application_session_context_document_api_handler.cpp."""
    own_report = report or TestReport("delete_app_session")
    resp = curl_request("POST", path=f"/{app_session_id}/delete")

    own_report.check_eq("DELETE returns 204 No Content", 204, resp.status)

    if report is None:
        own_report.summary()
    return resp


# ===========================================================================
# LIFECYCLE -- create -> get -> patch (modify/add/remove) -> reject -> delete
# ===========================================================================


def run_lifecycle() -> bool:
    """Runs every scenario above in sequence regardless of earlier failures,
    and reports one aggregate pass/fail count -- a single broken step
    doesn't hide problems in the rest of the sequence."""
    overall = TestReport("pa_lifecycle")

    step = TestReport("1. create")
    app_session_id, _ = create_app_session(step, af_app_id="pa-lifecycle-test")
    overall.merge(step)
    step.summary()
    if not app_session_id:
        print("\nAborting: create did not return an app session id.")
        overall.failed += 1
        overall.summary()
        return False

    step = TestReport("2. get (baseline)")
    get_app_session(app_session_id, step)
    overall.merge(step)
    step.summary()

    step = TestReport("3. patch modify")
    patch_modify(app_session_id, step)
    overall.merge(step)
    step.summary()

    step = TestReport("4. patch add")
    patch_add(app_session_id, step)
    overall.merge(step)
    step.summary()

    step = TestReport("5. patch remove")
    patch_remove(app_session_id, step)
    overall.merge(step)
    step.summary()

    step = TestReport("6. patch reject (invalid uplink GBR)")
    patch_reject(app_session_id, step)
    overall.merge(step)
    step.summary()

    step = TestReport("7. delete")
    delete_app_session(app_session_id, step)
    overall.merge(step)
    step.summary()

    step = TestReport("8. get after delete (expect 404)")
    get_app_session(app_session_id, step, expect_status=404)
    overall.merge(step)
    step.summary()

    print()
    return overall.summary()


# ===========================================================================
# CLI
# ===========================================================================


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="POST /app-sessions")
    p_create.add_argument("--ue-ipv4", default=UE_IPV4, help="UE IPv4 to bind (default: %(default)s)")
    p_create.add_argument("--af-app-id", default="pa-test-create")

    p_get = sub.add_parser("get", help="GET /app-sessions/{id}")
    p_get.add_argument("app_session_id")
    p_get.add_argument("--expect-status", type=int, default=200)

    p_patch = sub.add_parser("patch", help="PATCH /app-sessions/{id}")
    p_patch.add_argument("app_session_id")
    p_patch.add_argument("--scenario", choices=sorted(PATCH_SCENARIOS), required=True)

    p_delete = sub.add_parser("delete", help="POST /app-sessions/{id}/delete")
    p_delete.add_argument("app_session_id")

    sub.add_parser("lifecycle", help="run every scenario in sequence (CI entrypoint)")

    args = parser.parse_args()

    if args.command == "create":
        report = TestReport("create_app_session")
        app_session_id, _ = create_app_session(report, ue_ipv4=args.ue_ipv4, af_app_id=args.af_app_id)
        if app_session_id:
            print(f"app_session_id: {app_session_id}", file=sys.stderr)
        return 0 if report.summary() else 1

    if args.command == "get":
        report = TestReport("get_app_session")
        get_app_session(args.app_session_id, report, expect_status=args.expect_status)
        return 0 if report.summary() else 1

    if args.command == "patch":
        report = TestReport(f"patch_{args.scenario}")
        PATCH_SCENARIOS[args.scenario](args.app_session_id, report)
        return 0 if report.summary() else 1

    if args.command == "delete":
        report = TestReport("delete_app_session")
        delete_app_session(args.app_session_id, report)
        return 0 if report.summary() else 1

    if args.command == "lifecycle":
        return 0 if run_lifecycle() else 1

    parser.error(f"unknown command: {args.command}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
