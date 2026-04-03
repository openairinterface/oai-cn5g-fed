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
      <b><font size = "5">OpenAirInterface 5G Core Network Configuration </font></b>
    </td>
  </tr>
</table>

**TABLE OF CONTENTS**

[[_TOC_]]

# 1. Basics

The Provisioning API is a way to provision new PCC Rules, QoS data, TrafficControl data as well as, SUPI, DNN and slice based policy decisions, during the runtime of the PCF.
It replaces the yaml based configuration of the policy rules and is following the same concepts.

You can create QoS Data and Traffic Data. While creating a PCC Rule you can assign QoS Data and TrafficControl Data by the Id.
Policy decisions are assignments from PCC rule ids to a SUPI, a DNN or a slice.

This API supports creating, retrieving, and deleting policy configurations, which are essential for maintaining Quality of Service (QoS) and applying appropriate network policies for different users and services.

At the moment we are only supporting MySQL.

# 2. Activate the Feature

To activate this feature you need to configure the PCF accordingly:

```yaml
database:
  host: mysql
  user: test
  type: mysql
  password: test
  database_name: oai_db
  generate_random: true
  connection_timeout: 300

pcf:
  enable_policy_provisioning_api: yes # Use db instead of yaml, enables dynamic pcc rule creation via API
```

# 3. Location of the OpenAPI Specification File

You can find the API specification here:

```
/docker-compose/policies/policy_decision_api_spec.yaml
```

# 4. API Endpoints

## 4.1 QoS Data

**Create QoS Data**

- **Endpoint:** `POST /npcf-provisioning/v1/qosData`
- **Description:** This endpoint allows the creation of new QoS data that can be linked to a PCC Rule.
- **Example Request:**

```json
{
  "qosId": "non-gbr-qos-5qi-9",
  "5qi": 9,
  "arp": {
    "priorityLevel": 15,
    "preemptCap": "NOT_PREEMPT",
    "preemptVuln": "PREEMPTABLE"
  },
  "priorityLevel": 10
}
```
```http
POST /npcf-provisioning/v1/qosData
Host: oai-pcf:8080
```

**Retrieve QoS Data**

- **Endpoint:** `GET /npcf-provisioning/v1/qosData/{qosId}`
- **Description:** Fetches the QoS data associated with the given `qosId`.
- **Example Request:**

```http
GET /npcf-provisioning/v1/qosData/non-gbr-qos-5qi-9
Host: oai-pcf:8080
```

**Retrieve All QoS Data**

- **Endpoint:** `GET /npcf-provisioning/v1/qosData`
- **Description:** Fetches all QoS data.
- **Example Request:**

```http
GET /npcf-provisioning/v1/qosData
Host: oai-pcf:8080
```

**Update QoS Data**

- **Endpoint:** `PUT /npcf-provisioning/v1/qosData/{qosId}`
- **Description:** Updates the QoS data identified by the `qosId`.
- **Example Request:**

```json
{
  "qosId": "non-gbr-qos-5qi-9",
  "5qi": 9,
  "arp": {
    "priorityLevel": 10,
    "preemptCap": "PREEMPT",
    "preemptVuln": "NOT_PREEMPTABLE"
  },
  "priorityLevel": 2
}
```
```http
PUT /npcf-provisioning/v1/qosData/non-gbr-qos-5qi-9
Host: oai-pcf:8080
```

**Delete QoS Data**

- **Endpoint:** `DELETE /npcf-provisioning/v1/qosData/{qosId}`
- **Description:** Deletes the QoS data identified by the `qosId`.
- **Example Request:**

```http
DELETE /npcf-provisioning/v1/qosData/non-gbr-qos-5qi-9
Host: oai-pcf:8080
```

## 4.2 Traffic Control Data

**Create Traffic Control Data**

- **Endpoint:** `POST /npcf-provisioning/v1/trafficControlData`
- **Description:** Creates traffic control data that can be used in conjunction with QoS data for managing traffic flows.
- **Example Request:**

```json
{
  "tcId": "redirection-scenario",
  "redirectInfo": {
    "redirectEnabled": true,
    "redirectAddressType": "URL",
    "redirectServerAddress": "facebook.com"
  },
  "routeToLocs": [
    {
      "dnai": "access"
    },
    {
      "dnai": "internet"
    }
  ]
}
```
```http
POST /npcf-provisioning/v1/trafficControlData
Host: oai-pcf:8080
```

**Retrieve Traffic Control Data**

- **Endpoint:** `GET /npcf-provisioning/v1/trafficControlData/{scenarioId}`
- **Description:** Retrieves the traffic control data for a given scenario.
- **Example Request:**

```http
GET /npcf-provisioning/v1/trafficControlData/redirection-scenario
Host: oai-pcf:8080
```

**Retrieve All Traffic Control Data**

- **Endpoint:** `GET /npcf-provisioning/v1/trafficControlData`
- **Description:** Fetches all traffic control data scenarios.
- **Example Request:**

```http
GET /npcf-provisioning/v1/trafficControlData
Host: oai-pcf:8080
```

**Update Traffic Control Data**

- **Endpoint:** `PUT /npcf-provisioning/v1/trafficControlData/{scenarioId}`
- **Description:** Updates the traffic control data identified by the `scenarioId`.
- **Example Request:**

```json
{
  "tcId": "redirection-scenario",
  "redirectInfo": {
    "redirectEnabled": false,
    "redirectAddressType": "IPV4",
    "redirectServerAddress": "192.168.0.1"
  },
  "routeToLocs": [
    {
      "dnai": "access"
    }
  ]
}
```
```http
PUT /npcf-provisioning/v1/trafficControlData/redirection-scenario
Host: oai-pcf:8080
```

**Delete Traffic Control Data**

- **Endpoint:** `DELETE /npcf-provisioning/v1/trafficControlData/{scenarioId}`
- **Description:** Deletes the traffic control data identified by the `scenarioId`.
- **Example Request:**

```http
DELETE /npcf-provisioning/v1/trafficControlData/redirection-scenario
Host: oai-pcf:8080
```

## 4.3 PCC Rules

**Create PCC Rule**

- **Endpoint:** `POST /npcf-provisioning/v1/pccRule`
- **Description:** Creates a new PCC rule which can be associated with QoS and Traffic Control data.
- **Example Request:**

```json
{
  "pccRuleId": "non-gbr-rule-5qi-9",
  "flowInfos": [
    {
      "flowDescription": "permit out ip from any to assigned",
      "flowDirection": "BIDIRECTIONAL",
      "packetFilterUsage": true
    }
  ],
  "precedence": 7,
  "refQosData": ["non-gbr-qos-5qi-9"],
  "refTcData": ["redirection-scenario"]
}
```
```http
POST /npcf-provisioning/v1/pccRule
Host: oai-pcf:8080
```

**Retrieve PCC Rule**

- **Endpoint:** `GET /npcf-provisioning/v1/pccRule/{pccRuleId}`
- **Description:** Fetches the PCC rule details associated with the provided `pccRuleId`.
- **Example Request:**

```http
GET /npcf-provisioning/v1/pccRule/gbr-rule-5qi-5
Host: oai-pcf:8080
```
**Retrieve All PCC Rules**

- **Endpoint:** `GET /npcf-provisioning/v1/pccRule`
- **Description:** Fetches all PCC rules.
- **Example Request:**

```http
GET /npcf-provisioning/v1/pccRule
Host: oai-pcf:8080
```

**Update PCC Rule**

- **Endpoint:** `PUT /npcf-provisioning/v1/pccRule/{pccRuleId}`
- **Description:** Updates the PCC rule identified by the `pccRuleId`.
- **Example Request:**

```json
{
  "pccRuleId": "non-gbr-rule-5qi-9",
  "flowInfos": [
    {
      "flowDescription": "permit out 6 from 1.2.3.4 80, 8080-9090 to assigned",
      "flowDirection": "BIDIRECTIONAL",
      "packetFilterUsage": true
    }
  ],
  "precedence": 6,
  "refQosData": ["non-gbr-qos-5qi-9"],
  "refTcData": ["redirection-scenario"]
}
```
```http
PUT /npcf-provisioning/v1/pccRule/non-gbr-rule-5qi-9
Host: oai-pcf:8080
```

**Delete PCC Rule**

- **Endpoint:** `DELETE /npcf-provisioning/v1/pccRule/{pccRuleId}`
- **Description:** Deletes the PCC rule identified by the `pccRuleId`.
- **Example Request:**

```http
DELETE /npcf-provisioning/v1/pccRule/non-gbr-rule-5qi-9
Host: oai-pcf:8080
```

## 4.4 Policy Decisions

**Create SUPI Decision**

- **Endpoint:** `POST /npcf-provisioning/v1/supiPolicyDecision`
- **Description:** Associates a SUPI with specific PCC rules.
- **Example Request:**

```json
{
  "supi": "imsi-208950000000031",
  "pccRuleIds": ["non-gbr-rule-5qi-9"]
}
```
```http
POST /npcf-provisioning/v1/supiPolicyDecision
Host: oai-pcf:8080
```

**Retrieve SUPI Decision**

- **Endpoint:** `GET /npcf-provisioning/v1/supiPolicyDecision/{supi}`
- **Description:** Retrieves the policy decisions made for a specific SUPI.
- **Example Request:**

```http
GET /npcf-provisioning/v1/supiPolicyDecision/imsi-208950000000031
Host: oai-pcf:8080
```

**Retrieve All SUPI Decisions**

- **Endpoint:** `GET /npcf-provisioning/v1/supiPolicyDecisions`
- **Description:** Fetches all SUPI policy decisions.
- **Example Request:**

```http
GET /npcf-provisioning/v1/supiPolicyDecisions
Host: oai-pcf:8080
```

**Update SUPI Decision**

- **Endpoint:** `PUT /npcf-provisioning/v1/supiPolicyDecision/{supi}`
- **Description:** Updates the SUPI decision associated with the specified `supi`.
- **Example Request:**

```json
{
  "supi": "imsi-208950000000031",
  "pccRuleIds": ["gbr-rule-5qi-7"]
}
```
```http
PUT /npcf-provisioning/v1/supiPolicyDecision/imsi-208950000000031
Host: oai-pcf:8080
```

**Delete SUPI Decision**

- **Endpoint:** `DELETE /npcf-provisioning/v1/supiPolicyDecision/{supi}`
- **Description:** Deletes the policy decision associated with the specified `supi`.
- **Example Request:**

```http
DELETE /npcf-provisioning/v1/supiPolicyDecision/imsi-208950000000031
Host: oai-pcf:8080
```

**DNN and Slice Decisions work in the same manner. Check out the OpenAPI specification for more details.**

# 5. Example Provisions

Here are step-by-step examples of how to use the API to provision data:

## 5.1. **Provisioning QoS Data**

  Send a `POST` request to create GBR QoS data.

  **Request body:**

  ```json
  {
    "qosId": "gbr-qos-5qi-3",
    "5qi": 3,
    "maxbrUl": "60 Mbps",
    "maxbrDl": "100 Mbps",
    "gbrUl": "50 Mbps",
    "gbrDl": "50 Mbps",
    "arp": {
      "priorityLevel": 1,
      "preemptCap": "NOT_PREEMPT",
      "preemptVuln": "PREEMPTABLE"
    },
    "priorityLevel": 8
  }
  ```

  **Endpoint:**

  ```
  POST oai-pcf:8080/npcf-provisioning/v1/pccRule
  ```

## 5.2. **Creating a PCC Rule**

 Send a `POST` request to create a PCC rule that references the QoS data created in the previous step.

  **Request body:**

  ```json
  {
    "pccRuleId": "gbr-rule-5qi-3",
    "flowInfos": [
      {
        "flowDescription": "permit out ip from any to assigned",
        "flowDirection": "BIDIRECTIONAL",
        "packetFilterUsage": true
      }
    ],
    "precedence": 7,
    "refQosData": ["gbr-qos-5qi-3"]
  }
  ```

  **Endpoint:**

  ```
  POST oai-pcf:8080/npcf-provisioning/v1/pccRule
  ```

## 5.3. **Setting SUPI Policy Decisions**

  Use the `POST` request to create a policy decision for a specific SUPI that references the PCC rule created in the previous step.

  **Request body:**

  ```json
  {
    "supi": "imsi-208950000000031",
    "pccRuleIds": ["gbr-rule-5qi-3"]
  }
  ```

  **Endpoint:**

  ```
  POST oai-pcf:8080/npcf-provisioning/v1/supiPolicyDecision
  ```

## 5.4. **Create/Update a Default Policy Decision**
**Step 1**: Create a non-gbr PCC rule with the ID `non-gbr-rule-5qi-9`, in the same way as described in steps 1-3.

**Step 2**: Send a `POST` request to create or update the default policy decision.

  **Request body:**

  ```json
  ["non-gbr-rule-5qi-9"]
  ```

  **Endpoint:**

  ```
  POST oai-pcf:8080/npcf-provisioning/v1/defaultDecision
  ```
# 6. Error Handling and Status Codes

The API provides standard HTTP status codes to indicate success or failure. For example:
- `200 OK` for successful GET requests.
- `201 Created` for successful POST requests.
- `400 Bad Request` for invalid inputs.
- `404 Not Found` when a resource cannot be located.
- `409 Bad Request` for conflicts, like resource already exists.
