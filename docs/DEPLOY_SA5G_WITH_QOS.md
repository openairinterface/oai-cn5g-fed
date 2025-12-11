<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">OpenAirInterface 5G Core Network Deployment with eBPF-UPF using docker-compose</font></b>
    </td>
  </tr>
</table>


**Reading time: ~ 30mins**

**Tutorial replication time: ~ 1hs**


**TABLE OF CONTENTS**

[[_TOC_]]

-----------------------------------------------------------------------------------------
# Quality of Service (QoS) with OAI 5G Core Network

This tutorial explains how to configure and test Quality of Service (QoS) in the OAI 5G Core network. QoS allows different treatment of traffic flows based on their requirements, prioritising certain traffic types over others to ensure an optimal user experience for critical applications.

## 1. Prerequisites

Create a folder where you can store all the result files of the tutorial and later compare them with our provided result files. We recommend creating exactly the same folder to not break the flow of commands afterwards.

Ensure that the following tools are installed and meet the required versions:

- **awk**: Version >= 5.1.0
  You can check the version of `awk` installed on your system using the following command:
  ``` shell
  awk --version
  ```
  If the version is lower than 5.1.0, update `awk` using your package manager (e.g., `sudo apt install gawk` on Ubuntu).

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: rm -rf /tmp/oai/qos-testing
```
-->

``` shell
docker-compose-host $: mkdir -p /tmp/oai/qos-testing
docker-compose-host $: chmod 777 /tmp/oai/qos-testing
```

## 2. Architecture Overview

The QoS framework in OAI 5G Core enables:
* Different traffic treatment based on 5QI (5G QoS Identifier) values
* Control over bitrates for downlink
* Definition of PCC (Policy and Charging Control) rules
* QoS enforcement at the UPF using eBPF datapath

```
                               +-------+
                               |  N6   |
                               +-------+
                                  ^
                                  | DL Packet
                                  |
                                  v
                          +---------------------+
                          | XDP Program (Set 1) |
                          | (Pre-processing)    |
                          +---------------------+
                                  |
                                  | XDP Program (Set 1)
                                  | (Pre-processing)
                                  |
                                  v
                          +---------------------+
                          | XDP Program (Set 2) |
                          |    (Enforce FAR)    |
                          +---------------------+
                                  |
                                  | QoS Enabled?
                                  |
                                  +-----------------+
                                  | Yes             | No (Bypass TC)
                                  |                 |
                                  v                 v
                          +-----------------+     (Directly to N3)
                          | N6 TC Ingress   |       |
                          | (QoS Operations,|       |
                          | Redirect to N3) |       |
                          +-----------------+       |
                                  |                 |
                                  v                 |
                          +-----------------+       |
                          | N3 TC Egress    |       |
                          | (QoS Operation) |       |
                          +-----------------+       |
                                  |                 |
                                  |                 |
                                  |                 |
                                  |<----------------+
                                  v
                               +-------+
                               |  N3   |
                               +-------+

```

## 3. Database Configuration

First, we need to configure the subscriber database with UEs having different QoS profiles in [mysql database file](../docker-compose/database/oai_db2.sql).

In the table `SessionManagementSubscriptionData` add the following entries with varying QoS settings. We put a static IP to make it easier to know the expected bitrate per IP addresss:

```sql
INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES
('208950000000033', '20895', '{\"sst\": 222, \"sd\": \"00007B\"}','{\"default\":{\"pduSessionTypes\":{ \"defaultSessionType\": \"IPV4\"},\"sscModes\": {\"defaultSscMode\": \"SSC_MODE_1\"},\"5gQosProfile\": {\"5qi\": 6,\"arp\":{\"priorityLevel\": 1,\"preemptCap\": \"NOT_PREEMPT\",\"preemptVuln\":\"NOT_PREEMPTABLE\"},\"priorityLevel\":1},\"sessionAmbr\":{\"uplink\":\"100Mbps\", \"downlink\":\"100Mbps\"},\"staticIpAddress\":[{\"ipv4Addr\": \"12.1.1.8\"}]}}');
```

## 4. PCF Policy Configuration

QoS in 5G is applied through policy configuration. We need to create several configuration files for the PCF. See the examples below.

### 4.1. Configure QoS Profiles

Create the [QoS data configuration file](../docker-compose/policies/qos/qos_data/qos_data.yaml):

```yaml
# QoS settings for non-GBR flows with different 5QI values
non-gbr-qos-5qi-9:
  5qi: 9
  arp:
    priorityLevel: 4
    preemptCap: NOT_PREEMPT
    preemptVuln: PREEMPTABLE
  priorityLevel: 80
  maxbrUl: "10Mbps"
  maxbrDl: "10Mbps"
```

### 4.2. Configure PCC Rules

Create the [PCC rules configuration file](../docker-compose/policies/qos/pcc_rules/pcc_rules.yaml):

```yaml
# PCC rules associating traffic flows with QoS profiles
non-gbr-rule-5qi-9:
  flowInfos:
    - flowDescription: permit out ip from any to assigned
      packetFilterUsage: true
  precedence: 10
  refQosData:
    - non-gbr-qos-5qi-9
```

### 4.3. Configure Policy Decisions

Create the [policy decisions configuration file](../docker-compose/policies/qos/policy_decisions/policy_decision.yaml):

```yaml
# Map UEs (by SUPI) to PCC rules
decision_supi1:
  supi_imsi: "208950000000033"
  pcc_rules:
    - non-gbr-rule-5qi-9
```

## 5. Core Network Configuration

### 5.1. Configure PCF to Use Policy Files

Update the PCF configuration in the [config file](../docker-compose/conf/basic_nrf_config_ebpf.yaml) file to point to our policy files:

```yaml
pcf:
  local_policy:
    policy_decisions_path: /openair-pcf/policies/policy_decisions
    pcc_rules_path: /openair-pcf/policies/pcc_rules
    traffic_rules_path: /openair-pcf/policies/traffic_rules
    qos_data_path: /openair-pcf/policies/qos_data
```

### 5.2. Enable QoS in UPF

Update the UPF configuration in the [config file](../docker-compose/conf/basic_nrf_config_ebpf.yaml) file to enable QoS enforcement:

```yaml
upf:
  support_features:
    enable_bpf_datapath: yes    # If "yes": BPF is used as datapath else simpleswitch is used
    enable_qos: yes             # Enable QoS enforcement at the UPF
  remote_n6_gw: oai-ext-dn
  upf_info:
    sNssaiUpfInfoList:
      - sNssai:
          sst: 222
          sd: "00007B"
        dnnUpfInfoList:
          - dnn: "default"
```

### 5.3. Update Docker-Compose File

Create a `docker-compose.yaml` file that includes volume mounts for the policy files:

```yaml
version: '3.8'
services:
  oai-pcf:
    volumes:
      - ./policies/qos/policy_decisions:/openair-pcf/policies/policy_decisions
      - ./policies/qos/pcc_rules:/openair-pcf/policies/pcc_rules
      - ./policies/qos/qos_data:/openair-pcf/policies/qos_data
```

We will use `docker-compose-basic-nrf-qos.yaml` which already has the volume mounts applied.

## 6. Network Function Deployment

In the previous tutorial we explain how to deploy the core network using our [python deployer](../docker-compose/core-network.py). Here we will only provide quick commands needed to deploy the core network, to learn how to use the python deployer please follow [this page](./DEPLOY_SA5G_MINI_WITH_GNBSIM.md).

- Start the core network components with QoS enabled

As a first timer, we recommend to first run without any PCAP capture.

``` console
docker-compose-host $: python3 core-network.py --type start-basic-qos --scenario 1
```

For CI purposes, we are deploying with an automated PCAP capture on the docker network.

**REMEMBER: if you are planning to run your CN5G deployment for a long time, the PCAP file can become huge!**

``` shell
docker-compose-host $: python3 core-network.py --type start-basic-qos --scenario 1 --capture /tmp/oai/qos-testing/qos-testing.pcap
```
<details>
<summary>The output will look like this:</summary>

```
[2023-08-10 15:43:22,365] root:DEBUG:  Starting 5gcn components...
[2023-08-10 15:43:22,365] root:DEBUG: docker-compose -f docker-compose-basic-nrf-qos.yaml up -d
Creating network "demo-oai-public-net" with the default driver
Creating mysql ...
Creating oai-nrf ...
Creating oai-udr ...
Creating oai-udm ...
Creating oai-ext-dn ...
Creating oai-ausf ...
Creating mysql ... done
Creating oai-nrf ... done
Creating oai-udr ... done
Creating oai-udm ... done
Creating oai-ausf ... done
Creating oai-ext-dn ... done
Creating oai-amf ...
Creating oai-amf ... done
Creating oai-upf ...
Creating oai-upf ... done
Creating oai-smf ...
Creating oai-smf ... done
Creating oai-pcf ...
Creating oai-pcf ... done
```
</details>

If you want to use docker compose directly to deploy OAI 5G Core

```console
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-qos.yaml up -d
```

Verify that all containers are running correctly:

```console
docker-compose-host $: docker ps
```

## 7. Testing QoS Enforcement

For testing QoS, we'll use UERANSIM to simulate UEs with different QoS profiles and measure the achieved throughput using iperf3.

### 7.1. Deploy UERANSIM

The configurations are as follows:
- `ueransim/oai-cn5g-gnb.yaml`: gNB configuration
- `ueransim/ue-5qi-1.yaml`: UE configuration for the 5QI-1 UE (3 Mbps)
- `ueransim/ue-5qi-3.yaml`: UE configuration for the 5QI-3 UE (100 Mbps)

You can create more UEs by creating a UE configuration file and updating the `docker-compose-ueransim-qos.yaml` to add the UE.

Now deploy UERANSIM:

``` shell
docker-compose-host $: docker-compose -f docker-compose-ueransim-qos.yaml up -d
```

### 7.2. Test QoS Enforcement

First, check that the UE is registered and has an IP address:

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: sleep 10
```
-->

``` shell
docker-compose-host $: docker exec ueransim-ue-5qi-1 ping -c 3 -I uesimtun0 192.168.72.135
```


Now, start an iperf3 server in the UE to test Downlink QoS enforcement:

``` shell
docker-compose-host $: docker exec -d ueransim-ue-5qi-1 iperf3 -s -B 12.1.1.10
```

Next, run an iperf3 client in the UE to test throughput:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -c 12.1.1.10 -B 192.168.72.135 -J > /tmp/oai/qos-testing/iperf_result_ue-5qi-1.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-testing/iperf_result_ue-5qi-1.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-testing/iperf_result_ue-5qi-1.json | awk '{if($1>=2.5 && $1<=3.5){print "Max bitrate "$1" Mbps is within range (2.5-3.5)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (2.5-3.5)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

<details>
<summary>The output will look like this:</summary>

```
Connecting to host 12.1.1.10, port 5201
[  5] local 192.168.72.135 port 48777 connected to 12.1.1.10 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec   411 KBytes  3.36 Mbits/sec    0   47.4 KBytes
[  5]   1.00-2.00   sec   382 KBytes  3.13 Mbits/sec    0   64.5 KBytes
[  5]   2.00-3.00   sec   425 KBytes  3.48 Mbits/sec    0   80.3 KBytes
[  5]   3.00-4.00   sec   379 KBytes  3.11 Mbits/sec    0   97.4 KBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-4.00   sec  1.56 MBytes  3.27 Mbits/sec    0             sender
[  5]   0.00-4.33   sec  1.42 MBytes  2.75 Mbits/sec                  receiver

iperf Done.
```
</details>

Notice how the throughput stays close to but below 20 Mbps, which is the configured limit for this UE.

### 7.3. Test Different QoS Profiles

You can repeat the test with different UEs to confirm that the QoS limits are enforced correctly. You'll need to create additional UE configurations and modify the docker-compose file for UERANSIM to include them.

For example, to test the UE with 5QI-3 (100 Mbps limit):

The throughput should be limited to approximately 100 Mbps for this UE.

Now, start an iperf3 server in the UE to test Downlink QoS enforcement:

``` shell
docker-compose-host $: docker exec -d ueransim-ue-5qi-3 iperf3 -s -B 12.1.1.9
```

Next, run an iperf3 client in the UE to test throughput:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -c 12.1.1.9 -B 192.168.72.135 -J > /tmp/oai/qos-testing/iperf_result_ue-5qi-3.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-testing/iperf_result_ue-5qi-3.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-testing/iperf_result_ue-5qi-3.json | awk '{if($1>=95 && $1<=105){print "Max bitrate "$1" Mbps is within range (95-105)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (95-105)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

<details>
<summary>The output will look like this:</summary>

```
Connecting to host 12.1.1.9, port 5201
[  5] local 192.168.72.135 port 44757 connected to 12.1.1.9 port 5201
[ ID] Interval           Transfer     Bitrate         Retr  Cwnd
[  5]   0.00-1.00   sec  12.6 MBytes   106 Mbits/sec    0    591 KBytes
[  5]   1.00-2.00   sec  12.5 MBytes   105 Mbits/sec    0   1.13 MBytes
[  5]   2.00-3.00   sec  11.2 MBytes  94.4 Mbits/sec   50   1008 KBytes
[  5]   3.00-4.00   sec  11.2 MBytes  94.4 Mbits/sec    0   1.09 MBytes
- - - - - - - - - - - - - - - - - - - - - - - - -
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-4.00   sec  47.6 MBytes  99.8 Mbits/sec   50             sender
[  5]   0.00-4.14   sec  45.2 MBytes  91.6 Mbits/sec                  receiver

iperf Done.
```
</details>
### 7.4. Test Multiple QoS Flows on a Single PDU Session

A single PDU session can support multiple QoS flows with different QoS parameters (QERs) based on Service Data Flows (SDFs) and their precedence rules. In this test, we verify that different QoS limits are correctly enforced for traffic on different ports within the same PDU session.

For this test, we have configured three QoS rules for the same UE:

- **gbr-rule-5qi-1**: 3 Mbps (default QoS flow, all other traffic)
- **gbr-rule-iperf3-8080**: 20 Mbps (traffic on port 8080)
- **gbr-rule-iperf3-8081**: 10 Mbps (traffic on port 8081)

#### Test 1: Traffic on Port 8080 (Expected: ~20 Mbps)

Start an iperf3 server on the UE listening on port 8080:

``` shell
docker-compose-host $: docker exec -d ueransim-ue-5qi-1 iperf3 -s -B 12.1.1.10 -p 8080
```

Start an iperf3 client on the data network to generate traffic to port 8080:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -c 12.1.1.10 -p 8080 -J > /tmp/oai/qos-testing/iperf_result_ue-5qi-1-8080.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-testing/iperf_result_ue-5qi-1-8080.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-testing/iperf_result_ue-5qi-1-8080.json | awk '{if($1>=19 && $1<=21.5){print "Max bitrate "$1" Mbps is within range (19-21.5)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (19-21.5)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

The throughput should be limited to approximately 20 Mbps, as configured in the gbr-rule-iperf3-8080 policy.

#### Test 2: Traffic on Port 8081 (Expected: ~10 Mbps)

Start an iperf3 server on the UE listening on port 8081:

``` shell
docker-compose-host $: docker exec -d ueransim-ue-5qi-1 iperf3 -s -B 12.1.1.10 -p 8081
```

Start an iperf3 client on the data network to generate traffic to port 8081:

``` shell
docker-compose-host $: docker exec oai-ext-dn iperf3 -t 4 -c 12.1.1.10 -p 8081 -J > /tmp/oai/qos-testing/iperf_result_ue-5qi-1-8081.json
```

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: jq -e '.end.sum_sent and .end.sum_sent.bits_per_second' /tmp/oai/qos-testing/iperf_result_ue-5qi-1-8081.json > /dev/null 2>&1 && jq -r '.end.sum_sent.bits_per_second / 1000000' /tmp/oai/qos-testing/iperf_result_ue-5qi-1-8081.json | awk '{if($1>=9 && $1<=11){print "Max bitrate "$1" Mbps is within range (9-11)"; exit 0}else{print "Max bitrate "$1" Mbps is outside range (9-11)"; exit 1}}' || { echo "Required fields .end.sum_sent or .end.sum_sent.bits_per_second not found"; exit 1; }
```
-->

The throughput should be limited to approximately 10 Mbps, as configured in the gbr-rule-iperf3-8081 policy.

These tests demonstrate that the UPF correctly enforces different QoS parameters for different traffic flows within a single PDU session based on port-based traffic filtering rules.

## 8. Log Collection

<!---
For CI purposes please ignore these lines
``` shell
docker-compose-host $: docker-compose -f docker-compose-ueransim-qos.yaml stop -t 2
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-qos.yaml stop -t 30
```
-->

- **Stop PCAP collection**: Stop the wireshark or tshark process on the docker-compose-host.

``` console
docker-compose-host $: pkill tshark
```

- **Collect the logs of all the components**:

``` shell
docker-compose-host $: docker logs oai-amf > /tmp/oai/qos-testing/amf.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/qos-testing/smf.log 2>&1
docker-compose-host $: docker logs oai-nrf > /tmp/oai/qos-testing/nrf.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/qos-testing/upf.log 2>&1
docker-compose-host $: docker logs oai-udr > /tmp/oai/qos-testing/udr.log 2>&1
docker-compose-host $: docker logs oai-udm > /tmp/oai/qos-testing/udm.log 2>&1
docker-compose-host $: docker logs oai-ausf > /tmp/oai/qos-testing/ausf.log 2>&1
docker-compose-host $: docker logs oai-pcf > /tmp/oai/qos-testing/pcf.log 2>&1
docker-compose-host $: docker logs oai-ext-dn > /tmp/oai/qos-testing/ext-dn.log 2>&1
docker-compose-host $: docker logs ueransim-gnb > /tmp/oai/qos-testing/gnb.log 2>&1
docker-compose-host $: docker logs ueransim-ue-5qi-1 > /tmp/oai/qos-testing/ue-5qi-1.log 2>&1
docker-compose-host $: docker logs ueransim-ue-5qi-3 > /tmp/oai/qos-testing/ue-5qi-3.log 2>&1
```

## 9. Undeploy the network functions

### 9.1. Undeploy UERANSIM

``` shell
docker-compose-host $: docker-compose -f docker-compose-ueransim-qos.yaml down
```
<details>
<summary>The output will look like this:</summary>

``` console
Stopping ueransim-ue-5qi-8 ... done
Stopping ueransim-gnb     ... done
Removing ueransim-ue-5qi-8 ... done
Removing ueransim-gnb     ... done
Network demo-oai-public-net is external, skipping
```
</details>

### 9.2. Undeploy the core network

``` shell
docker-compose-host $: python3 core-network.py --type stop-basic-qos --scenario 1
```
<details>
<summary>The output will look like this:</summary>

``` console
[2023-08-10 16:05:54,271] root:DEBUG:  UnDeploying OAI 5G core components....
[2023-08-10 16:05:54,272] root:DEBUG: docker-compose -f docker-compose-basic-nrf-qos-qos.yaml down
Stopping oai-pcf    ...
Stopping oai-upf    ...
Stopping oai-smf    ...
Stopping oai-amf    ...
Stopping oai-ausf   ...
Stopping oai-udm    ...
Stopping oai-udr    ...
Stopping oai-ext-dn ...
Stopping oai-nrf    ...
Stopping mysql      ...
Removing oai-pcf    ... done
Removing oai-upf    ... done
Removing oai-smf    ... done
Removing oai-amf    ... done
Removing oai-ausf   ... done
Removing oai-udm    ... done
Removing oai-udr    ... done
Removing oai-ext-dn ... done
Removing oai-nrf    ... done
Removing mysql      ... done
Removing network demo-oai-public-net

[2023-08-10 16:05:55,711] root:DEBUG:  OAI 5G core components are UnDeployed....
```
</details>

## 10. Conclusion

You have successfully configured and tested QoS enforcement in the OAI 5G Core network. This tutorial demonstrated how to:

1. Configure subscriber QoS profiles in the database
2. Set up PC
