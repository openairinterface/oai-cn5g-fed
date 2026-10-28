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
      <b><font size = "5">OpenAirInterface 5G Core Network Basic Deployment using Docker Compose</font></b>
    </td>
  </tr>
</table>

# Basic Docker Compose Deployment

![SA Demo](./images/docker-compose/5gCN-basic.jpg)

This tutorial deploys the basic OAI 5G Core with NRF, MySQL, AMF, SMF, UPF, AUSF, UDM, UDR, and an external data network container. It then validates end-to-end traffic with Duranta/OAI gNB and OAI NR-UE in RF simulator mode, and checks how the SMF selects the PDU session type (IPv4 or IPv4v6).

## At A Glance

| Item | Value |
| ---- | ----- |
| Goal | Deploy the basic OAI 5G Core, validate UE traffic with Duranta/OAI gNB and OAI NR-UE, and check PDU session type selection |
| Working directory | `oai-cn5g-fed/docker-compose` |
| Core compose file | `docker-compose-basic-nrf.yaml` |
| RFSIM RAN compose file | `docker-compose-oai-rfsim-basic.yaml` |
| Reference configuration | `conf/basic_nrf_config.yaml` |
| Subscription database | `database/oai_db2.sql` |
| Result folder used below | `/tmp/oai/basic-deployment` |

**Reading time**: ~20 minutes

**Replication time**: ~35-50 minutes, depending on image availability.

**TABLE OF CONTENTS**

[[_TOC_]]

Use the document outline or your Markdown viewer to navigate between sections.

## 1. Pre-Requisites

Complete the [deployment pre-requisites](./DEPLOY_PRE_REQUISITES.md) before starting. The official OAI CN5G container images use Ubuntu 22.04 as the container base image and are compatible with Ubuntu hosts 22.04 through 26.04, Fedora 39 through 43, and RHEL 8 through 10.

Any Docker or Podman version available for those host releases should be fine. The commands below use `docker compose`; if your host only has the legacy command, replace `docker compose` with `docker-compose`.

Pull or build the required images before deploying:

- Pull official images: [Retrieve official images](./RETRIEVE_OFFICIAL_IMAGES.md)
- Build local images: [Build images](./BUILD_IMAGES.md)

For the RF simulator test, also pull the RAN images. These commands are shown for users; CI jobs normally preload the required images before running the tutorial checker.

```console
docker pull oaisoftwarealliance/oai-gnb:develop
docker pull oaisoftwarealliance/oai-nr-ue:develop
```

All commands below run from the `docker-compose` folder:

``` shell
docker-compose-host $: rm -rf /tmp/oai/basic-deployment
docker-compose-host $: mkdir -p /tmp/oai/basic-deployment
docker-compose-host $: chmod 777 /tmp/oai/basic-deployment
```

Enable IPv4 forwarding on the host:

```console
sudo sysctl net.ipv4.conf.all.forwarding=1
sudo iptables -P FORWARD ACCEPT
```

## 2. Choose The UE IP Allocation Mode

The SMF can get UE session information in two ways:

| Mode | SMF setting | Use when |
| ---- | ----------- | -------- |
| Local subscription info | `use_local_subscription_info: yes` | You want the simplest dynamic nrUE IP test. This is the default. |
| UDM/UDR/MySQL subscription info | `use_local_subscription_info: no` | You want static nrUE IP allocation or database-driven DNN/NSSAI mapping. |

The setting is in [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml):

```yaml
smf:
  support_features:
    use_local_subscription_info: yes
```

### 2.1 Enable Static UE IP Allocation

Static UE IP allocation requires database-driven subscription information:

The command sequence below enables static IP allocation because it gives CI and users a deterministic UE address to test.

``` shell
docker-compose-host $: sed -i 's/use_local_subscription_info: yes/use_local_subscription_info: no/g' conf/basic_nrf_config.yaml
```

The OAI NR-UE configuration in [ran-conf/nr-ue.conf](../docker-compose/ran-conf/nr-ue.conf) uses IMSI `208950000000036`, DNN `oai`, SST `1`, and the default SD `FFFFFF`. The `oai` DNN subnet in [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml) is `12.1.1.128/26`, so the static address must be inside that subnet.

The default database already has a dynamic session entry for this nrUE. For a persistent static-IP setup, replace the existing `208950000000036` `SessionManagementSubscriptionData` row in [database/oai_db2.sql](../docker-compose/database/oai_db2.sql) before starting the core:

```sql
INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES
('208950000000036', '20895', '{\"sst\": 1, \"sd\": \"FFFFFF\"}','{\"oai\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"IPV4\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"100Mbps\", \"downlink\":\"100Mbps\"},\"staticIpAddress\":[{\"ipv4Addr\": \"12.1.1.130\"}]}}');
```

To return the same nrUE to dynamic IP allocation, restore that row without the `staticIpAddress` field:

```sql
INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES
('208950000000036', '20895', '{\"sst\": 1, \"sd\": \"FFFFFF\"}','{\"oai\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"IPV4\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"100Mbps\", \"downlink\":\"100Mbps\"}}}');
```

Every UE in `AuthenticationSubscription` should also have a matching entry in `SessionManagementSubscriptionData` when `use_local_subscription_info` is set to `no`.

### 2.2 Return To Dynamic Local Subscription Mode

For the simplest dynamic nrUE test, return to the default local subscription mode:

```console
sed -i 's/use_local_subscription_info: no/use_local_subscription_info: yes/g' conf/basic_nrf_config.yaml
```

## 3. Deploy The Basic Core

Start the core and wait for the containers used by this tutorial. After AMF is running, update `ran-conf/gnb.conf` with the AMF container IP that Docker assigned on the `demo-oai-public-net` network.

``` shell
docker-compose-host $: docker-compose -f docker-compose-basic-nrf.yaml up -d
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" mysql 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: docker exec mysql mysql -uroot -plinux oai_db -e "UPDATE SessionManagementSubscriptionData SET dnnConfigurations=JSON_SET(dnnConfigurations, '$.oai.staticIpAddress', JSON_ARRAY(JSON_OBJECT('ipv4Addr', '12.1.1.130'))) WHERE ueid='208950000000036';"
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-nrf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-amf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-smf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-upf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-ext-dn 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: sed -i "s/amf_ip_address      = ( { ipv4       = \".*\";});/amf_ip_address      = ( { ipv4       = \"$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' oai-amf)\";});/" ran-conf/gnb.conf
docker-compose-host $: docker-compose -f docker-compose-basic-nrf.yaml ps -a
```

Expected status: all core containers should be `running` or `healthy`.

Check that NRF, AMF, SMF, UPF, UDM, UDR, AUSF, MySQL, and `oai-ext-dn` are up:

``` shell
docker-compose-host $: docker ps --format "table {{.Names}}\t{{.Status}}"
```

Start a packet capture. The Docker network, and with it the `demo-oai` host bridge, exists by this point:

``` shell
docker-compose-host $: nohup sudo tshark -i demo-oai -f "sctp or tcp port 80 or tcp port 8080 or udp port 2152 or udp port 8805" -w /tmp/oai/basic-deployment/basic-core.pcap > /tmp/oai/basic-deployment/basic-core.log 2>&1 &
```

## 4. Validate With Duranta/OAI gNB And OAI NR-UE

This flow uses:

- [docker-compose-oai-rfsim-basic.yaml](../docker-compose/docker-compose-oai-rfsim-basic.yaml) to start `oai-gnb-basic` and `oai-nr-ue-basic`.
- [ran-conf/gnb.conf](../docker-compose/ran-conf/gnb.conf), whose AMF address is updated by the command sequence in [section 3](#3-deploy-the-basic-core).
- [ran-conf/nr-ue.conf](../docker-compose/ran-conf/nr-ue.conf), which uses IMSI `208950000000036`, key `0C0A...535B`, OPC `63bf...837d`, DNN `oai`, and SST `1`.

Start the gNB:

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-gnb-basic
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-gnb-basic 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: docker logs oai-gnb-basic --tail 30
```

The AMF logs should show the gNB connection:

```console
docker logs oai-amf 2>&1 | grep -i "connected"
```

Start the UE:

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-nr-ue-basic
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-nr-ue-basic 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: docker logs oai-nr-ue-basic --tail 50
```

Check that the UE received a PDU session interface:

``` shell
docker-compose-host $: timeout 120 bash -c 'until docker exec oai-nr-ue-basic ip -4 addr show oaitun_ue1 | grep -q "12.1.1.130"; do sleep 2; done'
docker-compose-host $: docker exec oai-nr-ue-basic ip -4 addr show oaitun_ue1
```

If you selected static UE IP allocation in [section 2.1](#21-enable-static-ue-ip-allocation), the expected nrUE address is `12.1.1.130`. If you kept the default dynamic mode, the address should be in the `12.1.1.128/26` range.

Capture the UE IP and ping it from the external DN container:

``` shell
docker-compose-host $: docker exec oai-ext-dn ping -c4 12.1.1.130
```

You can also test uplink traffic from the UE:

``` shell
docker-compose-host $: docker exec oai-nr-ue-basic ping -I oaitun_ue1 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}')
```

## 5. Collect Logs

Stop any running `tshark` capture first:

``` shell
docker-compose-host $: sudo pkill tshark || true
docker-compose-host $: sleep 5
docker-compose-host $: sudo chmod 666 /tmp/oai/basic-deployment/basic-core.*
```

Collect core logs:

``` shell
docker-compose-host $: docker logs oai-amf > /tmp/oai/basic-deployment/amf.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/basic-deployment/smf.log 2>&1
docker-compose-host $: docker logs oai-nrf > /tmp/oai/basic-deployment/nrf.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/basic-deployment/upf.log 2>&1
docker-compose-host $: docker logs oai-udr > /tmp/oai/basic-deployment/udr.log 2>&1
docker-compose-host $: docker logs oai-udm > /tmp/oai/basic-deployment/udm.log 2>&1
docker-compose-host $: docker logs oai-ausf > /tmp/oai/basic-deployment/ausf.log 2>&1
docker-compose-host $: docker logs oai-ext-dn > /tmp/oai/basic-deployment/ext-dn.log 2>&1
```

Collect RAN and UE logs:

``` shell
docker-compose-host $: docker logs oai-gnb-basic > /tmp/oai/basic-deployment/oai-gnb-basic.log 2>&1
docker-compose-host $: docker logs oai-nr-ue-basic > /tmp/oai/basic-deployment/oai-nr-ue-basic.log 2>&1
```

Reference logs for the old standalone static UE IP tutorial are still available under [results/static-ue-ip](./results/static-ue-ip/).

## 6. Validate PDU Session Type Selection

The SMF selects the PDU session type from the type the UE requests, the `pdu_session_type` of the DNN in [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml), and the subscription (3GPP TS 23.501, clause 5.8.2.2.1). When it serves an IPv4v6 request with IPv4 because the DNN or the subscription allows IPv4 only, the PDU Session Establishment Accept carries 5GSM cause #50 "PDU session type IPv4 only allowed" (3GPP TS 24.501, clause 6.4.1.3).

This section starts three more nrUEs on the running deployment, one at a time. Each opens one PDU session per case, to these DNNs of SST `1`:

| DNN | `pdu_session_type` | IPv4 subnet | IPv6 prefix |
| --- | ------------------ | ----------- | ----------- |
| `oai` | `IPV4` | `12.1.1.128/26` | none |
| `oai.v4v6` | `IPV4V6` | `12.1.1.192/27` | none |
| `oai.dual` | `IPV4V6` | `12.1.1.224/27` | `2001:1:2::/64` |

The nrUEs are services of [docker-compose-oai-rfsim-basic.yaml](../docker-compose/docker-compose-oai-rfsim-basic.yaml), configured in [ran-conf/nr-ue-static.conf](../docker-compose/ran-conf/nr-ue-static.conf), [ran-conf/nr-ue-dynamic.conf](../docker-compose/ran-conf/nr-ue-dynamic.conf) and [ran-conf/nr-ue-ipv4-only.conf](../docker-compose/ran-conf/nr-ue-ipv4-only.conf). Their subscriptions are in [database/oai_db2.sql](../docker-compose/database/oai_db2.sql), which the SMF reads from the UDM as selected in [section 2.1](#21-enable-static-ue-ip-allocation).

| Case | nrUE (IMSI) and subscription | PDU session, DNN | UE requests | Expected session |
| ---- | ---------------------------- | ---------------- | ----------- | ---------------- |
| 1 | `oai-nr-ue-static` (`208950000000120`): a static IPv4 address on each DNN | 1, `oai.v4v6` | IPv4 | IPv4 `12.1.1.220` |
| 2 | `oai-nr-ue-static` | 2, `oai` | IPv4v6 | IPv4 `12.1.1.131`, cause #50: the DNN is IPv4 only |
| 3 | `oai-nr-ue-static`, with IPv4v6 allowed on `oai.dual` | 3, `oai.dual` | IPv4v6 | IPv4 `12.1.1.250`: the static address is IPv4 only |
| 4 | `oai-nr-ue-dynamic` (`208950000000121`): IPv4v6 allowed, no static address | 1, `oai.v4v6` | IPv4v6 | IPv4 from `12.1.1.192/27`, cause #50: the DNN has no IPv6 prefix |
| 5 | `oai-nr-ue-dynamic` | 2, `oai.dual` | IPv4v6 | IPv4v6, from `12.1.1.224/27` and `2001:1:2::/64` |
| 6 | `oai-nr-ue-ipv4-only` (`208950000000122`): IPv4 only, no static address | 1, `oai.dual` | IPv4v6 | IPv4 from `12.1.1.224/27`, cause #50: the subscription allows IPv4 only |

For each PDU Session Establishment Accept, the SMF logs `PDU Session Identity 0x<id>`, then the selected type (`PDU Session Type: 1` for IPv4 or `PDU Session Type: 3` for IPv4v6, once for N1 and once for N2), the 5GSM cause if there is one (`5GSM Cause: 50`), and the addresses. The commands below save the SMF log of each nrUE in `/tmp/oai/basic-deployment/pdu-type-<nrUE>-oai-smf.log`, and split it per PDU session in `pdu-type-<nrUE>-psi<id>.log`. An nrUE has one interface per PDU session: `oaitun_ue1` for the first one, and `oaitun_ue1p<id>` for the others. Uplink traffic is checked on each interface, over IPv4.

### 6.1 Stop The First nrUE

The logs of `oai-nr-ue-basic` were collected in section 5. Stop it, so that one nrUE runs at a time:

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml stop -t 2 oai-nr-ue-basic
```

### 6.2 nrUE With Static Addresses: Cases 1 To 3

Start the nrUE, wait for its three PDU sessions, and save its logs:

``` shell
docker-compose-host $: date +%s > /tmp/oai/basic-deployment/pdu-type-static.since
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-nr-ue-static
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker exec oai-nr-ue-static ip -4 -o addr 2>/dev/null | grep -c "inet 12.1.1.")" = 3 ]; do sleep 2; done'
docker-compose-host $: docker exec oai-nr-ue-static ip -o addr | tee /tmp/oai/basic-deployment/pdu-type-static-ue-addr.log
docker-compose-host $: docker logs --since $(cat /tmp/oai/basic-deployment/pdu-type-static.since) oai-smf > /tmp/oai/basic-deployment/pdu-type-static-oai-smf.log 2>&1
docker-compose-host $: docker logs oai-nr-ue-static > /tmp/oai/basic-deployment/pdu-type-static-oai-nr-ue.log 2>&1
docker-compose-host $: for id in 1 2 3; do awk "/PDU Session Establishment Accept, PDU Session Identity 0x$id,/{f=1} f{print} f && /smf_n2.*PDU Session Type/{exit}" /tmp/oai/basic-deployment/pdu-type-static-oai-smf.log > /tmp/oai/basic-deployment/pdu-type-static-psi$id.log; done
```

Check cases 1 to 3:

``` shell
docker-compose-host $: grep "PDU Session Type: 1" /tmp/oai/basic-deployment/pdu-type-static-psi1.log
docker-compose-host $: ! grep "5GSM Cause: 50" /tmp/oai/basic-deployment/pdu-type-static-psi1.log
docker-compose-host $: grep "UE IPv4 Address 12.1.1.220" /tmp/oai/basic-deployment/pdu-type-static-psi1.log
docker-compose-host $: grep "PDU Session Type: 1" /tmp/oai/basic-deployment/pdu-type-static-psi2.log
docker-compose-host $: grep "PDU Session Establishment Accept, 5GSM Cause: 50" /tmp/oai/basic-deployment/pdu-type-static-psi2.log
docker-compose-host $: grep "UE IPv4 Address 12.1.1.131" /tmp/oai/basic-deployment/pdu-type-static-psi2.log
docker-compose-host $: grep "PDU Session Type: 1" /tmp/oai/basic-deployment/pdu-type-static-psi3.log
docker-compose-host $: ! grep "5GSM Cause: 50" /tmp/oai/basic-deployment/pdu-type-static-psi3.log
docker-compose-host $: grep "UE IPv4 Address 12.1.1.250" /tmp/oai/basic-deployment/pdu-type-static-psi3.log
docker-compose-host $: docker exec oai-nr-ue-static ping -I oaitun_ue1 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}') > /tmp/oai/basic-deployment/pdu-type-static-ping-psi1.log 2>&1
docker-compose-host $: docker exec oai-nr-ue-static ping -I oaitun_ue1p2 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}') > /tmp/oai/basic-deployment/pdu-type-static-ping-psi2.log 2>&1
docker-compose-host $: docker exec oai-nr-ue-static ping -I oaitun_ue1p3 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}') > /tmp/oai/basic-deployment/pdu-type-static-ping-psi3.log 2>&1
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml stop -t 2 oai-nr-ue-static
```

### 6.3 nrUE With Dynamic Addresses: Cases 4 And 5

Start the nrUE, wait for its two PDU sessions, and save its logs:

``` shell
docker-compose-host $: date +%s > /tmp/oai/basic-deployment/pdu-type-dynamic.since
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-nr-ue-dynamic
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker exec oai-nr-ue-dynamic ip -4 -o addr 2>/dev/null | grep -c "inet 12.1.1.")" = 2 ]; do sleep 2; done'
docker-compose-host $: docker exec oai-nr-ue-dynamic ip -o addr | tee /tmp/oai/basic-deployment/pdu-type-dynamic-ue-addr.log
docker-compose-host $: docker logs --since $(cat /tmp/oai/basic-deployment/pdu-type-dynamic.since) oai-smf > /tmp/oai/basic-deployment/pdu-type-dynamic-oai-smf.log 2>&1
docker-compose-host $: docker logs oai-nr-ue-dynamic > /tmp/oai/basic-deployment/pdu-type-dynamic-oai-nr-ue.log 2>&1
docker-compose-host $: for id in 1 2; do awk "/PDU Session Establishment Accept, PDU Session Identity 0x$id,/{f=1} f{print} f && /smf_n2.*PDU Session Type/{exit}" /tmp/oai/basic-deployment/pdu-type-dynamic-oai-smf.log > /tmp/oai/basic-deployment/pdu-type-dynamic-psi$id.log; done
```

Check cases 4 and 5. The SMF must not log a static address for this nrUE:

``` shell
docker-compose-host $: ! grep "Static IP Address" /tmp/oai/basic-deployment/pdu-type-dynamic-oai-smf.log
docker-compose-host $: grep "PDU Session Type: 1" /tmp/oai/basic-deployment/pdu-type-dynamic-psi1.log
docker-compose-host $: grep "PDU Session Establishment Accept, 5GSM Cause: 50" /tmp/oai/basic-deployment/pdu-type-dynamic-psi1.log
docker-compose-host $: grep "UE IPv4 Address 12.1.1.19" /tmp/oai/basic-deployment/pdu-type-dynamic-psi1.log
docker-compose-host $: grep "PDU Session Type: 3" /tmp/oai/basic-deployment/pdu-type-dynamic-psi2.log
docker-compose-host $: ! grep "5GSM Cause: 50" /tmp/oai/basic-deployment/pdu-type-dynamic-psi2.log
docker-compose-host $: grep "UE IPv4 Address 12.1.1.22" /tmp/oai/basic-deployment/pdu-type-dynamic-psi2.log
docker-compose-host $: grep "UE IPv6 Address: 2001:1:2::" /tmp/oai/basic-deployment/pdu-type-dynamic-psi2.log
docker-compose-host $: grep "Accept, UE IPv4v6:" /tmp/oai/basic-deployment/pdu-type-dynamic-oai-nr-ue.log
docker-compose-host $: docker exec oai-nr-ue-dynamic ping -I oaitun_ue1 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}') > /tmp/oai/basic-deployment/pdu-type-dynamic-ping-psi1.log 2>&1
docker-compose-host $: docker exec oai-nr-ue-dynamic ping -I oaitun_ue1p2 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}') > /tmp/oai/basic-deployment/pdu-type-dynamic-ping-psi2.log 2>&1
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml stop -t 2 oai-nr-ue-dynamic
```

### 6.4 nrUE With An IPv4-Only Subscription: Case 6

Start the nrUE, wait for its PDU session, and save its logs:

``` shell
docker-compose-host $: date +%s > /tmp/oai/basic-deployment/pdu-type-ipv4-only.since
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-nr-ue-ipv4-only
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker exec oai-nr-ue-ipv4-only ip -4 -o addr 2>/dev/null | grep -c "inet 12.1.1.")" = 1 ]; do sleep 2; done'
docker-compose-host $: docker exec oai-nr-ue-ipv4-only ip -o addr | tee /tmp/oai/basic-deployment/pdu-type-ipv4-only-ue-addr.log
docker-compose-host $: docker logs --since $(cat /tmp/oai/basic-deployment/pdu-type-ipv4-only.since) oai-smf > /tmp/oai/basic-deployment/pdu-type-ipv4-only-oai-smf.log 2>&1
docker-compose-host $: docker logs oai-nr-ue-ipv4-only > /tmp/oai/basic-deployment/pdu-type-ipv4-only-oai-nr-ue.log 2>&1
docker-compose-host $: awk "/PDU Session Establishment Accept, PDU Session Identity 0x1,/{f=1} f{print} f && /smf_n2.*PDU Session Type/{exit}" /tmp/oai/basic-deployment/pdu-type-ipv4-only-oai-smf.log > /tmp/oai/basic-deployment/pdu-type-ipv4-only-psi1.log
```

Check case 6:

``` shell
docker-compose-host $: ! grep "Static IP Address" /tmp/oai/basic-deployment/pdu-type-ipv4-only-oai-smf.log
docker-compose-host $: grep "PDU Session Type: 1" /tmp/oai/basic-deployment/pdu-type-ipv4-only-psi1.log
docker-compose-host $: grep "PDU Session Establishment Accept, 5GSM Cause: 50" /tmp/oai/basic-deployment/pdu-type-ipv4-only-psi1.log
docker-compose-host $: grep "UE IPv4 Address 12.1.1.22" /tmp/oai/basic-deployment/pdu-type-ipv4-only-psi1.log
docker-compose-host $: docker exec oai-nr-ue-ipv4-only ping -I oaitun_ue1 -c4 $(docker exec oai-ext-dn hostname -I | awk '{print $1}') > /tmp/oai/basic-deployment/pdu-type-ipv4-only-ping-psi1.log 2>&1
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml stop -t 2 oai-nr-ue-ipv4-only
```

## 7. Cleanup

Stop the OAI RF simulator:

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml down -t 2
```

Stop the core:

``` shell
docker-compose-host $: docker-compose -f docker-compose-basic-nrf.yaml down -t 2
```

If you enabled static UE IP allocation and want to return to the default tutorial state:

``` shell
docker-compose-host $: sed -i 's/use_local_subscription_info: no/use_local_subscription_info: yes/g' conf/basic_nrf_config.yaml
docker-compose-host $: sed -i 's/amf_ip_address      = ( { ipv4       = ".*";});/amf_ip_address      = ( { ipv4       = "192.168.70.138";});/' ran-conf/gnb.conf
```

## 8. Troubleshooting

| Symptom | First check |
| ------- | ----------- |
| Core containers are not healthy | `docker compose -f docker-compose-basic-nrf.yaml ps` and `docker logs <container>` |
| Static UE IP is not `12.1.1.130` | Confirm `use_local_subscription_info: no` and the `208950000000036` `SessionManagementSubscriptionData` entry in `database/oai_db2.sql` |
| OAI gNB does not connect to AMF | Confirm `ran-conf/gnb.conf` contains the current `oai-amf` container IP from `docker inspect` |
| OAI UE has no `oaitun_ue1` | Check `docker logs oai-nr-ue-basic` and confirm `oai-gnb-basic` is healthy |
| No traffic between UE and `oai-ext-dn` | Re-run host forwarding commands and check routes inside `oai-ext-dn` with `docker exec oai-ext-dn ip route` |
| A case of section 6 fails | Compare `/tmp/oai/basic-deployment/pdu-type-<nrUE>-psi<id>.log`, the SMF log lines of that PDU session, with the table in [section 6](#6-validate-pdu-session-type-selection). An empty file means the SMF did not accept the PDU session: look for `unknown requested DNN` (5GSM cause #27) in `pdu-type-<nrUE>-oai-smf.log` |

## 9. Report An Issue

When opening an issue, include:

1. The exact scenario: dynamic nrUE IP, static nrUE IP, or the case of section 6.
2. The commands used to start the core and RAN/UE.
3. The edited parts of `conf/basic_nrf_config.yaml` and any database changes.
4. Logs from the affected containers.
5. Packet captures from `demo-oai` when available.

For contribution workflow details, see [CONTRIBUTING.md](../CONTRIBUTING.md).
