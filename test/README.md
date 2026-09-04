<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Robot test suite

Each suite generates its own `docker-compose` file and NF configuration from the templates in
`template/`, brings the core up, drives traffic through it, and tears everything down.

Currently the test suite is only supported on Ubuntu (22.04/24.04/26.04) distribution.

## Suites

| Suite | What it deploys | What it checks |
| ----- | --------------- | -------------- |
| [all_nfs.robot](./all_nfs.robot) | Full NRF-based CN + PCF, one gnbsim | UE attaches and pings the ext-DN |
| [smf_tests.robot](./smf_tests.robot) | SMF alone, no RAN | SMF configuration REST API (`GET`/`PUT`) |
| [smf_upf_tests.robot](./smf_upf_tests.robot) | SMF + UPF, with and without NRF | PFCP association, SMF- and UPF-initiated |
| [qos_tests.robot](./qos_tests.robot) | CN + PCF + 3 ext-DNs, gnbsim | UPF throughput, session-AMBR, QoS-flow enforcement |
| [ebpf_tests.robot](./ebpf_tests.robot) | CN with the eBPF-datapath UPF | Attach, ping, 400 Mbit/s bidirectional iperf3 |
| [omec_gnbsim_tests.robot](./omec_gnbsim_tests.robot) | CN + omec-gnbsim | UE lifecycle, idle cycle, release and re-establish, address-leak check |
| [packetrusher_tests.robot](./packetrusher_tests.robot) | CN + PacketRusher | N2/Xn handover, paging, UPF throughput, multi-UE attach |
| [Northbound.robot](./Northbound.robot) | CN + VPP-UPF + rfsim gNB/UEs + mobsim + MongoDB | AMF/SMF event-exposure notifications |

### Test cases per RAN suite

| `omec_gnbsim_tests.robot` | Flow |
| --- | --- |
| Full UE Lifecycle Single UE | register → PDU session → 4 ICMP → session release → deregister |
| Multiple UE test | the same, all UEs started at once |
| Idle Cycle Single UE | AN release → service request → ICMP again |
| Release And Re-establish PDU Session Single UE | release, then a second session on the same registration |
| Repeated Lifecycle Leak Check | Check if the lifecycle test passes N times against a core deployed once |

| `packetrusher_tests.robot` | Mandatory |
| --- | --- |
| N2 Handover Between Two gNBs | yes |
| Xn Handover Between Two gNBs | no — the core has no Xn support |
| Paging Of An Idle UE | no — paging support is still being added |
| Idle Cycle Single UE | yes |
| UPF Throughput Single UE | yes |
| Multi UE Registration And Deregistration | yes |

Non-mandatory tests are wrapped so an expected failure is logged as an `ERROR` instead of failing the
suite. They start passing on their own once the core gains support.

ICMP is reply driven everywhere, so a ping step only passes if the echo replies come back.

## Prerequisites

### 1. Python

```bash
sudo apt install python3 python3-venv python3-pip
python3 -m venv .rfvenv
.rfvenv/bin/pip install -r test/requirements.txt
```

### 2. Docker

- The daemon must be usable **without `sudo`** (the tests talk to `/var/run/docker.sock` directly).
- The subnets `192.168.79.128/25`, `192.168.80.128/25` and `192.168.81.128/25` must be free.
- No existing containers named `oai-*`, `mysql`, `gnbsim-*`, `omec-gnbsim-*`, `packetrusher-*` or
  `trace_dummy`.
- `Northbound.robot` also needs host port `27017` free (it starts its own MongoDB).

### 3. Images

Tags live in [image_tags.py](./image_tags.py) — edit that file to test a specific build. 
CI rewrites it with `sed`, so keep the entries whitespace-free.

All images are pulled from Docker Hub.

### 4. tshark, for packet captures

```bash
# only for ubuntu/debian
sudo apt install tshark wireshark
sudo usermod -aG wireshark $USER    # then log out and back in
tshark -D                           # must list real interfaces
```

This matters: `tshark` runs with its stderr discarded, so without permission to run `dumpcap` the
tests still pass and **every capture is silently missing**. `/usr/bin/dumpcap` is
`root:wireshark`, mode `0754`, so group membership is the only thing that grants it.

To test that dumpcap works:

```bash
timeout 3s dumpcap -i any -w /tmp/test.pcap
```

### 5. gtp5g kernel module — PacketRusher only

PacketRusher is running inside the container
but it needs a kernel module on the host. 
It uses `--tunnel` argument which needs
free5gc's `gtp5g` module loaded on the **host**:

```bash
git clone https://github.com/HewlettPackard/PacketRusher.git test/PacketRusher
cd test/PacketRusher/lib/gtp5g && make clean && make
sudo make install
# If Secure Boot: sign with the enrolled MOK before loading
# this is only for debian/ubuntu host
sudo /usr/src/linux-headers-$(uname -r)/scripts/sign-file sha256 \
     /var/lib/shim-signed/mok/MOK.priv /var/lib/shim-signed/mok/MOK.der gtp5g.ko
# need to do it after every reboot
sudo insmod gtp5g.ko
```

The module is namespace aware, so the privileged container creates its GTP-U interface in its own
netns; host networking is not needed.

To remove the module:

```bash
cd test/PacketRusher/lib/gtp5g
sudo make uninstall 
or 
rmmode gtp5g.ko
```

### 6. Northbound only

Needs the `5gcsdk` repository checked out into `test/5gcsdk`. 
Not a submodule; CI clones it at build
time.

```bash
git clone https://github.com/openairinterface/5gcsdk.git test/5gcsdk
```

## Running

Run from the **repository root** — artifacts are written relative to your working directory.

```bash
# list what would run, deploying nothing
.rfvenv/bin/robot --dryrun test

# everything
.rfvenv/bin/robot --outputdir archives test

# one suite
.rfvenv/bin/robot --outputdir archives test/omec_gnbsim_tests.robot

# one test
.rfvenv/bin/robot --outputdir archives --test "Idle Cycle Single UE" test/omec_gnbsim_tests.robot

# only the tests tagged for one NF, as CI does
.rfvenv/bin/robot -i UPF --outputdir archives test
```

Tags: `AMF`, `SMF`, `UPF`, `NRF`, `UDM`, `UDR`, `AUSF`, `PCF`. `Northbound.robot` carries no tags,
so a tag-filtered run never selects it.

## Suite options

These are Robot variables, passed with `--variable NAME:value`. Not environment variables.

### `omec_gnbsim_tests.robot`

| Variable | Default | Purpose |
| --- | --- | --- |
| `SESSION_UE_COUNT` | `500` | UEs in the simultaneous lifecycle test |
| `UE_SUBNET` | `12.1.0.0/16` | DNN address pool; the ext-DN route and its healthcheck follow it |
| `LEAK_UE_COUNT` | `100` | UEs per iteration of the leak check |
| `TEST_ITERATIONS` | `3` | iterations of the leak check |
| `LEAK_PROFILE` | `lifecycle` | which gnbsim profile each iteration runs |
| `MAX_REG_MS` / `MAX_DEREG_MS` / `MAX_SERVICE_MS` | `5000` | latency ceilings, in ms |

`LEAK_PROFILE` takes any profile from `template/omec_gnbsim_template_config.yaml`:

| Profile | Sequence |
| --- | --- |
| `lifecycle` | register → PDU session → ICMP → **session release** → deregister |
| `dereg` | register → PDU session → ICMP → deregister, session still up |
| `relcycle` | release, then establish a **second** session before deregistering |
| `idlecycle` | + AN release → service request → ICMP again |

```bash
# Testing Multiple UEs, default 500 UEs
.rfvenv/bin/robot --outputdir archives --variable SESSION_UE_COUNT:80 \
  test/omec_gnbsim_tests.robot

# Testing address-leak: 100 UEs, 20 times, on a /24 so a leak exhausts the pool fast
.rfvenv/bin/robot --test "Repeated Lifecycle Leak Check" \
  --variable LEAK_UE_COUNT:100 --variable TEST_ITERATIONS:20 \
  --variable UE_SUBNET:12.1.0.0/24 \
  --outputdir archives test/omec_gnbsim_tests.robot
```

The leak check deploys the core **once** and never restarts it, so what matters is what the core keeps
between iterations: after every UE has deregistered the AMF statistics table must be empty. A `/24`
holds 254 addresses, so 100 UEs × 20 iterations is 2000 sessions through that pool — a leaked address
per session fails by iteration 3. Afterwards:

```bash
L="archives/robot_framework/Omec Gnbsim Tests/logs"
grep -ac "Resources associated with this PDU Session have been released" "$L/oai-smf"  # want 2000
grep -aoE "\b12\.1\.[0-9]+\.[0-9]+\b" "$L/oai-smf" | sort -u | wc -l                   # want ~100
grep -aic "could not get paa" "$L/oai-smf"                                             # want 0
```

### `packetrusher_tests.robot`

| Variable | Default | Purpose |
| --- | --- | --- |
| `SESSION_UE_COUNT` | `500` | UEs in the multi-UE test |
| `UE_SUBNET` | `12.1.0.0/16` | DNN address pool |
| `HANDOVER_RUN_TIME` | `30s` | how long a handover test runs |
| `SCALE_RUN_TIME` | `120s` | how long the multi-UE test runs |
| `HANDOVER_DELAY` | `30000` | ms before PacketRusher triggers the handover |
| `IDLE_DELAY` / `IDLE_RETURN_DELAY` | `15000` / `10000` | ms before going idle, and before coming back |
| `RECONNECT_DELAY` | `300000` | ms before reconnecting |
| `DEREG_DELAY` | `15000` | ms before deregistering |
| `PING_DURATION` / `PING_INTERVAL` | `45` / `0.1` | ping seconds and spacing, across a handover |
| `MAX_INTERRUPTION_MS` | `5000` | longest user-plane gap a handover may cause |
| `IPERF_DURATION` | `10` | iperf3 seconds in the throughput test |
| `MIN_THROUGHPUT_MBPS` | `50` | throughput floor; the simple-switch datapath measures ~400–600 |

```bash
.rfvenv/bin/robot --outputdir archives test/packetrusher_tests.robot
.rfvenv/bin/robot --outputdir archives --test "UPF Throughput*" test/packetrusher_tests.robot
```

## Metrics

Per-procedure latencies come from **gnbsim only**. It timestamps NAS and NGAP transitions per SUPI and
reports registration, PDU session establishment, service request, UE context release and deregistration
in microseconds, with a per-leg breakdown of the registration handshake.

After a gnbsim run they appear in three places:

- the suite documentation at the top of `archives/report.html`, as min/p50/p95/max per test and metric
- the same table in the Robot log
- `archives/robot_framework/Omec Gnbsim Tests/gnbsim_metrics.csv`

Metrics are recorded per test in the teardown, so a filtered run reports only the tests that ran, and a
test that failed part way still contributes what it measured.

**PacketRusher reports no latencies.** It has no instrumentation and no per-UE completion timestamps.
It writes a pcap per test to `archives/robot_framework/Packetrusher Tests/pcap-<test>/` for debugging,
but no timings are derived from it: NAS is ciphered, and PacketRusher batches many NGAP messages into a
single SCTP frame, so per-UE request/response pairing is unreliable. Use gnbsim when you need numbers.

## Output

`--outputdir` receives Robot's own `log.html`, `report.html` and `output.xml`. Everything a suite
generates goes to `archives/robot_framework/<Suite Name>/`:

```
docker-compose-*.yaml   # generated from template/, unused NFs stripped
conf-*.yaml             # generated NF config, mounted into every NF
logs/                   # one file per container
mysql/                  # subscriber database, copied from template/
policies/               # PCF policies, when a PCF is deployed
*.pcapng                # one capture per suite plus one per test
```

The suite documentation in `report.html` is appended at teardown with the image tag, build date and
size actually used for each container — check there first when a result looks surprising.

Teardown also asserts every NF logged `Bye.` on shutdown; a container that was killed instead of
exiting cleanly is reported as an `ERROR`.

Container logs are binary, so use `grep -a` on them.

## Troubleshooting

**A container never becomes healthy.** `Check Core Network Health Status` polls for 60s then fails,
naming the unhealthy containers. Look at `logs/<container>` — the NF usually logged a configuration
error and exited.

**Missing `.pcapng` files.** Not in the `wireshark` group; see the tshark prerequisite.

**`No gnbsim metrics for '<test>': 404 ... No such container`.** The leak check removes its container
each iteration, so the test teardown finds nothing left to read. Harmless.

**Northbound: `UE ... not found in handler collection`.** The notification handler did not subscribe.
Check `test/5gcsdk/etc/handler_status.yaml`: if it reads `handler_status: 'on'` while no handler process
is alive, it is stale and blocks the next start. Reset it with
`git -C test/5gcsdk checkout -- etc/handler_status.yaml`. Confirm the AMF reached the handler with
`grep -a 1112 archives/robot_framework/Northbound/logs/oai-amf`.

**Leftover state after an interrupted run.**

```bash
docker ps -a --filter name=oai- --filter name=gnbsim- --filter name=omec-gnbsim- \
  --filter name=packetrusher- -q | xargs -r docker rm -f
docker network rm test-oai-public-net test-oai-n3-net test-oai-n6-net 2>/dev/null
```
