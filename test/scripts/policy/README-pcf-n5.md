# N5 Policy Authorization app-session test script

`pa_app_session_tests.py` exercises the `Npcf_PolicyAuthorization`
app-sessions API (`POST`/`GET`/`PATCH`/`DELETE`) [TS 29.514 §4.2] against a
live PCF over HTTP/2 prior-knowledge, via `curl` (neither `requests` nor
`httpx` can speak that transport). No pip dependencies.

## Requirements

- `python3` 3.10+, `curl` built with HTTP/2 support
- A reachable PCF with a UE that has an established PDU session (the demo
  topology: `docker-compose-basic-nrf-qos.yaml` +
  `docker-compose-ueransim-qos.yaml` in `oai-cn5g-fed`)

## Quick start

```bash
AF_CONTAINER=oai-af ./pa_app_session_tests.py lifecycle
```

Runs create → get → patch (modify/add/remove) → reject-case → delete → get,
with one pass/fail exit code for the whole sequence.

For individual `create`/`get`/`patch`/`delete` subcommands, their options,
and the `PCF_HOST`/`PCF_PORT`/`AF_CONTAINER`/`UE_IPV4` environment variables,
see `./pa_app_session_tests.py --help` or the module docstring at the top of
the script.
