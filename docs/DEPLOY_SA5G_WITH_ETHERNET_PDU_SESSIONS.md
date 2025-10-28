# Ethernet PDU Sessions with OAI 5G Core Network

This tutorial explains how to configure and use Ethernet PDU sessions with the OAI 5G Core network. Ethernet PDU sessions allow transporting Ethernet frames between UE and Data Network (DN) through the 5G core, enabling various use cases like enterprise networking and industrial IoT applications.

## 1. Prerequisites


Create a folder where you can store all the result files of the tutorial and later compare them with our provided result files, we recommend creating exactly the same folder to not break the flow of commands afterwards

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: rm -rf /tmp/oai/ethernet-pdu-sessions
```
-->

``` shell
docker-compose-host $: mkdir -p /tmp/oai/ethernet-pdu-sessions
docker-compose-host $: chmod 777 /tmp/oai/ethernet-pdu-sessions
```

## 2. Architecture Overview

The Ethernet PDU session support in OAI 5G Core enables:
* Ethernet frame forwarding between UE and Data Network
* Proper handling of Ethernet PDU session establishment procedures
* Support for multiple PDU session types simultaneously (IPv4, IPv6, Ethernet)

![Architecture](images/5gcn_ethernet_pdu_session.png)

## 3. Database Configuration

First, we need to configure the subscriber database to support Ethernet PDU sessions. Update your database with a UE subscription that includes PDU session type "ETHERNET".

 In the table `SessionManagementSubscriptionData` add below entries. Execute the following SQL statement to insert a UE with Ethernet PDU session support:

```sql
INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES
('208950000000035', '20895', '{\"sst\": 222, \"sd\": \"00007B"}','{\"default\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"ETHERNET\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"150Mbps\", \"downlink\":\"150Mbps\"}}, \"ethernet\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"ETHERNET\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"150Mbps\", \"downlink\":\"150Mbps\"}}}');
```

## 4. UPF Configuration

Update the UPF configuration to support Ethernet PDU sessions. Edit the `basic_nrf_config_ebpf.yaml` file:

```yaml
upf:
  support_features:
    enable_bpf_datapath: yes    # If "on": BPF is used as datapath else simpleswitch is used, DEFAULT= off
    enable_eth_pdu: yes      # If "on": ETHERNET PDU sessions are supported, DEFAULT= off

dnns:
  - dnn: "oai"
    pdu_session_type: "IPV4"
    ipv4_subnet: "12.1.1.128/25"
  - dnn: "oai.ipv4"
    pdu_session_type: "IPV4"
    ipv4_subnet: "12.1.1.64/26"
  - dnn: "default"
    pdu_session_type: "ETHERNET"
    ipv4_subnet: "12.1.1.0/26"
  - dnn: "ims"
    pdu_session_type: "IPV4V6"
    ipv4_subnet: "14.1.1.2/24"
```

Note that for Ethernet PDU sessions, the `ipv4_subnet` field is not actually used but must be present in the configuration for compatibility.

## 5. Network Function Deployment

In the previous tutorial we explain how to deploy the core network using our [python deployer](../docker-compose/core-network.py). Here we will only provide quick commands needed to deploy the core network, to learn how to use the python deployer please follow [this page](./DEPLOY_SA5G_MINI_WITH_GNBSIM.md).

- Start the core network components, check which scenario you are using with nrf or without nrf

As a first timer, we recommend to first run without any PCAP capture.

``` console
docker-compose-host $: python3 core-network.py --type start-basic-ebpf --scenario 1
```

For CI purposes, we are deploying with an automated PCAP capture on the docker network.

**REMEMBER: if you are planning to run your CN5G deployment for a long time, the PCAP file can become huge!**

``` shell
docker-compose-host $: python3 core-network.py --type start-basic-ebpf --scenario 1 --capture /tmp/oai/ethernet-pdu-sessions/ethernet-pdu-sessions.pcap
```
<details>
<summary>The output will look like this:</summary>

</details>

If you want to use docker compose directly to deploy OAI 5G Core

```console
docker-compose -f docker-compose-basic-nrf-ebpf.yaml up -d
```

Verify that all containers are running correctly:

```console
docker ps
```

## 6. Testing Ethernet PDU Sessions

We'll use the cn5g-tester docker image to verify the Ethernet PDU session functionality. The cn5g-tester will send control plane messages to establish an Ethernet PDU Session and it will send ping packets towards the data network (oai-ext-dn) and wait for responses. Users can replace the tester with an gNB and UE that supports Ethernet PDU sessions.


1. Deploy the OAI gNB:

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml up -d oai-gnb
```

2. Deploy the OAI UE with Ethernet PDU session configured

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml up -d oai-nr-ue3
```

3. First, check that the UE is registered and has Ethernet tap interface:

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: sleep 10
```
-->

``` shell
docker-compose-host $: docker exec -it oai-nr-ue3 ip a | grep oaitap_ue0
```

Install arping
``` shell
docker-compose-host $: docker exec -it oai-nr-ue3 apt update -y
docker-compose-host $: docker exec -it oai-nr-ue3 apt install arping -y
```

3. Send Ethernet traffic using arping

Assign IP address to tap device on OAI UE

``` shell
docker-compose-host $: docker exec -it oai-nr-ue3 ip addr add 192.168.72.140/26 dev oaitap_ue0
```

Set interface UP
``` shell
docker-compose-host $: docker exec -it oai-nr-ue3 ip link set dev oaitap_ue0 up
```

Send ARP ping packets
```console
docker-compose-host $: docker exec -it oai-nr-ue3 arping -c 2 -I oaitap_ue0 192.168.72.135
```
<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: docker exec -it oai-nr-ue3 arping -c 2 -I oaitap_ue0 192.168.72.135 > /tmp/oai/ethernet-pdu-sessions/oai-nr-ue3-arping.log 2>&1
```
-->

If the test is successful, the script will exit with code 0 and display success messages. Otherwise, it will exit with an error code and display error messages.

<details>
<summary>The output will look like this:</summary>


</details>

## 7. Log Collection

<!---
For CI purposes please ignore these lines
``` shell
docker-compose-host $: docker exec -it oai-upf sh -c 'timeout 2s cat /sys/kernel/debug/tracing/trace_pipe || true' > /tmp/oai/ethernet-pdu-sessions/upf-ebpf-trace-pipe.log 2>&1
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml stop -t 2
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-ebpf.yaml stop -t 30
```
-->

- **Stop PCAP collection**: Stop the wireshark or tshark process on the docker-compose-host.

``` console
docker-compose-host $: pkill tshark
```

- **Collect the logs of all the components**:

``` shell
docker-compose-host $: docker logs oai-amf > /tmp/oai/ethernet-pdu-sessions/amf.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/ethernet-pdu-sessions/smf.log 2>&1
docker-compose-host $: docker logs oai-nrf > /tmp/oai/ethernet-pdu-sessions/nrf.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/ethernet-pdu-sessions/upf.log 2>&1
docker-compose-host $: docker logs oai-udr > /tmp/oai/ethernet-pdu-sessions/udr.log 2>&1
docker-compose-host $: docker logs oai-udm > /tmp/oai/ethernet-pdu-sessions/udm.log 2>&1
docker-compose-host $: docker logs oai-ausf > /tmp/oai/ethernet-pdu-sessions/ausf.log 2>&1
docker-compose-host $: docker logs oai-ext-dn > /tmp/oai/ethernet-pdu-sessions/ext-dn.log 2>&1
docker-compose-host $: docker logs oai-gnb > /tmp/oai/ethernet-pdu-sessions/oai-gnb.log 2>&1
docker-compose-host $: docker logs oai-nr-ue3 > /tmp/oai/ethernet-pdu-sessions/oai-nr-ue3.log 2>&1
```

## 8. Undeploy the network functions

### 8.1. Undeploy the ran emulator

``` shell
docker-compose-host $: docker-compose -f docker-compose-oai-rfsim-ebpf.yaml down -t 0
```
<details>
<summary>The output will look like this:</summary>

``` console
Stopping gnbsim ... done
Found orphan containers (oai-nrf, oai-ausf, oai-smf, oai-udr, oai-upf, mysql, oai-amf, oai-udm, oai-ext-dn) for this project.
Removing gnbsim ... done
Network demo-oai-public-net is external, skipping
```
</details>

### 8.2. Undeploy the core network

``` shell
docker-compose-host $: python3 core-network.py --type stop-basic-ebpf --scenario 1
```
<details>
<summary>The output will look like this:</summary>

``` console
[2023-07-13 13:07:54,271] root:DEBUG:  UnDeploying OAI 5G core components....
[2023-07-13 13:07:54,272] root:DEBUG: docker-compose -f docker-compose-basic-nrf-ebpf.yaml down -t 0
Removing oai-upf    ...
Removing oai-smf    ...
Removing oai-amf    ...
Removing oai-ausf   ...
Removing oai-udm    ...
Removing oai-udr    ...
Removing oai-ext-dn ...
Removing oai-nrf    ...
Removing mysql      ...
Removing oai-udr    ... done
Removing oai-smf    ... done
Removing oai-upf    ... done
Removing oai-ausf   ... done
Removing oai-nrf    ... done
Removing oai-udm    ... done
Removing mysql      ... done
Removing oai-ext-dn ... done
Removing oai-amf    ... done
Removing network demo-oai-public-net

[2023-07-13 13:07:55,711] root:DEBUG:  OAI 5G core components are UnDeployed....
```
</details>

- If you replicate then your log files and pcap file will be present in `/tmp/oai/ethernet-pdu-sessions/`. If you want to compare it with our provided logs and pcaps, then follow the next section


## 9. Conclusion

You have successfully configured and tested Ethernet PDU sessions with the OAI 5G Core. This functionality allows your 5G network to transport Ethernet frames natively, opening up possibilities for various enterprise and industrial use cases.

For more information on the implementation details, refer to the [UPF Merge Request](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf/-/merge_requests/71) that added this functionality.