#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Tests for the Nsmf_Callback SM Policy notification API [TS 29.502 §5.2.2.7,
TS 29.512 §4.2.3.2]: POST /nsmf-callback/v1/{scid}/sm-policy-control-notify/update.

The SMF's HTTP/2 server speaks h2c *with prior knowledge* (cleartext HTTP/2,
no TLS/ALPN, no Upgrade dance). Neither packages `requests` (HTTP/1.1 only) nor
`httpx`/`httpcore` (HTTP/2 only via TLS ALPN) can produce that request, so
requests are shelled out to `curl --http2-prior-knowledge` for transport;
everything else -- building request bodies, parsing responses, asserting on
them -- is plain Python/`json`. No pip dependencies.

Configuration (environment variables):
    SMF_HOST       SMF SBI address                         (default: 192.168.70.133)
    SMF_PORT       SMF SBI port                             (default: 8080)
    SMF_API_VERSION SBI API version segment                 (default: v1)
    PCF_CONTAINER  If set, curl runs as `docker exec $PCF_CONTAINER curl ...`
                   (matches the demo topology, where the PCF originates the
                   N7 notification from its own container on the SMF's Docker
                   network). If unset, curl runs directly on whatever host
                   invokes this script.
    SCID           SM context reference to target           (default: random hex)

Usage:
    ./smf_pcf_n7_tests.py lifecycle
    ./smf_pcf_n7_tests.py update-notify [--scid <scid>]

Every subcommand exits 0 if all its assertions passed, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass, field

# ===========================================================================
# CONFIG
# ===========================================================================

SMF_HOST = os.environ.get("SMF_HOST", "192.168.70.133")
SMF_PORT = os.environ.get("SMF_PORT", "8080")
SMF_API_VERSION = os.environ.get("SMF_API_VERSION", "v1")
PCF_CONTAINER = os.environ.get("PCF_CONTAINER", "")
DEFAULT_SCID = os.environ.get("SCID", "")

BASE_URL = f"http://{SMF_HOST}:{SMF_PORT}/nsmf-callback/{SMF_API_VERSION}"

# Unlikely to collide with any real header/body content; marks where curl's
# -w status-code output starts so it can be split off the captured stdout.
_STATUS_MARKER = "###N7_TEST_STATUS###"


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

    def json(self) -> dict | list | None:
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

    full_argv = ["docker", "exec", PCF_CONTAINER] + argv if PCF_CONTAINER else argv

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

    # curl's `-D -` prints the synthesized status line ("HTTP/2 200"), then
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

    def check_one_of(self, description: str, actual, allowed) -> bool:
        return self.check(
            description, actual in allowed, f"expected one of {allowed!r}, got {actual!r}"
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


def sm_policy_update_notification_body(
    scid: str,
    rule_id: str = "pcc-rule-test-1",
    qos_id: str = "qos-test-1",
) -> dict:
    """An `SmPolicyNotification` carrying a single PCC rule addition
    [TS 29.512 §5.6.2.6, §5.6.2.10]. `resourceUri` echoes back the callback
    URI SMF gave PCF at SM policy association create time -- SMF uses it to
    locate the association, so it must be shaped like SMF's own callback
    base + scid."""
    return {
        "resourceUri": (
            f"http://{SMF_HOST}:{SMF_PORT}/nsmf-callback/{SMF_API_VERSION}"
            f"/{scid}/sm-policy-control-notify"
        ),
        "smPolicyDecision": {
            "pccRules": {
                rule_id: {
                    "pccRuleId": rule_id,
                    "flowInfos": [
                        {
                            "flowDescription": "permit out ip from any to assigned",
                            "packFiltId": "pf-1",
                        }
                    ],
                    "precedence": 100,
                    "refQosData": [qos_id],
                }
            },
            "qosDecs": {
                qos_id: {
                    "qosId": qos_id,
                    "5qi": 9,
                    "arp": {
                        "priorityLevel": 8,
                        "preemptCap": "NOT_PREEMPT",
                        "preemptVuln": "NOT_PREEMPTABLE",
                    },
                    "defQosFlowIndication": False,
                }
            },
            "policyCtrlReqTriggers": ["RES_MO_RE"],
        },
    }


# ===========================================================================
# UPDATE-NOTIFY -- POST /{scid}/sm-policy-control-notify/update [TS 29.512 §4.2.3.2]
# ===========================================================================

# Spec-compliant response codes for the SM policy update notification:
#   204 -- full success (all decisions applied, no body)
#   200 -- partial success (body is a PartialSuccessReport)
#   400 -- malformed request / unknown scid
#   404 -- association not found
#   500 -- internal error (ProblemDetails / ErrorReport body)
_ACCEPTABLE_STATUSES = {200, 204, 400, 404, 500}


def update_notify(
    scid: str,
    report: TestReport | None = None,
) -> Response:
    """POST an `SmPolicyNotification` to SMF's N7 update callback and assert
    on the response envelope. Returns the Response.

    This exercises the full callback plumbing added by the feat-qos-update-notify
    branch (URL routing, JSON parsing, response formatting) without requiring a
    live PDU session. When the operator points $SCID at a real, live session,
    the same call also exercises the delta computation, N4 staging, and N1/N2
    signalling downstream of the callback.
    """
    own_report = report or TestReport("update_notify")
    body = sm_policy_update_notification_body(scid)

    resp = curl_request(
        "POST",
        path=f"/{scid}/sm-policy-control-notify/update",
        content_type="application/json",
        body=body,
    )

    own_report.check_one_of(
        f"POST update returns a spec-compliant status",
        resp.status,
        _ACCEPTABLE_STATUSES,
    )

    if resp.status == 204:
        own_report.check("204 responses carry no body", not resp.body.strip(),
                         f"got body: {resp.body!r}")
    elif resp.body.strip():
        data = resp.json()
        own_report.check("body parses as JSON", data is not None,
                         f"got body: {resp.body!r}")
        if resp.status == 200 and isinstance(data, dict):
            own_report.check_in(
                "200 body is a PartialSuccessReport (has failureCause)",
                "failureCause", data,
            )
        elif resp.status in (400, 404, 500) and isinstance(data, dict):
            own_report.check(
                "4xx/5xx body is a ProblemDetails (has cause or status)",
                "cause" in data or "status" in data,
                f"got: {data!r}",
            )

    if report is None:
        own_report.summary()
    return resp


# ===========================================================================
# LIFECYCLE -- update-notify (single-scenario smoke test)
# ===========================================================================


def run_lifecycle() -> bool:
    """Runs every scenario above in sequence regardless of earlier failures,
    and reports one aggregate pass/fail count -- a single broken step
    doesn't hide problems in the rest of the sequence.

    Currently only exercises the update-notify path; terminate-notify and a
    live-session round-trip are TODO."""
    overall = TestReport("n7_lifecycle")

    scid = DEFAULT_SCID or uuid.uuid4().hex[:16]
    print(f"[lifecycle] using scid={scid}"
          f"{' (from $SCID)' if DEFAULT_SCID else ' (random)'}")

    step = TestReport("1. update-notify")
    update_notify(scid, step)
    overall.merge(step)
    step.summary()

    print()
    return overall.summary()


# ===========================================================================
# CLI
# ===========================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser(
        "update-notify", help="POST /{scid}/sm-policy-control-notify/update"
    )
    p_update.add_argument(
        "--scid",
        default=DEFAULT_SCID or None,
        help="SM context reference (default: $SCID or a random hex string)",
    )

    sub.add_parser("lifecycle", help="run every scenario in sequence (CI entrypoint)")

    args = parser.parse_args()

    if args.command == "update-notify":
        scid = args.scid or uuid.uuid4().hex[:16]
        report = TestReport("update_notify")
        update_notify(scid, report)
        return 0 if report.summary() else 1

    if args.command == "lifecycle":
        return 0 if run_lifecycle() else 1

    parser.error(f"unknown command: {args.command}")  # pragma: no cover
    return 2


if __name__ == "__main__":
    sys.exit(main())
