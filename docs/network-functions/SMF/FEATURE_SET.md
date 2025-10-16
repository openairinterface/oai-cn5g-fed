# OpenAirInterface Session Management Function (SMF) Feature Set

[[_TOC_]]

## 1. 5GC Service Based Architecture

![5GC SBA](../../images/5gc_sba.png)

## 2. OAI SMF Available Interfaces

| **ID** | **Interface** | **Status** | **Comment** |
|--------|---------------|------------|-------------|
| 1 | N4 | ✅ | between SMF and UPF (PFCP) |
| 2 | N7 | ✅ | between SMF and PCF |
| 3 | N10 | ✅ | between SMF and UDM (Nudm_SubscriberDataManagement) |
| 4 | N11 (*) | ✅ | between SMF and AMF (Nsmf_PDU_Session Services, Namf_N1N2MessageTransfer) |
| 5 | N16/16a | ❌ | between SMFs |


> **All interfaces support both HTTP/1.1 and HTTP/2**

## 3. OAI SMF Feature List

Based on document **3GPP TS 23.501 v16.0.0 (Section 6.2.2)**.

| **ID** | **Classification**                                                  | **Status** | **Comments**                              |
|--------|---------------------------------------------------------------------|------------|-------------------------------------------|
| 1  | Session Management (Session Establishment/Modification/Release)     | ✅ |                                           |
| 2  | UE IP address allocation & management                               | ✅ | IP Address pool is controlled by SMF      |
| 3  | DHCPv4 (server and client) and DHCPv6 (server and client) function  | ❌ |                                           |
| 4  | Respond to ARP requests and/or IPv6 Neighbour Solicitation requests | ❌ |                                           |
| 5  | Selection of UPF function                                           | ✅ | Local configuration/UPF discovery via NRF |
| 6  | Configures traffic steering at UPF                                  | ✅ | Based on traffic rules  from PCF          |
| 7  | Termination of interfaces towards PCFs                              | ✅ | Only supporting traffic rules             |
| 8  | Lawful intercept                                                    | ❌ |                                           |
| 9  | Charging data collection and support of charging interfaces         | ❌ |                                           |
| 10 | Termination of SM parts of NAS messages                             | ✅ |                                           |
| 11 | Downlink Data Notification                                          | ✅ |                                           |
| 12 | Determine SSC mode of a session                                     | ✅ | Only support SSC mode 1                   |
| 13 | Initiator of AN specific SM information, sent via AMF over N2 to AN | ✅ |                                           |
| 14 | Support for Control Plane CIoT 5GS Optimisation                     | ❌ |                                           |
| 15 | Support of header compression                                       | ❌ |                                           |
| 16 | Act as I-SMF in deployments                                         | ❌ |                                           |
| 17 | Provisioning of external parameters                                 | ❌ |                                           |
