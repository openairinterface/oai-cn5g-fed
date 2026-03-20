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
      <b><font size = "5">OpenAirInterface 5G Core Network when using any docker-compose-based deployment</font></b>
    </td>
  </tr>
</table>


![SA Demo](./images/docker-compose/5gCN-mini.jpg)

**OVERVIEW**

This tutorial will help in understanding how to deploy an OAI Core Network and to connect a real RAN.

**TABLE OF CONTENTS**

1.  [Pre-requisites](#1-pre-requisites)
2.  [Network Considerations](#2-network-considerations)

## 1. Pre-requisites ##

The container images are built using the command `docker build` on a Ubuntu 18.04 host machine. The base image for all the containers is Ubuntu 18.04.

The required software and their respective versions are listed below. To replicate the testbed use these versions or newer ones.


| Software                   | Version                         |
|:-------------------------- |:------------------------------- |
| docker engine              | 19.03.6, build 369ce74a3c       |
| docker-compose             | 1.27.4, build 40524192          |
| Host operating system      | Ubuntu 18.04.4 LTS              |
| Container operating system | Ubuntu 18.04                    |
| tshark                     | 3.4.4 (Git commit c33f6306cbb2) |
| wireshark                  | 3.4.4 (Git commit c33f6306cbb2) |

### 1.1. Wireshark ###

The new version of `wireshark` may not be available in the ubuntu repository.

- So it is better to build it from source.

You may also use the developer PPA:

```bash
sudo add-apt-repository ppa:wireshark-dev/stable
sudo apt update
sudo apt install wireshark

wireshark --version
Wireshark 3.4.7 (Git v3.4.7 packaged as 3.4.7-1~ubuntu18.04.0+wiresharkdevstable1)
```

## 2. Network Considerations ##

### 2.1. on the Core Network side ###

Most of the times the `docker-compose-host` machine is not configured with packet forwarding. It can be done using the command below (if you have already done it in any other section then don't repeat).

**This is the most important step towards end-to-end connectivity.**

```bash
(docker-compose-host)$ sudo sysctl net.ipv4.conf.all.forwarding=1
(docker-compose-host)$ sudo iptables -P FORWARD ACCEPT
```

### 2.2. on the RAN side ###

We need to make the CN-5G containers visible from this host

```bash
(gnb-host)$ sudo ip route add 192.168.70.128/26 via IP_ADDR_NIC0 dev NIC1
```
