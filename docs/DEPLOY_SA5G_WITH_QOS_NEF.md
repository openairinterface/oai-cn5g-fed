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
      <b><font size = "5">OpenAirInterface 5G Core Network QoS on Demand through the NEF</font></b>
    </td>
  </tr>
</table>


**Reading time: ~ 20mins**

**Tutorial replication time: ~ 1hs**


**TABLE OF CONTENTS**

1.  [Prerequisites](#1-prerequisites)
2.  [Architecture Overview](#2-architecture-overview)
3.  [Building the NEF Image](#3-building-the-nef-image)
4.  [Core Network Configuration](#4-core-network-configuration)
5.  [Network Function Deployment](#5-network-function-deployment)
6.  [Deploy UERANSIM](#6-deploy-ueransim)
7.  [Testing QoS on Demand through the NEF](#7-testing-qos-on-demand-through-the-nef)
8.  [Log Collection](#8-log-collection)
9.  [Undeploy the network functions](#9-undeploy-the-network-functions)
10. [Conclusion](#10-conclusion)

-----------------------------------------------------------------------------------------
# QoS on Demand through the NEF with OAI 5G Core Network

The [QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md) shows an Application Function asking the network for QoS at runtime by calling the PCF's `Npcf_PolicyAuthorization` service on **N5** directly. That works when the AF is part of the operator's trust domain, because N5 is an internal 5GC interface: the AF has to speak 3GPP SBI, know the PCF's address, and phrase its request in terms of `medComponents`, `medSubComps` and `fDescs`.

An AF outside that trust domain — a third-party application provider — is not supposed to reach the PCF at all. It goes through the **Network Exposure Function**, which publishes a northbound REST API (3GPP TS 29.122, the "T8" APIs) across **N33**, and translates each request into the right internal service call. For QoS on demand, the relevant resource is **AS Session with QoS** (TS 29.122 clause 4.4.13), which NEF maps onto exactly the same `Npcf_PolicyAuthorization` app-session the other tutorial creates by hand.

This tutorial walks the same QoS-on-demand lifecycle as [section 8 of the QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md#8-testing-qos-on-demand-n5-af-initiated-qos), but driven from the northbound side: create → verify by throughput → modify → delete, through the NEF. Everything below the NEF — the PCC rules, the `qosReference` presets, the SMF, the UPF enforcement — is unchanged, which is the point: the same policy machinery serves an internal AF on N5 and an external AF on N33.

## 1. Prerequisites

This tutorial assumes you have already run the [QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md), or at least read sections 3 to 5 of it: the subscriber database, the PCC rules, the QoS profiles and the `qosReference` presets are shared, and are not repeated here.

Ensure that the following tools are installed and meet the required versions:

- **awk**: Version >= 5.1.0
  You can check the version of `awk` installed on your system using the following command:
  ``` shell
  awk --version
  ```
  If the version is lower than 5.1.0, update `awk` using your package manager (e.g., `sudo apt install gawk` on Ubuntu).

- **jq**: used to read the iperf3 JSON reports.

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: rm -rf /tmp/oai/qos-nef-testing
```
-->

``` shell
docker-compose-host $: mkdir -p /tmp/oai/qos-nef-testing
docker-compose-host $: chmod 777 /tmp/oai/qos-nef-testing
```

## 2. Architecture Overview

The deployment is the one from the QoS tutorial with a single container added, `oai-nef`. The AF no longer addresses the PCF; it addresses the NEF, and the NEF addresses the PCF:

```
  AF (external)            NEF                   PCF                SMF              UPF
       |                    |                     |                  |                |
       | N33/T8: POST       |                     |                  |                |
       | as-session-with-qos|                     |                  |                |
       |------------------->|                     |                  |                |
       |                    | translate T8        |                  |                |
       |                    | subscription ->     |                  |                |
       |                    | ascReqData          |                  |                |
       |                    |                     |                  |                |
       |                    | N5: POST            |                  |                |
       |                    | app-sessions        |                  |                |
       |                    |-------------------->|                  |                |
       |                    |                     | derive QosData   |                |
       |                    |                     | and PCC rule     |                |
       |                    |                     |                  |                |
       |                    |                     | N7: SM Policy    |                |
       |                    |                     | UpdateNotify     |                |
       |                    |                     |----------------->|                |
       |                    |                     |                  | N4: QER/PDR    |
       |                    |                     |                  |--------------->|
       |                    |    201 + Location   |                  |                |
       |                    |<--------------------|                  |                |
       |    201 + Location  |                     |                  |                |
       |<-------------------|                     |                  |                |
```

The translation NEF performs is a field-for-field mapping, implemented in `build_pcf_qos_body()`:

| T8 (TS 29.122), what the AF sends | N5 (TS 29.514), what the PCF receives |
|---|---|
| `ueIpv4Addr` | `ascReqData.ueIpv4` |
| `dnn` | `ascReqData.dnn` |
| `snssai` | `ascReqData.sliceInfo` |
| `exterAppId` | `ascReqData.afAppId` |
| `flowInfo[].flowId` | `medComponents.<flowId>.medCompN` |
| `flowInfo[].flowDescriptions` | `medComponents.<flowId>.medSubComps.<flowId>.fDescs` |
| `qosReference` | `medComponents.<flowId>.qosReference` |
| `events` | `ascReqData.evSubsc.events[]` (T8 `UserPlaneEvent` → PCF `AfEvent`) |
| `notificationDestination` | *not forwarded* — NEF keeps it and sets `evSubsc.notifUri` to its **own** callback address, so PCF notifies NEF, and NEF notifies the AF |

Two consequences are worth keeping in mind while reading the requests below:

- `qosReference` is a **per-subscription** field in T8, while on N5 it sits inside each media component. One T8 subscription therefore applies one QoS treatment to all of its flows.
- NEF **copies the `qosReference` label through unchanged**. It does not translate it into a 5QI, so the label must be one the PCF already knows — i.e. a key of [`oai_qos_references.yaml`](../docker-compose/policies/qos_references/oai_qos_references.yaml). This is why no new policy configuration is needed for this tutorial.

## 3. Building the NEF Image

There is no published `oai-nef` image yet, so it has to be built from source. The QoS implementation lives on the `pre_develop` branch:

```console
docker-compose-host $: git clone --branch pre_develop https://github.com/openairinterface/oai-cn5g-nef.git ~/oai-cn5g-nef
docker-compose-host $: cd ~/oai-cn5g-nef
docker-compose-host $: git submodule sync --recursive
docker-compose-host $: git submodule update --init --recursive
docker-compose-host $: docker build -f docker/Dockerfile.nef.ubuntu --target oai-nef -t oai-nef:pre_develop .
```

> **Note**
>
> `git submodule sync` is required and not optional: the submodule URLs move from `gitlab.eurecom.fr` to `github.com` on this branch, so a working tree that previously tracked `develop` keeps fetching the old remotes without it.
>
> At the time of writing, `docker/Dockerfile.nef.ubuntu` on `pre_develop` does not build as committed — it still refers to the AMF build script and binary, and its dependency installer does not install `cpr`. The deviations needed are listed in `BUILD_FINDINGS.md` in that repository. Once the packaging fixes land upstream, the command above works unmodified.

Check that the image is present before deploying:

``` shell
docker-compose-host $: docker image inspect oai-nef:pre_develop --format 'NEF image present: {{.Id}}'
```

## 4. Core Network Configuration

The core network configuration is **identical** to the QoS tutorial: the same [`basic_nrf_config_qos.yaml`](../docker-compose/conf/basic_nrf_config_qos.yaml), the same [PCC rules and policy decisions](../docker-compose/policies/qos), and the same [`qosReference` presets](../docker-compose/policies/qos_references/oai_qos_references.yaml). Nothing about the PCF, SMF or UPF changes when an AF arrives through the NEF rather than on N5 directly.

The only new file is the NEF's own configuration, [`conf/nef_config_qos.yaml`](../docker-compose/conf/nef_config_qos.yaml). Two parts of it matter here.

The N5 peer, which is what makes the translation possible:

```yaml
nfs:
  pcf:
    host: oai-pcf
    sbi:
      port: 8080
      api_version: v1
      interface_name: eth0
```

and the authorization policy:

```yaml
nef:
  af_whitelist: []
  security:
    jwt_secret: ""
    insecure_dev_mode: true
```

NEF authorizes every northbound request before serving it, using an AF whitelist and/or a bearer token (HMAC-SHA256 JWT, which NEF validates but does not issue). With neither configured it is fail-closed and denies everything, so this demo sets `insecure_dev_mode: true` to let the unauthenticated AF through. NEF prints a prominent warning banner at startup when it does so. **Never use this outside a lab.**

> **Note: do not send an `Authorization` header**
>
> An empty `jwt_secret` means "JWT is not in use", not "any token is accepted": a request that *carries* a bearer token is rejected. All the `curl` calls below therefore send no `Authorization` header. If you configure a `jwt_secret`, add `-H "Authorization: Bearer <token>"` to each of them.

NEF is configured only by this mounted file — it reads no environment variables.

## 5. Network Function Deployment

Deploy the core network with the NEF included:

``` shell
docker-compose-host $: python3 core-network.py --type start-basic-qos-nef --scenario 1 --capture /tmp/oai/qos-nef-testing/qos-nef-testing.pcap
```

If you prefer to use docker compose directly:

```console
docker-compose-host $: docker compose -f docker-compose-basic-nrf-qos-nef.yaml up -d
```

Verify that all containers are running correctly, `oai-nef` among them:

``` shell
docker-compose-host $: docker ps --format 'table {{.Names}}\t{{.Status}}'
```

Confirm that NEF came up and is serving:

``` shell
docker-compose-host $: docker logs oai-nef 2>&1 | grep -iE "HTTP2 server listening|insecure_dev_mode"
```

<details>
<summary>The output will look like this:</summary>

```
[system ] [warning] NEF: insecure_dev_mode=true with no JWT secret and no AF whitelist – all requests will be permitted (development mode only)
╔══════════════════════════════════════════════════════════════╗
║  SECURITY WARNING: insecure_dev_mode IS ENABLED              ║
║  No authentication configured (no JWT secret, no whitelist). ║
║  ALL requests will be permitted without any auth check.      ║
╚══════════════════════════════════════════════════════════════╝
[nef_sbi] [info] NEF HTTP/2 server listening on 192.168.70.140:8080
```
</details>

> **Note: NRF registration is switched off in this deployment**
>
> `nef_config_qos.yaml` sets `register_nf.general: no`. NEF builds its NF profile with a hardcoded list of service names — `nnef-trafficinfluence`, `nnef-bdt`, `nnef-qosmonitoring`, `nnef-analyticsexposure` — none of which are in the TS 29.510 `ServiceName` enum (which defines only `nnef-pfdmanagement`, `nnef-smcontext`, `nnef-eventexposure` and `nnef-eas-deployment` for the NEF). The NRF therefore rejects the entire profile with `400 Bad Request` and logs:
>
> ```
> Unexpected value nnef-trafficinfluence in json cannot be converted to enum of type ServiceName_anyOf::eServiceName_anyOf
> ```
>
> Nothing in this tutorial needs NRF discovery, because NEF reaches the PCF through the statically configured `nfs.pcf` endpoint. Leaving registration enabled is harmless — NEF carries on serving after the failure — but it fills the log with an error that has nothing to do with QoS.

## 6. Deploy UERANSIM

The RAN side is unchanged from the QoS tutorial. Deploy the gNB and the two UEs:

``` shell
docker-compose-host $: docker compose -f docker-compose-ueransim-qos.yaml up -d
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: sleep 20
```
-->

Check that the 5QI-1 UE is registered and has its static IP address `12.1.1.10`:

``` shell
docker-compose-host $: docker exec ueransim-ue-5qi-1 ip a | grep uesimtun0
```

## 7. Testing QoS on Demand through the NEF

> **⚠ Known blocker: `AfEvent` model collision between NEF and PCF**
>
> As of the `pre_develop` NEF and the `develop` PCF, the create in 7.2 below **fails**. NEF answers `500` with `{"detail":"Failed to create policy authorization in PCF"}` and the PCF logs:
>
> ```
> [pcf_sbi] [warning] Parsing error: Unexpected value FAILED_RESOURCES_ALLOCATION in json
>                     cannot be converted to enum of type AfEvent_anyOf::eAfEvent_anyOf
> ```
>
> NEF always populates `ascReqData.evSubsc.events[]` on create, injecting the TS 29.514 §5.6.3.6 values `SUCCESSFUL_RESOURCES_ALLOCATION` and `FAILED_RESOURCES_ALLOCATION` whether or not the AF asked for any event. The PCF parses that field through the generated `AfEvent` model in `common-src`, which is the **TS 29.517 `Naf_EventExposure`** enum (`UE_MOBILITY`, `SVC_EXPERIENCE`, `DISPERSION`, …) — two different 3GPP APIs define an enum called `AfEvent`, and only one of them survived code generation. The PCF's own policy-authorization code knows the correct strings, but the model layer cannot parse them, so the whole `ascReqData` is rejected with `400`.
>
> There is no workaround from the AF side: `evSubsc` is built unconditionally in `build_pcf_qos_body()` whenever NEF has a callback URI, which it always does on create. (`PATCH` and `PUT` pass an empty callback URI and therefore send no `evSubsc`.) The fix belongs in `common-src`/PCF — generating the TS 29.514 `AfEvent` separately from the TS 29.517 one — and optionally in NEF, which should only send `evSubsc` for events the AF actually subscribed to.
>
> Until that lands, the steps below are the intended flow but will not pass. Everything up to the PCF call is verified working: NEF validates the T8 request, translates it, and reaches `POST http://oai-pcf:8080/npcf-policyauthorization/v1/app-sessions`.

The UE's PDU session starts with the statically provisioned policy from the QoS tutorial: PCC rule `gbr-rule-5qi-1`, 3 Mbps downlink. Nothing in that policy mentions port 5000. Over the next steps the AF will ask the NEF for 15 Mbps on port 5000, lower it to 5 Mbps, and then give it back — and the throughput measured at the UE will follow each request.

Start an iperf3 server on the UE, listening on port 5000. It stays up for the whole section:

``` shell
docker-compose-host $: docker exec -d ueransim-ue-5qi-1 iperf3 -s -B 12.1.1.10 -p 5000
```

### 7.1. Baseline: before any AF request

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -O 1 -c 12.1.1.10 -p 5000 -B 192.168.72.135 -J > /tmp/oai/qos-nef-testing/iperf_result_baseline.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-nef-testing/iperf_result_baseline.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-nef-testing/iperf_result_baseline.json | awk '{if($1>=2 && $1<=4){print "Max bitrate "$1" Mbps is within range (2-4)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (2-4)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

The throughput sits at about 3 Mbps — the default GBR rule for this UE.

### 7.2. Create the AS Session with QoS

The AF now asks the NEF for 15 Mbps on port 5000, by creating an **AS Session with QoS** subscription. The SCS/AS identity is the `{scsAsId}` path segment, `scs-as-1` here; `-i` prints the response headers so we can capture the `Location` header, whose last segment is the subscription id used by every later request:

``` shell
docker-compose-host $: docker exec oai-af curl -i -H 'Content-Type: application/json' -X POST -d '{"ueIpv4Addr": "12.1.1.10", "notificationDestination": "http://oai-af/notifications", "qosReference": "OAI_QOS_GBR_VIDEO_1", "exterAppId": "oai-qos-demo", "dnn": "default", "snssai": { "sst": 222, "sd": "00007B" }, "flowInfo": [ { "flowId": 1, "flowDescriptions": [ "permit out 6 from any to assigned 5000" ] } ] }' --http2-prior-knowledge http://192.168.70.140:8080/3gpp-as-session-with-qos/v1/scs-as-1/subscriptions > /tmp/nef_create_response.txt
docker-compose-host $: SUB_ID=$(grep -i '^location:' /tmp/nef_create_response.txt | awk -F/ '{print $NF}' | tr -d '\r'); echo "subscription id: $SUB_ID"
```

NEF answers `201 Created`. Note what it did *not* require: no `medComponents`, no `medSubComps`, no `suppFeat`, and no knowledge of where the PCF is. The AF described a flow and named a QoS treatment; NEF produced the N5 request.

> **Note: the notification callback must not be an IP literal in a private range**
>
> `notificationDestination` is sent as `http://oai-af/notifications`, a hostname, not `http://192.168.70.144/notifications`. NEF validates the callback URI to stop an AF aiming notifications into the operator's network, and rejects any IP literal in a loopback, link-local or RFC 1918 range with `400 Bad Request`:
>
> ```
> {"detail":"notificationDestination: callback URI host is in an RFC 1918 private range and is not allowed","status":400,"title":"Bad Request","type":"about:blank"}
> ```
>
> Since the whole demo topology is `192.168.70.0/24`, every address here is in such a range. A host that is not an IP literal is accepted without a DNS lookup, so a container name works and is what this tutorial uses.

Read the subscription back to see what NEF stored, including the `self` link it added:

```console
docker exec oai-af curl -i --http2-prior-knowledge http://192.168.70.140:8080/3gpp-as-session-with-qos/v1/scs-as-1/subscriptions/$SUB_ID
```

Now measure again, with the same iperf3 server still listening on port 5000:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -O 1 -c 12.1.1.10 -p 5000 -B 192.168.72.135 -J > /tmp/oai/qos-nef-testing/iperf_result_nef-qos.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-nef-testing/iperf_result_nef-qos.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-nef-testing/iperf_result_nef-qos.json | awk '{if($1>=9 && $1<=18){print "Max bitrate "$1" Mbps is within range (9-18)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (9-18)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

<details>
<summary>The output will look like this:</summary>

```
Connecting to host 12.1.1.10, port 5000
[  5] local 192.168.72.135 port 50551 connected to 12.1.1.10 port 5000
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  1.80 MBytes  15.1 Mbits/sec    0   46.1 KBytes
[  5]   1.00-2.00   sec  1.67 MBytes  14.0 Mbits/sec    0   46.1 KBytes
[  5]   2.00-3.00   sec  1.60 MBytes  13.4 Mbits/sec    0   46.1 KBytes
[  5]   3.00-4.00   sec  1.67 MBytes  14.0 Mbits/sec    0   46.1 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-4.00   sec  6.72 MBytes  14.1 Mbits/sec    0             sender
[  5]   0.00-4.05   sec  6.64 MBytes  13.7 Mbits/sec                  receiver

iperf Done.
```
</details>

The throughput has moved from ~3 Mbps to just under 15 Mbps, the downlink MBR of `OAI_QOS_GBR_VIDEO_1`. Follow the request through the chain in the logs:

``` shell
docker-compose-host $: docker logs oai-nef 2>&1 | grep -iE "QoS subscription create|cont_qos_create" | tail -5
```

### 7.3. Modify the QoS of a running session

The AF lowers the treatment to `OAI_QOS_GBR_VIDEO_LOW_1` (5 Mbps MBR, 3 Mbps GBR) with a `PATCH`. NEF applies the [RFC 7396](https://www.rfc-editor.org/rfc/rfc7396) JSON Merge Patch to the stored subscription, re-validates the merged result, rebuilds the N5 body and sends an update to the PCF:

``` shell
docker-compose-host $: SUB_ID=$(grep -i '^location:' /tmp/nef_create_response.txt | awk -F/ '{print $NF}' | tr -d '\r'); docker exec oai-af curl -i --fail-with-body -X PATCH -H 'Content-Type: application/merge-patch+json' -d '{"qosReference": "OAI_QOS_GBR_VIDEO_LOW_1"}' --http2-prior-knowledge http://192.168.70.140:8080/3gpp-as-session-with-qos/v1/scs-as-1/subscriptions/$SUB_ID
```

Because `qosReference` is a top-level field in T8, changing the QoS of every flow in the subscription is a one-field patch — compare the equivalent N5 request in the [QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md#81-test-new-qos-profile-from-af), which has to address the media component by its `medCompN`.

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -O 1 -c 12.1.1.10 -p 5000 -B 192.168.72.135 -J > /tmp/oai/qos-nef-testing/iperf_result_nef-patch-qos.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-nef-testing/iperf_result_nef-patch-qos.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-nef-testing/iperf_result_nef-patch-qos.json | awk '{if($1>=3 && $1<=6){print "Max bitrate "$1" Mbps is within range (3-6)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (3-6)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

The throughput drops to about 5 Mbps.

### 7.4. Delete the subscription

Ending the application session removes the QoS treatment. `DELETE` releases the PCF app-session and then drops NEF's local state:

``` shell
docker-compose-host $: SUB_ID=$(grep -i '^location:' /tmp/nef_create_response.txt | awk -F/ '{print $NF}' | tr -d '\r'); docker exec oai-af curl -i --fail-with-body -X DELETE --http2-prior-knowledge http://192.168.70.140:8080/3gpp-as-session-with-qos/v1/scs-as-1/subscriptions/$SUB_ID
```

NEF answers `204 No Content`. The PCF removes the AF-derived PCC rule and the SMF removes the matching QER/PDR from the UPF, so traffic on port 5000 falls back to this UE's default flow, `gbr-rule-5qi-1` at 3 Mbps:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -O 1 -c 12.1.1.10 -p 5000 -B 192.168.72.135 -J > /tmp/oai/qos-nef-testing/iperf_result_nef-delete-qos.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-nef-testing/iperf_result_nef-delete-qos.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-nef-testing/iperf_result_nef-delete-qos.json | awk '{if($1>=2 && $1<=4){print "Max bitrate "$1" Mbps is within range (2-4)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (2-4)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

A subsequent `GET` on the same subscription id now returns `404 Not Found`:

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: SUB_ID=$(grep -i '^location:' /tmp/nef_create_response.txt | awk -F/ '{print $NF}' | tr -d '\r'); docker exec oai-af curl -s -o /dev/null -w '%{http_code}' --http2-prior-knowledge http://192.168.70.140:8080/3gpp-as-session-with-qos/v1/scs-as-1/subscriptions/$SUB_ID | grep -qx 404
```
-->

```console
docker exec oai-af curl -i --http2-prior-knowledge http://192.168.70.140:8080/3gpp-as-session-with-qos/v1/scs-as-1/subscriptions/$SUB_ID
```

> **Note: subscription state is in memory**
>
> NEF keeps its subscriptions and its NEF-subscription-to-PCF-app-session correlation in memory only. Restarting the `oai-nef` container loses them, and the PCF app-sessions they correspond to are then orphaned.

## 8. Log Collection

``` shell
docker-compose-host $: docker logs oai-nef > /tmp/oai/qos-nef-testing/nef.log 2>&1
docker-compose-host $: docker logs oai-pcf > /tmp/oai/qos-nef-testing/pcf.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/qos-nef-testing/smf.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/qos-nef-testing/upf.log 2>&1
docker-compose-host $: docker logs oai-amf > /tmp/oai/qos-nef-testing/amf.log 2>&1
docker-compose-host $: docker logs ueransim-gnb > /tmp/oai/qos-nef-testing/gnb.log 2>&1
docker-compose-host $: docker logs ueransim-ue-5qi-1 > /tmp/oai/qos-nef-testing/ue-5qi-1.log 2>&1
```

## 9. Undeploy the network functions

### 9.1. Undeploy UERANSIM

``` shell
docker-compose-host $: docker compose -f docker-compose-ueransim-qos.yaml down -t 0
```

### 9.2. Undeploy the core network

``` shell
docker-compose-host $: python3 core-network.py --type stop-basic-qos-nef --scenario 1
```

## 10. Conclusion

The same QoS-on-demand lifecycle you can drive on N5 is reachable from outside the operator's trust domain through the NEF's T8 API, with no change to the policy configuration underneath. The AF described a flow and named a QoS treatment; NEF translated that into an `Npcf_PolicyAuthorization` app-session, and the measured throughput followed the request through create, modify and delete.

The `qosReference` label is the contract between the two sides: the AF names a treatment, the operator defines what it means in [`oai_qos_references.yaml`](../docker-compose/policies/qos_references/oai_qos_references.yaml), and NEF passes the label through without interpreting it. An external AF therefore never names a 5QI, a bitrate or an ARP level — which is exactly the separation the exposure layer exists to provide.

To drive the PCF directly over N5 instead, see [section 8 of the QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md#8-testing-qos-on-demand-n5-af-initiated-qos).
