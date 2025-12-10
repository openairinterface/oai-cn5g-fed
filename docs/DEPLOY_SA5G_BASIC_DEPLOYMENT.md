<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">OpenAirInterface 5G Core Network Basic Deployment using Docker-Compose</font></b>
    </td>
  </tr>
</table>


![SA Demo](./images/docker-compose/5gCN-basic.jpg)

**OVERVIEW**

This tutorial will help in understanding how to deploy a `basic` OAI core network using docker-compose. The recommended hardware to install the above core network setting is

- 4 CPU
- 16GiB RAM
- Minimum 1.5 GiB of free storage for docker images

Please follow the tutorial step by step to create a stable working testbed. You can use this tutorial to deploy OAI-5G core and test it with oai-gNB and oai-nr-ue.


**Reading time**: ~ 20 mins

**Tutorial replication time**: ~ 30 mins


**Note**

- In case readers are interested in deploying debuggers/developers core network environment with more logs please follow [this tutorial](./DEBUG_5G_CORE.md).
- In this tutorial we have considered two different host machines, `docker-compose-host` as the host machine to deploy core network functions and `gNB-host` as the gNB host machine.


**TABLE OF CONTENTS**

[[_TOC_]]

## 1. Basic Deployment Flavours ##

The Basic functional 5g core network can be deployed into 2 scenarios:

    - Scenario I:  AMF, SMF, UPF (SPGWU), NRF, UDM, UDR, AUSF, MYSQL
    - Scenario II:  AMF, SMF, UPF (SPGWU), UDM, UDR, AUSF, MYSQL

## 2. Pre-requisites ##

The container images are built using `docker build` command on Ubuntu 18.04 host machine. The base image for all the containers is Ubuntu 18.04.

The required software and their respected versions are listed below. To replicate the testbed use these versions.

| Software                   | Version                |
|:-------------------------- |:-----------------------|
| docker engine              | 29.1.2                 |
| Host operating system      | Ubuntu 22.04/24.04 LTS |
| tshark                     | 4.6                    |
| wireshark                  | 4.6                    |

### 2.1. Networking considerations ###

Most of the times the `docker-compose-host` machine is not configured with packet forwarding. It can be enabled using the command below (if you have already done it in any other section then don't repeat).

**This is the most important step towards end-to-end connectivity.**

```console
## run the commands on docker-compose-host
sudo sysctl net.ipv4.conf.all.forwarding=1
## run the commands on docker-compose-host
sudo iptables -P FORWARD ACCEPT
```

## 3. Network Function Container Images ##

In this demo the network function branch and tags which were used are listed below, follow the [Retrieving images](./RETRIEVE_OFFICIAL_IMAGES.md) or the [Building images](./BUILD_IMAGES.md) 

## 4. Configuring Host Machines ##

All the network functions are connected using `demo-oai` bridge.

There are two ways to create this bridge, either manually or automatically using docker-compose.

* The manual version will allow packet capturing while network functions are getting deployed. So the initial tested setup packets can be captured for debugging purposes or checking if network functions registered properly to NRF.
* The second option of automatic deployment is good when initial packet capture is not important.

### 4.1 Creating bridge manually ###

Since this is not the `default` behavior, you **have to** edit the docker-compose file.

- The bottom section of [docker-compose file](../docker-compose/docker-compose-mini-nrf.yaml) SHALL look like this:

```
    networks:
          public_net:
              external:
                  name: demo-oai-public-net
        # public_net:
        #     driver: bridge
        #     name: demo-oai-public-net
        #     ipam:
        #         config:
        #             - subnet: 192.168.70.128/26
        #     driver_opts:
        #         com.docker.network.bridge.name: "demo-oai"
```

- The `docker-compose-host` machine needs to be configured with `demo-oai` bridge before deploying core network components. To capture initial message exchange between network functions.

    ```console
    docker-compose-host $: docker network create \
      --driver=bridge \
      --subnet=192.168.70.128/26 \
      -o "com.docker.network.bridge.name"="demo-oai" \
      demo-oai-public-net
    455631b3749ccd6f10a366cd1c49d5a66cf976d176884252d5d88a1e54049bc5
    docker-compose-host $: ifconfig demo-oai
    demo-oai: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
            inet 192.168.70.129  netmask 255.255.255.192  broadcast 192.168.70.191
            RX packets 0  bytes 0 (0.0 B)
            RX errors 0  dropped 0  overruns 0  frame 0
            TX packets 0  bytes 0 (0.0 B)
            TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
    docker-compose-host $: docker network ls
    NETWORK ID          NAME                  DRIVER              SCOPE
    d2d34e05bb2d        bridge                bridge              local
    455631b3749c        demo-oai-public-net   bridge              local
    ```

### 4.2 Create bridge automatically ###

- Though the bridge can be automatically created using docker-compose file if there is no need to capture initial packets.

This is the `default` version in the [docker-compose-basic-nrf.yaml](../docker-compose/docker-compose-basic-nrf.yaml).

The bottom section SHALL look like this:

    ```
    networks:
        # public_net:
        #     external:
        #         name: demo-oai-public-net
          public_net:
              driver: bridge
              name: demo-oai-public-net
              ipam:
                  config:
                      - subnet: 192.168.70.128/26
              driver_opts:
                  com.docker.network.bridge.name: "demo-oai"
    ```

### 4.3 In case you forgot, the section below is for both manual and automatic network creation. ###

- If the `docker-compose-host` machine is not configured with packet forwarding then it can be done using the command below (**important step**),

    ```console
    ## run the commands on docker-compose-host
    sudo sysctl net.ipv4.conf.all.forwarding=1
    ## run the commands on docker-compose-host
    sudo iptables -P FORWARD ACCEPT
    ```

- The `gNB-host` needs to be configured with a route to reach `docker-compose-host`. Assuming `gNB-host` physical interface which is connected with `docker-compose-host` is NIC1 and the ip-address of this interface is IP_ADDR_NIC1 then,

    ```console
    #execute the command on gNB host
    sudo ip route add route 192.168.70.128/26 \
                           via IP_ADDR_NIC1\
                           dev NIC1_NAME
    ```

- To verify, ping the ip-address of the `docker-compose-host` interface connected to demo-oai bridge, if possible also ping amf from the gNB host machine.

    ```console
    #execute the command on gNB host
    ping 192.168.70.129
    ```

## 5. Configuring the OAI-5G Core Network Functions ##

5G core network has two architectures service based or reference point which makes the NRF component optional, similarly you can choose to deploy the OAI core network components with or without NRF. Additionally in cloud native world it is preferred to provide a Fully Qualified Domain Name (FQDN) to a service rather than static ip-address. Each of our network functions can communicate with other core network function's using ip-address or FQDN. For example, AMF can register to NRF either with NRFs ip-address or FQDN.

Configuring network functions with static ip-addresses is preferred for bare-metal deployment of network functions. Whereas for docker-compose or helm chart based deployment it is better to use FQDN of network functions. In the docker-compose file you will see each network function is configured with both ip-address and FQDN, but if you are using FQDN then the code of network function will ignore the ip-address configuration.

In docker-compose the [service-name](https://docs.docker.com/compose/compose-file/#services-top-level-element) is actually the FQDN of the service.

### 5.1. Core Network Configuration ###

The configuration is in [conf/basic_nrf_config.yaml](../docker-compose/conf/basic_nrf_config.yaml)

### 5.2. User Subscription Profile ###

There are two ways to configure the User Subscription Profile,

1. Pre-configure all the users in the [database file](../docker-compose/database/oai_db2.sql). This way when the core network starts it will have all the users.
2. Add a new user when the core-network is already running.

For the first method, you have to edit the [database file](../docker-compose/database/oai_db2.sql) and add or change the entries in table `AuthenticationSubscription`, either remove the already present entries or add a new one like below:

```sql
INSERT INTO `AuthenticationSubscription` (`ueid`, `authenticationMethod`, `encPermanentKey`, `protectionParameterId`, `sequenceNumber`, `authenticationManagementField`, `algorithmId`, `encOpcKey`, `encTopcKey`, `vectorGenerationInHss`, `n5gcAuthMethod`, `rgAuthenticationInd`, `supi`) VALUES
('208950000000031', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{\"sqn\": \"000000000020\", \"sqnScheme\": \"NON_TIME_BASED\", \"lastIndexes\": {\"ausf\": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '208950000000031'),
```

Make sure you edit the IMSI, opc and key according to the settings of your user device.


## 6. Deploying OAI 5G Core Network ##

```console
docker-compose -f ../docker-compose/docker-compose-basic-nrf.yaml up -d
# to follow if the components are healthy or not
docker-compose -f ../docker-compose/docker-compose-basic-nrf.yaml ps -a
```

```console
# To capture packets execute on core network host
sudo tshark -i demo-oai
     -f "not arp and not port 53 and not host archive.ubuntu.com and not host security.ubuntu.com" \
     -w /tmp/5gcn-basic-deployment-nrf.pcap
```

- Explanation on the capture filter:
   *  `not arp` : Not capturing ARP traffic
   *  `not port 53` : Not capturing DNS traffic
   *  `not host archive.ubuntu.com and not host security.ubuntu.com` : Not capturing traffic from `oai-ext-dn` container when installing tools
- To stop the core network you can use:

```console
docker-compose -f ../docker-compose/docker-compose-basic-nrf.yaml down -t2
```

Your core network is ready you can use it.

You can use `oai-ext-dn` to perform iperf or ping towards the UE, just make sure that the subnet used by the UE is properly defined in the `oai-ext-dn` container using `ip route` command.

``` shell
#on core network host
docker exec -it oai-ext-dn bash
ping <ue-ip-address>
```

## 7. Notes ##

- The `oai-ext-dn` container is optional and is only required if the user wants to ping from the UE. In general this container is not required except for testing purposes.
- This tutorial can be taken as reference to test the OAI 5G core with a COTS UE. The configuration file has to be changed according to the gNB, and COTS UE information should be present in the mysql database.
- Generally, in a COTS UE, two PDN sessions are created by default so configure the IMS in SMF properly.
- In case you want to deploy debuggers/developers core network environment with more logs, please follow [this tutorial](./DEBUG_5G_CORE.md)

## 8. Report an Issue ##

To report an issue regarding any-component of CN5G,

1. Share the testing scenario, what the test is trying to achieve.
2. Share logs of the 5GCN components and packet capture/tcpdump of the 5GCN components. Depending on where the packets are captured take care of interface on which the packets are captured. Also it will be nice to capture packets using a filter `ngap || http || pfcp || gtp`. So that the size of `.pcap` file is not huge.
3. You can send an email at openair5g-cn@lists.eurecom.fr with the configuration files, log files in debug mode and pcaps with appropriate filters. Choose an appropriate subject.
4. You can also report an issue or create a bug directly on gitlab. You don't need to sign `Contributor License Agreement` to open issues, it is only needed when you want to contribute and push your changes. You have to send us an email to whitelist your domain/email-address to create a gitlab account, please contact us at contact@openairinterface.org.
5. If you are interested to contribute then please follow [contribution guidelines](../CONTRIBUTING.md).
