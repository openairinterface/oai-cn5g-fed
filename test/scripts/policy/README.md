<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Policy-control HTTP/2 API test scripts

Two standalone, dependency-free Python scripts that assert on the OAI policy-control
SBI (cleartext HTTP/2, prior knowledge) via `curl`. They are driven by
[`../../policy_api_tests.robot`](../../policy_api_tests.robot), which deploys a core,
holds a live PDU session open with omec-gnbsim, and runs each script against it.

| Script | Drives | Standalone docs |
| --- | --- | --- |
| `smf_pcf_n7_tests.py` | SMF N7 SM-policy update callback [TS 29.512 §4.2.3.2] | [README-smf-n7.md](./README-smf-n7.md) |
| `pa_app_session_tests.py` | PCF N5 policy-authorization app-sessions [TS 29.514 §4.2] | [README-pcf-n5.md](./README-pcf-n5.md) |

Both are fully environment-variable driven (SBI host/port, the `docker exec` container
curl runs in, and — for the PCF script — the UE address, DNN, slice and qosReference the
app-session must line up with). The robot suite sets these to match the generated topology
and the omec session; the defaults documented in each script reproduce the standalone demo
topology so the scripts remain runnable by hand.

Run one by hand against an already-running core, e.g.:

```bash
PCF_CONTAINER=oai-pcf ./smf_pcf_n7_tests.py lifecycle
AF_CONTAINER=oai-af   ./pa_app_session_tests.py lifecycle
```
