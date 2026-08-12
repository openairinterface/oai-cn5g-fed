<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Robot test suite

In CI we use the [Robot Framework](https://robotframework.org/) to test functionality of the core
network functions. Each suite generates its own `docker-compose` file and NF configuration from the
templates in `template/`, brings the core up, drives traffic through it, and tears everything down.

| Suite | What it deploys | What it checks |
| ----- | --------------- | -------------- |
| `all_nfs.robot` | Full NRF-based CN + PCF, HTTP/1.1, one gnbsim | UE attaches and pings the ext-DN |
| `smf_tests.robot` | SMF alone, no RAN | SMF configuration REST API (`GET`/`PUT`) |
| `qos_tests.robot` | CN + PCF + 3 ext-DNs, gnbsim | UPF throughput, session-AMBR and QoS-flow enforcement |
| `ebpf_tests.robot` | CN with the eBPF-datapath UPF | Attach, ping and 400 Mbit/s bidirectional iperf3 |
| `Northbound.robot` | CN + VPP-UPF + rfsim gNB/UEs + mobsim + MongoDB | AMF/SMF event-exposure notifications (see [prerequisites](#northbound-only)) |

## Prerequisites

### Python

```bash
# preferably in a virtual environment
pip install -r requirements.txt
```

### tshark

Every suite captures a `.pcapng` alongside its logs.

```bash
sudo apt install tshark
sudo usermod -aG wireshark $USER   # then log out and back in
```

The group membership matters. `tshark` is started with its stderr discarded, so without permission to
run `dumpcap` the tests still pass but every capture is silently empty. Check with `tshark -D`.

### Docker

- The Docker daemon must be usable **without `sudo`** (the tests talk to `/var/run/docker.sock` directly).
- The subnets `192.168.79.128/25`, `192.168.80.128/25` and `192.168.81.128/25` must be free, and no
  existing containers may be named `oai-*`, `mysql`, `gnbsim-*` or `trace_dummy`.
- For `Northbound.robot`, host port `27017` must be free (the suite starts its own MongoDB container).

### Images

Image tags are listed in `image_tags.py` — edit that file to test a specific build. CI rewrites it with
`sed`, so keep the entries whitespace-free.

Most images are pulled from Docker Hub, but **`gnbsim` is not published under that name**:

```bash
docker pull rohankharade/gnbsim:latest
docker image tag rohankharade/gnbsim:latest gnbsim:latest
```

### Northbound only [Currently not public it will be public soon]

`Northbound.robot` additionally needs the `5gcsdk` repository checked out into `test/5gcsdk`. It is not a
submodule; CI clones it at build time.

```bash
git clone -b oai-jenkins-ci https://github.com/openairinterface/5gcsdk.git test/5gcsdk
```

## Running

Run from the **repository root** — generated artifacts are written relative to your working directory.

```bash
# list the tests that would run, without deploying anything
robot --dryrun test

# run everything
robot --outputdir archives test

# run a single suite
robot --outputdir archives test/all_nfs.robot

# run only the tests tagged for one NF, as CI does when an upstream job triggers
robot -i UPF --outputdir archives test
```

Available tags: `AMF`, `SMF`, `UPF`, `NRF`, `UDM`, `UDR`, `AUSF`, `PCF`, `North`.

## Output

`--outputdir` receives Robot's own `log.html`, `report.html` and `output.xml`. Everything a suite
generates goes to `archives/robot_framework/<Suite Name>/`:

```
archives/robot_framework/All Nfs/
  docker-compose-nrf-cn-pcf.yaml   # generated from template/, unused NFs stripped
  conf-nrf-cn-pcf.yaml             # generated NF config, mounted into every NF
  logs/                            # one file per container
  mysql/                           # subscriber database, copied from template/
  policies/                        # PCF policies, copied from template/ (when PCF is deployed)
  core_network.pcapng              # tshark capture, one per suite plus one per test
```

The suite documentation in `report.html` is appended at teardown with a table of the image tag, build
date and size actually used for each container — check there first when a result looks surprising.

Teardown also asserts that every NF logged `Bye.` on shutdown; a container that was killed instead of
exiting cleanly is reported as an `ERROR` in the log.

## Troubleshooting

**A container never becomes healthy.** `Check Core Network Health Status` polls for 60s and then fails
naming the unhealthy containers. Look at `logs/<container>` in the suite's artifact directory — the NF
usually logged a configuration error and exited.

**Empty `.pcapng` files.** Missing `wireshark` group membership; see above.

**Northbound: `UE ... not found in handler collection`.** The notification handler did not subscribe.
Check `test/5gcsdk/etc/handler_status.yaml`: if it reads `handler_status: 'on'` while no handler process
is alive, it is stale and blocks the next start. Reset it with
`git -C test/5gcsdk checkout -- etc/handler_status.yaml`. Confirm the AMF actually reached the handler by
grepping its log for the notification URI: `grep 1112 archives/robot_framework/Northbound/logs/oai-amf`.

**Leftover state between runs.** A suite that was interrupted can leave containers and networks behind:

```bash
docker ps -a --filter name=oai- --filter name=gnbsim- -q | xargs -r docker rm -f
docker network rm test-oai-public-net test-oai-n3-net test-oai-n6-net 2>/dev/null
```
