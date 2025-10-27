# OpenAirInterface Core PDN Gateway Feature Set

[[_TOC_]]

## 1. PGW Fundamentals 

*from [Wikipedia.org](https://en.wikipedia.org/wiki/System_Architecture_Evolution)*

The Packet Data Network Gateway provides connectivity from the UE to external packet data networks by being the point of exit and entry of traffic for the UE.

A UE may have simultaneous connectivity with more than one PGW for accessing multiple PDNs.

The PGW performs:

-  Policy enforcement,
-  Packet filtering for each user,
-  Charging support,
-  Lawful interception and
-  Packet screening.

Another key role of the PGW is to act as the anchor for mobility between 3GPP and non-3GPP technologies such as WiMAX and 3GPP2 (CDMA 1X and EvDO).

## 2. OAI PGW Available Interfaces 

| **ID** | **Interface** | **Status** | **Comments** | **Protocols** |
|--------|---------------|------------|--------------|---------------|
| 1 | S5 / S8 | ✅ | Available on control plane only. | GTP-based |
| 2 | Gx     | ❌ | Policy | |
| 3 | Gy     | ❌ | Charging | |
| 4 | N6     | ✅ | | |

## 3. OAI PGW Conformance Functions 

Based on document **3GPP TS 23.401 V15.5.0 §4.4.3.3**.

| **ID** | **Classification** | **Status** | **Comments** |
|--------|-------------------|------------|--------------|
| 1  | Per-user based packet filtering (ie deep packet inspection) | ✅ | |
| 2  | Lawful Interception | ❌ | |
| 3  | UE IP address allocation | ✅ | Pools of IP addresses |
| 4  | Transport level packet marking in the uplink and downlink | ❌ | |
| 5  | Accounting for inter-operator charging | ❌ | |
| 6  | UL and DL service level charging as defined in TS 23.203 | ❌ | |
| 7  | Interfacing OFCS through | ❌ | |
| 8  | UL and DL service level gating control | ❌ | |
| 9  | UL and DL service level rate enforcement | ❌ | |
| 10 | UL and DL rate enforcement based on APN-AMBR | ❌ | |
| 11 | DL rate enforcement based on the accumulated MBRs of the aggregate of SDFs with the same GBR QCI | ❌ | |
| 12 | DHCPv4 (server and client) and DHCPv6 (client and server) | ❌ | |
| 13 | The network does not support PPP bearer type | ❌ | |
| 14 | The PDN GW may support Non-IP data transfer | ❌ | |
| 15 | Packet screening | ❌ | |
| 16 | Sending of one or more "end marker(s)" to the source SGW immediately after switching the path during SGW change | ❌ | |
| 17 | PCC related features (e.g. involving PCRF and OCS) | ❌ | |
| 18 | UL and DL bearer binding as defined in TS 23.203 | ❌ | |
| 19 | UL bearer binding verification as defined in TS 23.203 | ❌ | |
| 20 | Functionality as defined in RFC 4861 | ❌ | |
| 21 | Accounting per UE and bearer | ❌ | |

