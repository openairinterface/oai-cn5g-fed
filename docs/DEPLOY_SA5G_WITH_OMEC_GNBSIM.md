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
      <b><font size = "5">OpenAirInterface 5G Core Network Deployment and Testing with omec-gnbsim</font></b>
    </td>
  </tr>
</table>


![SA Demo](./images/5gcn_vpp_upf_omec_gnbsim.png)

Note: the diagram above shows the VPP-UPF variant. This tutorial now uses the
`basic` deployment, which is the same call flow with `oai-upf` and a single network.

**Reading time: ~ 30mins**

**Tutorial replication time: ~ 1h30mins**

Note: In case readers are interested in deploying debuggers/developers core network environment with more logs please follow [this tutorial](./DEBUG_5G_CORE.md)

**TABLE OF CONTENTS**

1.  Pre-requisites
2.  [Building Container Images](https://github.com/openairinterface/oai-cn5g-fed/-/blob/omec-gnbsim-tutorial/docs/BUILD_IMAGES.md)/[Pull the container images](https://github.com/openairinterface/oai-cn5g-fed/-/blob/omec-gnbsim-tutorial/docs/RETRIEVE_OFFICIAL_IMAGES.md)
3.  Configuring Host Machines
4.  Configuring OAI 5G Core Network Functions
5.  Deploying OAI 5G Core Network
6.  [Getting a `omec-gnbsim` docker image](#6-getting-a-omec-gnbsim-docker-image)
7.  [Executing `omec-gnbsim` Scenario](#7-executing-the-omec-gnbsim-scenario)
8.  [Analysing Scenario Results](#8-analysing-the-scenario-results)
9.  [Trying some advanced stuff](#9-trying-some-advanced-stuff)

* In this demo the image tags which were used are listed below, follow the [Building images](./BUILD_IMAGES.md) to build images with below tags. When pulling images of network functions from dockerhub pull images for `develop` tag

This tutorial is an extension of a previous tutorial: [testing a `basic` deployment](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md).

Moreover, there are various other opensource gnb/ue simulator tools that are available for SA5G test. In this tutorial, we use an opensource simulator tool called `omec-gnbsim`. With the help of `omec-gnbsim` tool, we can perform basic SA5G test by simulating multiple gnb & ue.

##### About omec-gnbsim -

[omec-gnbsim](https://github.com/omec-project/gnbsim.git) is tool  under SD-Core project of Open Networking Foundation (ONF). It provides a tool to simulate gNodeB and UE by generating NAS and NGAP messages for the configured UEs and call flows. The tool currently supports simulation profiles for the following
procedures :

    1. Registration                              -> Validated with OAI-5GCN
    2. UE Initiated PDU Session Establishment    -> Validated with OAI-5GCN
    3. UE Initiated De-registration              -> Validated with OAI-5GCN
    4. AN Release                                -> Validated with OAI-5GCN
    5. UE Initiated Service Request              -> Validated with OAI-5GCN
    6. N/W triggered PDU Session Release         -> Not supported by OAI-5GCN
    7. UE Requested PDU Session Release          -> Validated with OAI-5GCN
    8. N/W triggered UE Deregistration           -> Not supported by OAI-5GCN

Let's begin !!

* Steps 1 to 5 are the same as in the [`basic` deployment tutorial](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md). Please follow those steps to deploy the OAI 5G core network components.
* We deploy omec-gnbsim docker service on same host as of core network, so there is no need to create additional route as
we did for gnb-host.
* Before we proceed further for end-to-end SA5G test, make sure you have healthy docker services for OAI cn5g

## 1. Pre-requisites

Create a folder where you can store all the result files of the tutorial and later compare them with our provided result files, we recommend creating exactly the same folder to not break the flow of commands afterwards.

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: rm -rf /tmp/oai/omec-gnbsim
```
-->

#### NOTE on slice selection ####

omec-gnbsim does not include the optional requested NSSAI IE during the PDU session
resource setup procedure, so the network has to fall back on the subscriber's default
NSSAI. Earlier versions of this tutorial asked for `EXTERNAL_UDM=yes` on the
`oai-amf` service; that environment variable no longer exists, since the NFs are now
configured through [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml).
No extra configuration is needed for the `basic` deployment: with
`amf.support_features_options.enable_simple_scenario: no`, which is the default, the
AMF retrieves the slice selection subscription data from the UDM itself.

If PDU session establishment fails on the slice or the DNN, make the SMF take those
from the UDM rather than from its own configuration:

```yaml
smf:
  support_features:
    use_local_subscription_info: no
```

``` shell
docker-compose-host $: mkdir -p /tmp/oai/omec-gnbsim
docker-compose-host $: chmod 777 /tmp/oai/omec-gnbsim
```

## 5. Deploying OAI 5g Core Network
* We use the same wrapper script for docker compose as in the previous tutorials, this time with the `basic` deployment (`oai-upf` rather than `vpp-upf`). Use the help option to see how to use the script.

``` shell
docker-compose-host $: python3 ./core-network.py --type start-basic --scenario 1 --capture /tmp/oai/omec-gnbsim/omec-gnbsim.pcap
[2025-01-01 10:00:00,000] root:DEBUG:  Starting 5gcn components... Please wait....
[2025-01-01 10:00:00,000] root:DEBUG: docker compose -f docker-compose-basic-nrf.yaml up -d mysql
...
[2025-01-01 10:01:00,000] root:DEBUG:  All components are healthy, please see below for more details....
NAME         IMAGE                                        STATUS
mysql        mysql:8.0                                    Up (healthy)
oai-amf      oaisoftwarealliance/oai-amf:develop          Up (healthy)
oai-ausf     oaisoftwarealliance/oai-ausf:develop         Up (healthy)
oai-ext-dn   oaisoftwarealliance/trf-gen-cn5g:latest      Up (healthy)
oai-nrf      oaisoftwarealliance/oai-nrf:develop          Up (healthy)
oai-smf      oaisoftwarealliance/oai-smf:develop          Up (healthy)
oai-udm      oaisoftwarealliance/oai-udm:develop          Up (healthy)
oai-udr      oaisoftwarealliance/oai-udr:develop          Up (healthy)
oai-upf      oaisoftwarealliance/oai-upf:develop          Up (healthy)
[2025-01-01 10:01:00,000] root:DEBUG:  Checking if the containers are configured....
[2025-01-01 10:01:00,000] root:DEBUG:  OAI 5G Core network is configured and healthy....
```

More details in [section 5 of the `basic` deployment tutorial](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md).

## 6. Building a `omec-gnbsim` docker image

* Pull pre-built docker image 

``` console
docker-compose-host $: docker pull oaisoftwarealliance/omec-gnbsim:v2.3-fixes
```

OR 

* Build `omec-gnbsim` docker image
``` console
docker-compose-host $: git clone https://github.com/omec-project/gnbsim.git
docker-compose-host $: cd gnbsim/ && git checkout 1caccfcaac9b718d987aff378212614e4fe634fb
docker-compose-host $: go build
docker-compose-host $: make docker-build
```

## 7. Executing the `omec-gnbsim` Scenario

* Refer and update accordingly the Omec-gnbsim test profiles in [omec-gnbsim-config.yaml](../docker-compose/omec-gnbsim-config.yaml)
* The configuration parameters are preconfigured in [docker-compose-basic-nrf.yaml](../docker-compose/docker-compose-basic-nrf.yaml) and [docker-compose-omec-gnbsim.yaml](../docker-compose/docker-compose-omec-gnbsim.yaml) and one can modify them for the test.
* gnbsim runs in `singleInterface` mode here: the `basic` deployment has one network
  (`demo-oai-public-net`, 192.168.70.128/26), so N2 and N3 share the address
  192.168.70.171. The enabled profiles use DNN `default` with SST 222 / SD 00007B,
  matching the subscribers in the database, and ping the ext-DN at 192.168.70.135.
* Launch omec-gnbsim docker service

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: sleep 5
```
-->


``` shell
docker-compose-host $: docker compose -f docker-compose-omec-gnbsim.yaml up -d
 Container omec-gnbsim  Started
```

Verify docker logs

``` bash
docker-compose-host $: docker logs omec-gnbsim -f
```

After successful test, we should see selected test profiles are passed
```bash
:
2022-09-09T06:36:28Z [INFO][GNBSIM][Summary] Profile Name: profile1 , Profile Type: register
2022-09-09T06:36:28Z [INFO][GNBSIM][Summary] Ue's Passed: 5 , Ue's Failed: 0
:
:
2022-09-09T12:30:32Z [INFO][GNBSIM][Summary] Profile Name: profile2 , Profile Type: pdusessest
2022-09-09T12:30:32Z [INFO][GNBSIM][Summary] Ue's Passed: 5 , Ue's Failed: 0
:
:
2022-09-09T12:30:45Z [INFO][GNBSIM][Summary] Profile Name: profile5 , Profile Type: deregister
2022-09-09T12:30:45Z [INFO][GNBSIM][Summary] Ue's Passed: 2 , Ue's Failed: 0
:

```
## Stop the core network and gnbsim

``` shell
docker-compose-host $: docker compose -f docker-compose-omec-gnbsim.yaml down
docker-compose-host $: python3 ./core-network.py --type stop-basic --scenario 1
```


## 8. Analysing the Scenario Results

| Pcap/log files                                                                             |
|:------------------------------------------------------------------------------------------ |
| [omec-gnbsim-logs.txt](./results/omec-gnbsim/omec-gnbsim-logs.txt) |
| [5gcn-deployment-omec-gnbsim.pcapng](./results/omec-gnbsim/pcap/5gcn-deployment-omec-gnbsim.pcapng) |


<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: sleep 15
```
-->

