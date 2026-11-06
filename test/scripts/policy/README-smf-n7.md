# N7 PCF-initiated PDU Session Modification test script

`smf_pcf_n7_tests.py` exercises the SMF's `Nsmf_Callback` policy notification
endpoint (`POST /nsmf-callback/v1/{scid}/sm-policy-control-notify/update`)
[TS 29.512 §4.2.3.2] against a live SMF over HTTP/2 prior-knowledge, via
`curl` (neither `requests` nor `httpx` can speak that transport). No pip
dependencies.

## Requirements

- `python3` 3.10+, `curl` built with HTTP/2 support
- A reachable SMF with a UE that has an established PDU session (the demo
  topology: `docker-compose-basic-nrf-qos.yaml` +
  `docker-compose-ueransim-qos.yaml` in `oai-cn5g-fed`)

## Quick start

```bash
PCF_CONTAINER=oai-pcf ./smf_pcf_n7_tests.py lifecycle
```

Runs three scenarios against the SMF's N7 callback endpoint, in order, with
one aggregate pass/fail exit code:

1. **update-notify** -- POSTs a well-formed `SmPolicyNotification` and
   asserts on the response (204 full-success / 200 partial-success / 4xx-5xx
   with `ProblemDetails`).
2. **terminate-notify** -- POSTs a `TerminationNotification` and asserts the
   handler answers 204 immediately, with no body. Run after update-notify
   since, against a live scid, it actually releases the SM Policy
   Association.
3. **update-notify, malformed body** -- POSTs unparseable JSON to the update
   endpoint and asserts it is rejected with a bare 400, exercising the
   JSON-parsing error path independently of session state.

For individual subcommands, their options, and the
`SMF_HOST`/`SMF_PORT`/`SMF_API_VERSION`/`PCF_CONTAINER` environment
variables, see `./smf_pcf_n7_tests.py --help` or the module docstring at the
top of the script.
