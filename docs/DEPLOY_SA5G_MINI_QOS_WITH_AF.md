<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">QoS on Demand on a minimal OAI 5G Core, with a simple-switch UPF and an external AF</font></b>
    </td>
  </tr>
</table>

**Reading time: ~ 10 mins**

**Tutorial replication time: ~ 20 mins**

**TABLE OF CONTENTS**

1. [What this tutorial checks](#1-what-this-tutorial-checks)
2. [Prerequisites](#2-prerequisites)
3. [Architecture](#3-architecture)
4. [Deploy the core network](#4-deploy-the-core-network)
5. [Deploy the RAN](#5-deploy-the-ran)
6. [Measure the baseline](#6-measure-the-baseline)
7. [Ask for QoS through the AF](#7-ask-for-qos-through-the-af)
8. [Release the QoS session](#8-release-the-qos-session)
9. [Results](#9-results)
10. [Undeploy](#10-undeploy)

-----------------------------------------------------------------------------

# 1. What this tutorial checks

The [QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md) runs a full core (NRF, UDR, UDM,
AUSF, ...) with the **eBPF/XDP** UPF datapath, and drives the N5 interface with
`curl`. This tutorial is a deliberately small counterpart that answers three
questions at once:

1. Does **QoS enforcement work in the UPF's simple-switch datapath**, not just
   in the eBPF one?
2. Does it work on a **minimal core** -- AMF, SMF, PCF, UPF and nothing else?
3. Does it work when the QoS is requested by a **real external AF**
   ([phine.af](https://github.com/phinetech/phine.af)) through its CAMARA
   Quality-on-Demand API, rather than by a hand-written `curl` call?

Everything runs on `develop` images. The RAN is the OAI gNB and OAI NR-UE in
RF simulator mode.

The short answer to all three is **yes** -- see [section 9](#9-results).

# 2. Prerequisites

Docker with the Compose v2 plugin, and roughly 4 GB of free RAM. Nothing else
should be using the `192.168.70.128/26` subnet.

Pull the images:

``` shell
docker-compose-host $: docker pull oaisoftwarealliance/oai-amf:develop
docker-compose-host $: docker pull oaisoftwarealliance/oai-smf:develop
docker-compose-host $: docker pull oaisoftwarealliance/oai-upf:develop
docker-compose-host $: docker pull oaisoftwarealliance/oai-pcf:develop
docker-compose-host $: docker pull oaisoftwarealliance/oai-gnb:develop
docker-compose-host $: docker pull oaisoftwarealliance/oai-nr-ue:develop
docker-compose-host $: docker pull oaisoftwarealliance/trf-gen-cn5g:latest
docker-compose-host $: docker pull phinetech/phine.af:develop
```

To build the AF image yourself instead of pulling it:

``` shell
phine.af-host $: git clone https://github.com/phinetech/phine.af
phine.af-host $: cd phine.af && docker build -t phinetech/phine.af:develop .
```

# 3. Architecture

```
  CAMARA QoD REST (h2c)        N5                   N7                N4
 client ------------> phine.af ---> oai-pcf ---> oai-smf ---> oai-upf (simple switch)
                                       ^                           |
                                       | local policy files        | N3 (GTP-U)
                                       |                           |
                                  policies/mini-qos-af       oai-gnb-basic <-rfsim-> oai-nr-ue-basic
                                                                   |
                                                              oai-ext-dn (N6)
```

There is **no NRF, UDR, UDM or AUSF container**:

* The AMF authenticates the UE with its internal AUSF/UDM
  (`amf.support_features_options.enable_simple_scenario: yes`), reading the
  subscriber key from the legacy `users` table in
  [database/oai_db1.sql](../docker-compose/database/oai_db1.sql). MySQL is the
  only reason a fifth core container exists.
* The SMF takes the PCF from the static `nfs:` section. It would do that even
  with an NRF present: `discover_pcf` is hardcoded to `false` in the SMF
  (`src/smf_app/smf_config.cpp`), which logs *"PCF NRF discovery not
  supported. Using the provided values"*.
* The SMF takes the subscription data from `local_subscription_infos`
  (`use_local_subscription_info: yes`) but the **PCC rules from the PCF**
  (`use_local_pcc_rules: no`) -- that is what makes the AF able to change them
  at runtime.

The relevant UPF settings in
[conf/mini_qos_config.yaml](../docker-compose/conf/mini_qos_config.yaml):

```yaml
upf:
  support_features:
    enable_bpf_datapath: no   # simple switch, the point of this tutorial
    enable_qos: yes
  datapath_configuration:
    qos_shape_ms: 50          # shape the downlink rather than police it
```

`qos_shape_ms` is worth a word. With the default (`0`) the simple-switch
datapath *polices* the downlink: it forgives a `qos_burst_ms` burst (400 ms by
default) and drops the rest, which makes a TCP iperf3 run sawtooth around the
limit. A non-zero value makes it *shape* instead -- excess packets are queued
for up to that many milliseconds -- and the measured rate settles close to the
configured MBR.

# 4. Deploy the core network

``` shell
docker-compose-host $: cd docker-compose
docker-compose-host $: docker compose -f docker-compose-mini-qos-af.yaml up -d mysql oai-amf oai-smf oai-upf oai-pcf oai-ext-dn phine-af
```

Check that the UPF really came up on the simple-switch datapath with QoS on:

``` shell
docker-compose-host $: docker logs oai-upf 2>&1 | grep -E "Enable BPF Datapath|Enable QoS|qos_shape_ms"
```

<details>
<summary>Expected output</summary>

```
[config ] [info] Datapath configuration transferred: ..., qos_burst_ms=400, qos_shape_ms=50, qos_shape_ul_ms=0
[config ] [info]     + Enable BPF Datapath......................: No
[config ] [info]     + Enable QoS Enforcement  (QER)............: Yes
```
</details>

And that the PCF loaded the local policy:

``` shell
docker-compose-host $: docker logs oai-pcf 2>&1 | grep -E "QoS reference set|Loaded PCC rule|HTTP2 server"
```

# 5. Deploy the RAN

Start the gNB first, then the UE:

The RAN is the repository's existing rfsim pair, so there is nothing scenario
specific to configure:

``` shell
docker-compose-host $: docker compose -f docker-compose-oai-rfsim-basic.yaml up -d
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-nr-ue-basic)" = "healthy" ]; do sleep 2; done'
```

[docker-compose-oai-rfsim-basic.yaml](../docker-compose/docker-compose-oai-rfsim-basic.yaml)
joins the `demo-oai-public-net` the core created, so it has to come up after
section 5. It brings `oai-gnb-basic` and `oai-nr-ue-basic` with
[ran-conf/gnb.conf](../docker-compose/ran-conf/gnb.conf) and
[ran-conf/nr-ue.conf](../docker-compose/ran-conf/nr-ue.conf): the gNB expects
the AMF at `192.168.70.138`, and the UE uses IMSI `208950000000036` on DNN
`oai`, which is why the core config places the AMF there and names its DNN
`oai`.

Confirm the UE has an IP and can reach the data network:

``` shell
docker-compose-host $: docker exec oai-nr-ue-basic ip -4 addr show oaitun_ue1
docker-compose-host $: docker exec oai-nr-ue-basic ping -c 3 -I oaitun_ue1 192.168.70.135
```

The UE gets `12.1.1.2`, the first address of the `oai` DNN pool. The rest
of this tutorial uses that address; adjust it if yours differs.

# 6. Measure the baseline

The UPF shapes the downlink, so the iperf3 *server* runs on the UE and the
*client* in `oai-ext-dn`:

Two ports are measured throughout: **5000**, which the AF request below
names, and **5001**, which it does not. The second one is the control -- a
correctly scoped rule must leave it alone.

``` shell
docker-compose-host $: docker exec -d oai-nr-ue-basic iperf3 -s -B 12.1.1.2 -p 5000
docker-compose-host $: docker exec -d oai-nr-ue-basic iperf3 -s -B 12.1.1.2 -p 5001
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 6 -O 1 -c 12.1.1.2 -p 5000 -B 192.168.70.135
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 6 -O 1 -c 12.1.1.2 -p 5001 -B 192.168.70.135
```

`-O 1` discards the first second so TCP slow start is not counted. On the run
this tutorial was written from, the baseline was **87.4 Mbps** on port 5000
and **91.7 Mbps** on port 5001: the only policy limit in force is the 100 Mbps
session AMBR from `local_subscription_infos`, and the RF simulator carries the
rest. The numbers vary between runs; what matters is that both are far above
the 10 Mbps the AF is about to ask for.

# 7. Ask for QoS through the AF

phine.af exposes the CAMARA Quality-on-Demand API. Its `premium` profile maps
to 5QI 7 with a 10 Mbps maximum and 5 Mbps guaranteed rate in each direction.
Create a session for the UE's IP and its port 5000:

``` shell
docker-compose-host $: curl -i --http2-prior-knowledge -X POST \
    -H 'Content-Type: application/json' \
    -d '{"device":{"ipv4Address":{"publicAddress":"12.1.1.2","publicPort":5000}},"applicationServer":{"ipv4Address":"0.0.0.0/0"},"devicePorts":{"ports":[5000]},"qosProfile":"premium","duration":3600}' \
    http://192.168.70.141:8080/quality-on-demand/v1/sessions
```

The AF Core speaks HTTP/2 cleartext without an upgrade handshake, hence
`--http2-prior-knowledge`.

A successful response carries `"qosStatus":"REQUESTED"` and a `sessionId`.
Keep that id:

``` shell
docker-compose-host $: QOD_SESSION_ID=<sessionId from the response>
```

> If you get `"qosStatus":"UNAVAILABLE"` with
> `"statusInfo":"NETWORK_TERMINATED"`, the AF reached the PCF but the PCF
> refused the request. `docker logs phine-af` prints the PCF's status code and
> problem details, and `docker logs oai-pcf` explains the decision.

Behind that single REST call, phine.af built an `Npcf_PolicyAuthorization`
app-session and posted it to the PCF, which derived a PCC rule and a QosData
entry, pushed them to the SMF over N7, and the SMF installed the matching
PDR/QER on the UPF over N4. You can see the whole chain:

``` shell
docker-compose-host $: docker logs oai-pcf 2>&1 | grep -E "POST /app-sessions|Deriving QoS|Created QosData"
docker-compose-host $: docker logs oai-upf 2>&1 | grep -E "QoS/MBR"
```

<details>
<summary>The UPF shows the new flow's MBR next to the default one</summary>

```
[pfcp_switch] [debug] QoS/MBR: seid 0x1 PDR 2 downlink: flow 100000000 bps, session 0 bps
[pfcp_switch] [debug] QoS/MBR: seid 0x1 PDR 4 downlink: flow 10000000 bps, session 0 bps
```
</details>

Measure again, both the named port and the control:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 6 -O 1 -c 12.1.1.2 -p 5000 -B 192.168.70.135
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 6 -O 1 -c 12.1.1.2 -p 5001 -B 192.168.70.135
```

Port 5000 settles just under **10 Mbps**, the MBR of the `premium` profile.
Port 5001 is untouched -- **92.5 Mbps** against a 91.7 Mbps baseline on the
run this was written from. The rule is enforced at the requested rate *and*
scoped to the flow the AF described, which is the result this scenario is
checking.

# 8. Release the QoS session

``` shell
docker-compose-host $: curl -i --http2-prior-knowledge -X DELETE \
    http://192.168.70.141:8080/quality-on-demand/v1/sessions/$QOD_SESSION_ID
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 6 -O 1 -c 12.1.1.2 -p 5000 -B 192.168.70.135
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 6 -O 1 -c 12.1.1.2 -p 5001 -B 192.168.70.135
```

The AF answers `200 OK`. It terminates the app-session on the PCF, the PCF
removes the AF-derived PCC rule, the SMF removes the QER from the UPF, and
both ports return to the baseline from section 6 (90.8 and 92.4 Mbps on the
run this tutorial was written from).

# 9. Results

What this scenario demonstrates:

* **Simple-switch QoS works, and is scoped to the described flow.** The UPF
  enforces an AF-requested downlink MBR without the eBPF datapath. A clean
  deployment measured 87.4 Mbps baseline -> 9.53 Mbps with the AF's 10 Mbps
  `premium` profile -> 90.8 Mbps after the QoD session was deleted, while an
  untargeted port stayed above 90 Mbps throughout.
* **A minimal core is enough.** AMF + SMF + PCF + UPF (+ MySQL for the AMF's
  internal UDM) carries the full N5 -> N7 -> N4 chain. No NRF is involved.
* **OAI RAN works.** The OAI gNB and NR-UE attach, get a PDU session, and keep
  working in both directions after a second QoS flow is installed.

### 9.1 Smaller things

* The PCC rule precedence polarity is easy to get backwards: **lower wins**
  (TS 29.244 clause 8.2.11). A static catch-all rule must use a value *above*
  the PCF's AF band (`PA_QOS_PRECEDENCE_BASE` = 1000, band 1000-1999), or it
  outranks every AF rule and nothing appears to happen. The rule in
  [policies/mini-qos-af/pcc_rules](../docker-compose/policies/mini-qos-af/pcc_rules/pcc_rules.yaml)
  uses 10000 for that reason.
* phine.af sends the bare 5QI as `qosReference` (`"7"` for `premium`). OAI
  expects a named operator preset there, so it does not resolve, and the PCF
  logs a warning and derives the QoS from the bitrates in the request
  instead. That is the behaviour this tutorial relies on; defining a preset
  named `7` in
  [policies/qos_references](../docker-compose/policies/qos_references/) would
  override the AF's rates with the operator's.
* The PCF aborts at startup if a directory under `pcf.local_policy.*_path`
  contains a comment-only YAML file: it converts to `~`, and the JSON parser
  rejects it with `parse_error.101`.
* phine.af hardcodes its `notifUri` to `http://phine.af-core:50051/...`. The
  compose file gives the AF container a `phine.af-core` network alias so the
  PCF can at least resolve the name.

# 10. Undeploy

``` shell
docker-compose-host $: docker compose -f docker-compose-oai-rfsim-basic.yaml down -t 5
docker-compose-host $: docker compose -f docker-compose-mini-qos-af.yaml down -t 5
```
