# OpenAirInterface Network Slice Selection Function (NSSF) Feature Set

## 1. 5GC Service Based Architecture

![5GC SBA](../../images/5gc_sba.png)


## 2. OAI NSSF Available Interfaces

| **ID** | **Interface** | **Status** | **Comment** |
|--------|---------------|------------|-------------|
| 1 | N22 (*) | ✅ | between NSSF and AMF |
| 2 | N31 | ❌ | between NSSFS |

> (*): support both HTTP/1.1 and HTTP/2

## 3. OAI NSSF Feature List

Based on document **3GPP TS 23.501 v16.0.0 (Section 6.2.14)**.

| **ID** | **Classification** | **Status** | **Comments** |
|--------|-------------------|------------|--------------|
| 1 | NSI Selection | ✅ | Case: PDU Session (NON-Roaming) |
| 2 | Determining the Allowed NSSAI | ❌ | |
| 3 | Determining the Configured NSSAI | ❌ | |
| 4 | Determining the AMF Set | ❌ | |


Based on document **3GPP TS 23.531 v16.0.0 (Section 5.1)**.

| **ID** | **Classification**                                                  | **Status**         | **Comments**                                |
| ------ | ------------------------------------------------------------------- | ------------------ | ------------------------------------------- |
| 1      | NSI Selection                                                       | ✅ |  Case:  PDU Session (NON-Roaming)           |
| 2      | NSSAI create/replace/update the S-NSSAI(s) per TA                   | ❌                |                                             |
| 2      | NSSAI subscribe and unsubscribe for S-NSSAI(s) changes per TA       | ❌                |                                             |
