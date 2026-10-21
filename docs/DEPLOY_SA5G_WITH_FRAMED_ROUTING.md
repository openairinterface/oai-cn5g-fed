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
      <b><font size = "5">OpenAirInterface 5G Core Network Deployment with Framed Routing using Docker Compose</font></b>
    </td>
  </tr>
</table>

# Framed Routing

Framed Routing lets a UE act as a router for an IP subnet that sits behind it. The subnet is
provisioned per subscriber in the UDR (`ipv4FrameRouteList`), signalled to the SMF over N10 and
installed in the UPF as an additional route towards that UE's PDU session. Packets with a source
address inside the framed subnet are then forwarded upstream, and packets destined to the framed
subnet are tunnelled down to the UE instead of being dropped as unknown UE addresses.

This is the 5G equivalent of the RADIUS `Framed-Route` attribute (RFC 2865) and is used for CPE /
industrial gateway deployments, where a 5G modem terminates the PDU session and a LAN behind it has
to stay reachable.

This tutorial does not add any deployment file. It reuses the existing `basic` (simple-switch UPF)
and `basic-ebpf` (eBPF/XDP UPF) deployments together with the OAI RF simulator RAN, and only
changes the configuration.

## At A Glance

| Item | Value |
| ---- | ----- |
| Goal | Enable Framed Routing and reach a subnet behind the UE from the data network |
| Working directory | `oai-cn5g-fed/docker-compose` |
| Core compose file (simple switch) | `docker-compose-basic-nrf.yaml` |
| Core compose file (eBPF) | `docker-compose-basic-nrf-ebpf.yaml` |
| RFSIM RAN compose file (simple switch) | `docker-compose-oai-rfsim-basic.yaml` |
| RFSIM RAN compose file (eBPF) | `docker-compose-oai-rfsim-ebpf.yaml` |
| Reference configuration | `conf/basic_nrf_config.yaml`, `conf/basic_nrf_config_ebpf.yaml` |
| Subscription database | `database/oai_db2.sql` |
| Subscriber used | IMSI `208950000000036`, DNN `oai`, SST `1` |
| UE PDU session address | `12.1.1.130` |
| Framed subnet behind the UE | `192.168.128.0/24` |
| Result folder used below | `/tmp/oai/framed-routing` |

**Reading time**: ~20 minutes

**Replication time**: ~30-45 minutes, depending on image availability.

**TABLE OF CONTENTS**

[[_TOC_]]

Use the document outline or your Markdown viewer to navigate between sections.

## 1. Pre-Requisites

Follow the [deployment pre-requisites](./DEPLOY_PRE_REQUISITES.md) and make sure you can run the
[basic deployment](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md) before starting here. This tutorial assumes
you are in the `oai-cn5g-fed/docker-compose` folder.

Framed Routing needs an SMF that forwards `ipv4FrameRouteList` from the UDM and a UPF that installs
the framed route. Both are part of the `develop` images used by the compose files below.

Create the folder used for the logs of this tutorial.

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: rm -rf /tmp/oai/framed-routing
```
-->

``` shell
docker-compose-host $: mkdir -p /tmp/oai/framed-routing
docker-compose-host $: chmod 777 /tmp/oai/framed-routing
```

## 2. Architecture

```
  +------------------+        +-----------+        +-----------+        +-------------+
  | Framed subnet    |        |    UE     |        |    UPF    |        | oai-ext-dn  |
  | 192.168.128.0/24 | ------ | 12.1.1.130|== N3 ==| route:    |== N6 ==| data network|
  | (behind the UE)  |  LAN   |oaitun_ue1 |        | 192.168.  |        |             |
  +------------------+        +-----------+        | 128.0/24  |        +-------------+
                                                   | -> UE     |
                                                   +-----------+
```

The UE address `12.1.1.130` is allocated from the `oai` DNN pool `12.1.1.128/25`. The framed subnet
`192.168.128.0/24` is **not** part of any DNN pool: it only exists as a per-subscriber route that
the UPF installs when the PDU session is created.

In this tutorial the "LAN behind the UE" is emulated with a second address on the UE's tunnel
interface, which is enough to prove that the core forwards both directions for a prefix that is not
the UE address itself.

## 3. Subscriber Configuration

Framed Routing is subscription data, so the SMF has to take the session information from
UDM/UDR instead of the local configuration. The subscriber `208950000000036` used by the OAI
NR-UE already has a `SessionManagementSubscriptionData` entry for DNN `oai` in
[database/oai_db2.sql](../docker-compose/database/oai_db2.sql); the framed subnet is added to that
entry with the `ipv4FrameRouteList` field:

```json
{
  "oai": {
    "pduSessionTypes": { "defaultSessionType": "IPV4" },
    "sscModes": { "defaultSscMode": "SSC_MODE_1" },
    "5gQosProfile": { "5qi": 6, "arp": { "priorityLevel": 1, "preemptCap": "NOT_PREEMPT", "preemptVuln": "NOT_PREEMPTABLE" }, "priorityLevel": 1 },
    "sessionAmbr": { "uplink": "100Mbps", "downlink": "100Mbps" },
    "staticIpAddress": [ { "ipv4Addr": "12.1.1.130" } ],
    "ipv4FrameRouteList": [ { "ipv4Mask": "192.168.128.0/24" } ]
  }
}
```

You can either patch `database/oai_db2.sql` before the first start, or apply the field at runtime on
the running MySQL container. The sections below use the runtime variant so that the shipped database
file stays untouched.

`ipv4FrameRouteList` is a list: provision several prefixes behind the same UE by adding more
`ipv4Mask` entries.

## 4. Framed Routing With The Simple-Switch UPF

### 4.1 Enable Framed Routing In The Configuration

Two settings in [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml) have to
change:

```yaml
smf:
  support_features:
    use_local_subscription_info: no   # take the framed route from UDM/UDR

upf:
  support_features:
    enable_bpf_datapath: no
    enable_snat: yes
    enable_fr: yes                    # install framed routes in the UPF
```

``` shell
docker-compose-host $: sed -i 's/use_local_subscription_info: yes/use_local_subscription_info: no/g' conf/basic_nrf_config.yaml
docker-compose-host $: grep -q 'enable_fr' conf/basic_nrf_config.yaml || sed -i '/enable_snat: yes           # If "on": Source natting is done for UE, DEFAULT= off/a\    enable_fr: yes             # If "on": Framed Routing is enabled, DEFAULT= off' conf/basic_nrf_config.yaml
docker-compose-host $: grep -A4 '^upf:' conf/basic_nrf_config.yaml
```

With `enable_snat: yes` the simple-switch UPF also adds a source NAT rule for the framed subnet, so
the subnet behind the UE reaches external destinations without any extra rule on `oai-ext-dn`.

### 4.2 Deploy The Core Network

``` shell
docker-compose-host $: docker-compose -f docker-compose-basic-nrf.yaml up -d
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" mysql 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-nrf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-amf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-smf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-upf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-ext-dn 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: docker ps --format "table {{.Names}}\t{{.Status}}"
```

Check that the UPF started with the feature enabled:

``` shell
docker-compose-host $: docker logs oai-upf 2>&1 | grep -i "Framed Routing"
```

<details>
<summary>The output will look like this:</summary>

``` console
[config ] [info]     + Enable Framed Routing....................: Yes
```
</details>

### 4.3 Provision The Framed Route

``` shell
docker-compose-host $: docker exec mysql mysql -uroot -plinux oai_db -e "UPDATE SessionManagementSubscriptionData SET dnnConfigurations=JSON_SET(dnnConfigurations, '\$.oai.ipv4FrameRouteList', JSON_ARRAY(JSON_OBJECT('ipv4Mask', '192.168.128.0/24'))) WHERE ueid='208950000000036';"
docker-compose-host $: docker exec mysql mysql -uroot -plinux oai_db -N -e "SELECT JSON_EXTRACT(dnnConfigurations, '\$.oai.ipv4FrameRouteList') FROM SessionManagementSubscriptionData WHERE ueid='208950000000036';"
```

<details>
<summary>The output will look like this:</summary>

``` console
[{"ipv4Mask": "192.168.128.0/24"}]
```
</details>

### 4.4 Deploy The RAN

Point the gNB at the AMF address that Docker assigned, then start the RF simulator gNB and UE. The
gNB container reports healthy as soon as the process exists, so wait for the RF simulator to serve
the cell before starting the UE.

``` shell
docker-compose-host $: sed -i "s/amf_ip_address      = ( { ipv4       = \".*\";});/amf_ip_address      = ( { ipv4       = \"$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' oai-amf)\";});/" ran-conf/gnb.conf
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-gnb-basic
docker-compose-host $: timeout 180 bash -c 'until docker logs oai-gnb-basic 2>&1 | grep -q "RU 0 RF started"; do sleep 3; done'
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml up -d oai-nr-ue-basic
docker-compose-host $: timeout 300 bash -c 'until docker exec oai-nr-ue-basic ip -4 a show oaitun_ue1 2>/dev/null | grep -q "inet "; do sleep 3; done'
docker-compose-host $: docker exec oai-nr-ue-basic ip -4 a show oaitun_ue1
```

<details>
<summary>The output will look like this:</summary>

``` console
3: oaitun_ue1: <POINTOPOINT,NOARP,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UNKNOWN group default qlen 500
    inet 12.1.1.130/24 scope global oaitun_ue1
```
</details>

The UPF logs the framed route it installed for this session:

``` shell
docker-compose-host $: docker logs oai-upf 2>&1 | grep -i "framed routing ip"
docker-compose-host $: docker exec oai-upf ip route
```

<details>
<summary>The output will look like this:</summary>

``` console
[pfcp_switch] [debug] framed routing ip: 192.168.128.0/24
...
12.1.1.128/25 dev tun0 proto kernel scope link src 12.1.1.129
192.168.128.0/24 via 12.1.1.129 dev tun0
```
</details>

### 4.5 Configure The Subnet Behind The UE

The UE has to own the framed subnet and send its traffic into the PDU session. A policy routing rule
keeps the framed subnet on `oaitun_ue1` while the container's own management traffic keeps using
`eth0`.

``` shell
docker-compose-host $: docker exec oai-nr-ue-basic ip addr add 192.168.128.1/24 dev oaitun_ue1
docker-compose-host $: docker exec oai-nr-ue-basic ip rule add from 192.168.128.0/24 lookup 200
docker-compose-host $: docker exec oai-nr-ue-basic ip route add default dev oaitun_ue1 table 200
```

On the data network side, `oai-ext-dn` needs a route to the framed subnet via the UPF N6 address:

``` shell
docker-compose-host $: docker exec oai-ext-dn ip route add 192.168.128.0/24 via $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' oai-upf)
docker-compose-host $: docker exec oai-ext-dn ip route
```

### 4.6 Test Framed Routing

Uplink, from an address inside the framed subnet to the data network:

``` shell
docker-compose-host $: docker exec oai-nr-ue-basic ping -c 3 -I 192.168.128.1 $(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' oai-ext-dn)
```

<details>
<summary>The output will look like this:</summary>

``` console
PING 192.168.70.130 (192.168.70.130) from 192.168.128.1 : 56(84) bytes of data.
64 bytes from 192.168.70.130: icmp_seq=1 ttl=63 time=11.6 ms
64 bytes from 192.168.70.130: icmp_seq=2 ttl=63 time=7.35 ms
64 bytes from 192.168.70.130: icmp_seq=3 ttl=63 time=7.91 ms

--- 192.168.70.130 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
```
</details>

Downlink, from the data network into the subnet behind the UE. This is the direction that only works
with Framed Routing: without the installed route the UPF has no PDU session matching
`192.168.128.1`.

``` shell
docker-compose-host $: docker exec oai-ext-dn ping -c 3 192.168.128.1
```

<details>
<summary>The output will look like this:</summary>

``` console
PING 192.168.128.1 (192.168.128.1) 56(84) bytes of data.
64 bytes from 192.168.128.1: icmp_seq=1 ttl=63 time=9.92 ms
64 bytes from 192.168.128.1: icmp_seq=2 ttl=63 time=6.55 ms
64 bytes from 192.168.128.1: icmp_seq=3 ttl=63 time=11.4 ms

--- 192.168.128.1 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2002ms
```
</details>

Optionally, if the host has internet access, the framed subnet also reaches external destinations
through the UPF source NAT:

``` console
docker-compose-host $: docker exec oai-nr-ue-basic ping -c 3 -I 192.168.128.1 8.8.8.8
```

### 4.7 Collect The Logs

``` shell
docker-compose-host $: docker logs oai-amf > /tmp/oai/framed-routing/amf-sw.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/framed-routing/smf-sw.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/framed-routing/upf-sw.log 2>&1
docker-compose-host $: docker logs oai-udm > /tmp/oai/framed-routing/udm-sw.log 2>&1
docker-compose-host $: docker logs oai-udr > /tmp/oai/framed-routing/udr-sw.log 2>&1
docker-compose-host $: docker logs oai-ext-dn > /tmp/oai/framed-routing/ext-dn-sw.log 2>&1
docker-compose-host $: docker logs oai-gnb-basic > /tmp/oai/framed-routing/gnb-sw.log 2>&1
docker-compose-host $: docker logs oai-nr-ue-basic > /tmp/oai/framed-routing/nr-ue-sw.log 2>&1
```

### 4.8 Undeploy

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-basic.yaml down -t 2
docker-compose-host $: docker-compose -f docker-compose-basic-nrf.yaml down -t 2
```

## 5. Framed Routing With The eBPF UPF

The eBPF/XDP UPF installs the framed subnet in its BPF maps instead of the Linux FIB. The
configuration steps are the same, only the files and the N6 topology differ: the eBPF UPF runs in
the host network namespace and uses the dedicated `demo-n3` and `demo-n6` bridges.

### 5.1 Enable Framed Routing In The Configuration

[conf/basic_nrf_config_ebpf.yaml](../docker-compose/conf/basic_nrf_config_ebpf.yaml) already has the
`enable_fr` flag, it only has to be turned on:

```yaml
smf:
  support_features:
    use_local_subscription_info: no

upf:
  support_features:
    enable_bpf_datapath: yes
    enable_snat: no
    enable_fr: yes
```

``` shell
docker-compose-host $: sed -i 's/use_local_subscription_info: yes/use_local_subscription_info: no/g' conf/basic_nrf_config_ebpf.yaml
docker-compose-host $: sed -i 's/^    enable_fr: no$/    enable_fr: yes/' conf/basic_nrf_config_ebpf.yaml
docker-compose-host $: grep -E 'enable_bpf_datapath|enable_snat|enable_fr' conf/basic_nrf_config_ebpf.yaml
```

### 5.2 Deploy The Core Network

``` shell
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-ebpf.yaml up -d
docker-compose-host $: timeout 180 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" mysql 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-amf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-smf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-upf 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: timeout 120 bash -c 'until [ "$(docker inspect -f "{{.State.Health.Status}}" oai-ext-dn 2>/dev/null)" = "healthy" ]; do sleep 2; done'
docker-compose-host $: docker logs oai-upf 2>&1 | grep -i "Framed Routing"
```

<details>
<summary>The output will look like this:</summary>

``` console
[config ] [info]     + Enable Framed Routing....................: Yes
[upf_app] [info]   ├─ Framed Routing    :  ✓ on
```
</details>

### 5.3 Provision The Framed Route

``` shell
docker-compose-host $: docker exec mysql mysql -uroot -plinux oai_db -e "UPDATE SessionManagementSubscriptionData SET dnnConfigurations=JSON_SET(dnnConfigurations, '\$.oai.ipv4FrameRouteList', JSON_ARRAY(JSON_OBJECT('ipv4Mask', '192.168.128.0/24'))) WHERE ueid='208950000000036';"
```

### 5.4 Deploy The RAN

The eBPF deployment pins the AMF to `192.168.70.132`, which is what
[ran-conf/gnb.sa.band78.106prb.rfsim.yaml](../docker-compose/ran-conf/gnb.sa.band78.106prb.rfsim.yaml)
already points to, so no gNB configuration change is needed here.

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml up -d oai-gnb
docker-compose-host $: timeout 180 bash -c 'until docker logs oai-gnb 2>&1 | grep -q "RU 0 RF started"; do sleep 3; done'
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml up -d oai-nr-ue1
docker-compose-host $: timeout 300 bash -c 'until docker exec oai-nr-ue1 ip -4 a show oaitun_ue1 2>/dev/null | grep -q "inet "; do sleep 3; done'
docker-compose-host $: docker exec oai-nr-ue1 ip -4 a show oaitun_ue1
docker-compose-host $: docker logs oai-upf 2>&1 | grep -i "Framed route"
```

<details>
<summary>The output will look like this:</summary>

``` console
[upf_app] [info] [eBPF] Framed route 0xc0a88000/0xffffff00 -> UE 0xc010182 installed (SEID 0x1)
```

`0xc0a88000/0xffffff00` is `192.168.128.0/24` and `0xc010182` is the UE address `12.1.1.130`.
</details>

### 5.5 Configure The Subnet Behind The UE

``` shell
docker-compose-host $: docker exec oai-nr-ue1 ip addr add 192.168.128.1/24 dev oaitun_ue1
docker-compose-host $: docker exec oai-nr-ue1 ip rule add from 192.168.128.0/24 lookup 200
docker-compose-host $: docker exec oai-nr-ue1 ip route add default dev oaitun_ue1 table 200
```

On the eBPF deployment the N6 link is `demo-n6` (`192.168.72.128/26`), where the UPF owns
`192.168.72.129` and `oai-ext-dn` owns `192.168.72.135`. The interface names inside `oai-ext-dn`
depend on the order in which Docker attaches the networks, so the route is added without `dev`:

``` shell
docker-compose-host $: docker exec oai-ext-dn ip route add 192.168.128.0/24 via 192.168.72.129
docker-compose-host $: docker exec oai-ext-dn ip route
```

### 5.6 Test Framed Routing

``` shell
docker-compose-host $: docker exec oai-nr-ue1 ping -c 3 -I 192.168.128.1 192.168.72.135
docker-compose-host $: docker exec oai-ext-dn ping -c 3 192.168.128.1
```

<details>
<summary>The output will look like this:</summary>

``` console
PING 192.168.72.135 (192.168.72.135) from 192.168.128.1 : 56(84) bytes of data.
64 bytes from 192.168.72.135: icmp_seq=1 ttl=64 time=21.6 ms
...
PING 192.168.128.1 (192.168.128.1) 56(84) bytes of data.
64 bytes from 192.168.128.1: icmp_seq=1 ttl=64 time=24.1 ms
...
3 packets transmitted, 3 received, 0% packet loss
```
</details>

### 5.7 Optional: Reach External Destinations From The Framed Subnet

The eBPF UPF runs in the host network namespace and resolves the egress interface with
`bpf_fib_lookup()` against the host FIB. The compose file already installs a policy routing rule for
the UE pool `12.1.1.0/24` from the UPF entrypoint; the framed subnet needs the same treatment, plus
source NAT on `oai-ext-dn` because `enable_snat` is off in the eBPF configuration.

``` console
docker-compose-host $: sudo ip rule add from 192.168.128.0/24 lookup 200
docker-compose-host $: docker exec oai-ext-dn iptables -t nat -A POSTROUTING -s 192.168.128.0/24 -j MASQUERADE
docker-compose-host $: docker exec oai-nr-ue1 ping -c 3 -I 192.168.128.1 8.8.8.8
```

Remove the host rule again when you are done:

``` console
docker-compose-host $: sudo ip rule del from 192.168.128.0/24 lookup 200
```

### 5.8 Collect The Logs And Undeploy

``` shell
docker-compose-host $: docker logs oai-amf > /tmp/oai/framed-routing/amf-ebpf.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/framed-routing/smf-ebpf.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/framed-routing/upf-ebpf.log 2>&1
docker-compose-host $: docker logs oai-udm > /tmp/oai/framed-routing/udm-ebpf.log 2>&1
docker-compose-host $: docker logs oai-udr > /tmp/oai/framed-routing/udr-ebpf.log 2>&1
docker-compose-host $: docker logs oai-ext-dn > /tmp/oai/framed-routing/ext-dn-ebpf.log 2>&1
docker-compose-host $: docker logs oai-gnb > /tmp/oai/framed-routing/gnb-ebpf.log 2>&1
docker-compose-host $: docker logs oai-nr-ue1 > /tmp/oai/framed-routing/nr-ue-ebpf.log 2>&1
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml down -t 2
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-ebpf.yaml down -t 2
```

## 6. Restore The Default Configuration

``` shell
docker-compose-host $: sed -i 's/use_local_subscription_info: no/use_local_subscription_info: yes/g' conf/basic_nrf_config.yaml
docker-compose-host $: sed -i '/^    enable_fr: yes             # If "on": Framed Routing is enabled, DEFAULT= off$/d' conf/basic_nrf_config.yaml
docker-compose-host $: sed -i 's/amf_ip_address      = ( { ipv4       = ".*";});/amf_ip_address      = ( { ipv4       = "192.168.70.138";});/' ran-conf/gnb.conf
docker-compose-host $: sed -i 's/use_local_subscription_info: no/use_local_subscription_info: yes/g' conf/basic_nrf_config_ebpf.yaml
docker-compose-host $: sed -i 's/^    enable_fr: yes$/    enable_fr: no/' conf/basic_nrf_config_ebpf.yaml
```

## 7. Troubleshooting

| Symptom | First check |
| ------- | ----------- |
| UPF banner does not show Framed Routing | `enable_fr: yes` is under `upf.support_features` in the configuration file that the compose file mounts |
| No `framed routing ip` line in the UPF log | `use_local_subscription_info` must be `no`, otherwise the SMF never asks the UDM for the subscription and the framed route is not signalled over N4 |
| `ipv4FrameRouteList` is empty in MySQL | The `UPDATE` targets DNN `oai` of subscriber `208950000000036`; adapt the JSON path if you use another DNN or subscriber |
| OAI gNB does not connect to AMF | Simple switch: `ran-conf/gnb.conf` must contain the current `oai-amf` container IP from `docker inspect`. eBPF: the AMF is pinned to `192.168.70.132` |
| OAI UE has no `oaitun_ue1` | Check `docker logs oai-nr-ue-basic` / `docker logs oai-nr-ue1`; the UE config needs a `uicc0.pdu_sessions` entry |
| Uplink works but downlink does not | The framed route is installed in the UPF but `oai-ext-dn` has no route to the framed subnet; check `docker exec oai-ext-dn ip route` |
| Framed subnet cannot reach external hosts on eBPF | Add the host policy routing rule from [section 5.7](#57-optional-reach-external-destinations-from-the-framed-subnet) |
