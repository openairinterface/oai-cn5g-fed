# OpenAirInterface Access and Mobility Management Function (AMF) Feature Set

[[_TOC_]]


## 1. 5GC Service Based Architecture

![5GC SBA](../../images/5gc_sba.png)

## 2. OAI AMF Available Interfaces

| **ID** | **Interface** | **Status** | **Comment** |
|--------|---------------|------------|--------------|
| 1 | N1  | ✅ | Communicate with UE via NAS message |
| 2 | N2  | ✅ | Communicate with gNB via NGAP message |
| 3 | N8  | ✅ | Interface to/from UDM (e.g., retrieve UE subscription data) |
| 4 | N11 | ✅ | Interface to/from SMF (e.g., N1N2MessageTransfer, PDU Session Services) |
| 5 | N14 | ❌ | Interface between AMFs |
| 6 | N15 | ❌ | Interface between AMF and PCF |


## 3. OAI AMF Feature List

Based on document **3GPP TS 23.501 V16.0.0 §6.2.1**.

| **ID** | **Classification**                                                  | **Status** | **Comments** |
|--------|---------------------------------------------------------------------|------------|--------------|
| 1  | Termination of RAN CP interface (N2)                                | ✅ | Communicate with gNB via NGAP message |
| 2  | Termination of NAS (N1)                                             | ✅ | Communicate with UE via NAS message |
| 3  | NAS ciphering and integrity protection                              | ✅ | |
| 4  | Registration management                                             | ✅ | |
| 5  | Connection management                                               | ✅ | |
| 6  | Reachability management                                             | ❌ | |
| 7  | Mobility Management                                                 | ✅ | Support N2 Handover |
| 8  | Lawful intercept (for AMF events and interface to LI System)        | ❌ | |
| 9  | Provide transport for SM messages between UE and SMF                | ✅ | |
| 10 | Transparent proxy for routing SM messages                           | ❌ | |
| 11 | Access Authentication                                               | ✅ | |
| 12 | Access Authorization                                                | ✅ | |
| 13 | Provide transport for SMS messages between UE and SMSF              | ❌ | |
| 14 | Security Anchor Functionality (SEAF)                                | ✅ | |
| 15 | Location Services management for regulatory services                | ❌ | |
| 16 | Provide transport for Location Services messages between UE and LMF as well as between RAN and LMF | ✅ | |
| 17 | EPS Bearer ID allocation for interworking with EPS                  | ❌ | |
| 18 | UE mobility event notification                                      | ✅ | |
| 19 | Support for Control Plane CIoT 5GS Optimisation                     | ❌ | |
| 20 | Provisioning of external parameters                                 | ❌ | |
| 21 | Support non-3GPP access networks                                    | ❌ | |
