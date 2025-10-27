# OpenAirInterface Network Exposure Function (NEF) Feature Set

[[_TOC_]]

## 1. 5GC Service Based Architecture

![5GC SBA](../../images/5gc_sba.png)

## 2. OAI NEF Available Interfaces

| **ID** | **Interface** | **Status** | **Comment**                     |
| ------ | ------------- | ---------- | --------------------------------|
| 1      | SBI           | ✅         | between NEF and other NFs       |


## 3. OAI NEF Feature List

Based on document **3GPP TS 23.501 v16.0.0 (Section 6.2.5)**.

| **ID** | **Classification**                                                        | **Status** | **Comments**                             |
| ------ | ------------------------------------------------------------------------- | ---------- | ---------------------------------------- |
| 1      | Exposure of capabilities and events                                       | ✅         | Partially implemented for the AMF events |
| 2      | Secure provision of information from external application to 3GPP network | ❌         |                                          |
| 3      | Translation of internal-external information                              | ❌         |                                          |
| 4      | Exposure of analytics                                                     | ❌         |                                          |
| 5      | Retrieval of data from external party by NWDAF                            | ✅         | Partially implemented                    |
| 6      | Support of Non-IP Data Delivery                                           | ❌         |                                          |
| 7      | Support of UAS NF functionality                                           | ❌         |                                          |
| 8      | Support of EAS deployment functionality                                   | ❌         |                                          |

