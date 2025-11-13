# OpenAirInterface Location Management Function (LMF) Feature Set

[[_TOC_]]

## 1. 5GC Service Based Architecture

![5GC SBA](../../images/5gc_sba.png)

## 2. OAI LMF Available Interfaces

| **ID** | **Interface** | **Status** | **Comment** |
|--------|---------------|------------|--------------|
| 1 | NL1 | ✅ | NL1 interface connects the LMF to the UE (via AMF) |


## 3. OAI LMF Feature List

Based on document **TS 23.273 (section 4.3.8 of TS 23.273)**.

| **ID** | **Classification** | **Status** | **Comments** |
|--------|-------------------|------------|--------------|
| 1 | Support a request for a single location received from a serving AMF for a target UE | ✅ | |
| 2 | Support a request for periodic or triggered location received from a serving AMF for a target UE | ❌ | |
| 3 | Determine type and number of position methods and procedures based on UE and PLMN capabilities, QoS, UE connectivity state per access type, LCS Client type, co-ordinate type and optionally service type | ❌ | |
| 4 | Report UE location estimates directly to a GMLC for periodic or triggered location of a target UE | ❌ | |
| 5 | Support cancelation of periodic or triggered location for a target UE | ❌ | |
| 6 | Support the provision of broadcast assistance data to UEs via NG-RAN in ciphered or unciphered form and forward any ciphering keys to subscribed UEs via the AMF | ❌ | |
| 7 | Support change of a serving LMF for periodic or triggered location reporting for a target UE | ❌ | |

