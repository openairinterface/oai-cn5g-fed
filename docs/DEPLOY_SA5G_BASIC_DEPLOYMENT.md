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

This tutorial deploys the basic OAI 5G Core with NRF, MySQL, AMF, SMF, UPF, AUSF, UDM, UDR, and an external data network container. It then validates end-to-end traffic with Duranta/OAI gNB and OAI NR-UE in RF simulator mode.

## At A Glance

| Item | Value |
| ---- | ----- |
| Goal | Deploy the basic OAI 5G Core and validate UE traffic with Duranta/OAI gNB and OAI NR-UE |
| Working directory | `oai-cn5g-fed/docker-compose` |
| Core compose file | `docker-compose-basic-nrf.yaml` |
| RFSIM RAN compose file | `docker-compose-oai-rfsim-basic.yaml` |
| Reference configuration | `conf/basic_nrf_config.yaml` |
| Subscription database | `database/oai_db2.sql` |
| Result folder used below | `/tmp/oai/basic-deployment` |

**Reading time**: ~20 minutes

**Replication time**: ~30-45 minutes, depending on image availability.

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

The OAI NR-UE configuration in [ran-conf/nr-ue.conf](../docker-compose/ran-conf/nr-ue.conf) uses IMSI `208950000000036`, DNN `oai`, SST `1`, and the default SD `FFFFFF`. The `oai` DNN subnet in [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml) is `12.1.1.128/25`, so the static address must be inside that subnet.

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

If you want a packet capture, start it after the Docker network exists:

```console
sudo tshark -i demo-oai \
  -f "not arp and not port 53" \
  -w /tmp/oai/basic-deployment/basic-core.pcap
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

If you selected static UE IP allocation in [section 2.1](#21-enable-static-ue-ip-allocation), the expected nrUE address is `12.1.1.130`. If you kept the default dynamic mode, the address should be in the `12.1.1.128/25` range.

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
docker-compose-host $: pkill tshark || true
docker-compose-host $: chmod 666 /tmp/oai/basic-deployment/*.pcap 2>/dev/null || true
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

## 6. Cleanup

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

## 7. Troubleshooting

| Symptom | First check |
| ------- | ----------- |
| Core containers are not healthy | `docker compose -f docker-compose-basic-nrf.yaml ps` and `docker logs <container>` |
| Static UE IP is not `12.1.1.130` | Confirm `use_local_subscription_info: no` and the `208950000000036` `SessionManagementSubscriptionData` entry in `database/oai_db2.sql` |
| OAI gNB does not connect to AMF | Confirm `ran-conf/gnb.conf` contains the current `oai-amf` container IP from `docker inspect` |
| OAI UE has no `oaitun_ue1` | Check `docker logs oai-nr-ue-basic` and confirm `oai-gnb-basic` is healthy |
| No traffic between UE and `oai-ext-dn` | Re-run host forwarding commands and check routes inside `oai-ext-dn` with `docker exec oai-ext-dn ip route` |

## 8. Report An Issue

When opening an issue, include:

1. The exact scenario: dynamic nrUE IP or static nrUE IP.
2. The commands used to start the core and RAN/UE.
3. The edited parts of `conf/basic_nrf_config.yaml` and any database changes.
4. Logs from the affected containers.
5. Packet captures from `demo-oai` when available.

For contribution workflow details, see [CONTRIBUTING.md](../CONTRIBUTING.md).
