# OpenAirInterface Core Serving Gateway Feature Set

[[_TOC_]]

## 1. SGW Fundamentals

*from [Wikipedia.org](https://en.wikipedia.org/wiki/System_Architecture_Evolution)*

The Serving Gateway routes and forwards user data packets, while also acting as the mobility anchor for the user plane during inter-eNodeB handovers and as the anchor for mobility between LTE and other 3GPP technologies (terminating S4 interface and relaying the traffic between 2G/3G systems and PGW).

For idle state UEs, the SGW terminates the downlink data path and triggers paging when downlink data arrives for the UE.

*  It manages and stores UE contexts, e.g. parameters of the IP bearer service, network internal routing information.
*  It also performs replication of the user traffic in case of lawful interception. 

## 2. OAI SGW Available Interfaces

| **ID** | **Interface** | **Status** | **Comments** | **Protocols** |
|--------|---------------|------------|--------------|---------------|
| 1 | S5 / S8 | ✅ | Split in control plane only | GTP-C/U |
|   |         | ❌ | Missing split in User plane | |
| 2 | S1-U    | ✅ | Split in control plane only | GTP-U/UDP |
| 3 | S11     | ✅ | S11-C only actually | GTP-C/UDP |
| 4 | S4      | ❌ | No interconnection with SGSN | GTP-C/UDP |
| 5 | S12     | ❌ | No interconnection with UTRAN | GTP-U/UDP |

## 3. OAI SGW Conformance Functions

Based on document **3GPP TS 23.401 V15.5.0 §4.4.3.2**.

| **ID** | **Classification** | **Status** | **Comments** |
|--------|-------------------|------------|--------------|
| 1 | Local Mobility Anchor point for inter eNodeB handover (except when user data is transported using the Control Plane CIoT EPS optimization) | ❓ | Should be, X2HO have to be tested. |
| 2 | Sending sending of one or more "end marker" to -- the source eNodeB, -- the source SGSN or -- the source RNC immediately after the Serving GW switches the path during inter-eNodeB and inter-RAT handover(s), especially to assist the reordering function in eNodeB | ❌ | Could be requested |
| 3 | Mobility anchoring for inter-3GPP mobility (terminating S4 and relaying the traffic between 2G/3G system and PDN GW) | ❌ | No Support of 2G and 3G systems |
| 4 | ECM-IDLE mode downlink packet buffering and initiation of network triggered service request procedure and optionally Paging Policy Differentiation | ❌ | Buffering is not supported in idle-mode |
| 5 | Lawful Interception | ❌ | |
| 6 | Packet routing and forwarding | ✅ | |
| 7 | Transport level packet marking in the uplink & the downlink e.g. setting the DiffServ Code Point, based on the QCI, and optionally the ARP priority level, of the associated EPS bearer | ❌ | Could be supported |
| 8 | Accounting for inter-operator charging. -- For GTP based S5/S8, the SGW generates accounting data per UE and bearer | ❌ | |
| 9 | Interfacing OFCS according to charging principles and through reference points specified in TS 32.240 | ❌ | |
| 10 | Forwarding of "end marker" to -- the source eNodeB, -- the source SGSN or -- the source RNC when the "end marker" is received from PGW and SGW has downlink user plane established. Upon reception of "end marker", the Serving GW shall not send Downlink Data Notification. | ❌ | |

