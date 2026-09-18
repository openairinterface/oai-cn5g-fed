/* SPDX-License-Identifier: MIT */

/* data initialization script for UEs 208950000000031 and 208950000000032 */
USE `oai_db`;

-- ---------------------------------------------------------------------
-- 1. POPULATE QosData
-- ---------------------------------------------------------------------
-- Profiling: non-gbr-qos-5qi-5
INSERT INTO `QosData` (
    `QosId`, `r_5qi`, `r_5qiIsSet`, `MaxbrUl`, `MaxbrUlIsSet`, `MaxbrDl`, `MaxbrDlIsSet`,
    `GbrUl`, `GbrUlIsSet`, `GbrDl`, `GbrDlIsSet`, `Arp_PriorityLevel`, `Arp_PreemptCap_value_value`,
    `Arp_PreemptVuln_value_value`, `ArpIsSet`, `Qnc`, `QncIsSet`, `PriorityLevel`, `PriorityLevelIsSet`,
    `AverWindow`, `AverWindowIsSet`, `MaxDataBurstVol`, `MaxDataBurstVolIsSet`, `ReflectiveQos`,
    `ReflectiveQosIsSet`, `SharingKeyDl`, `SharingKeyDlIsSet`, `SharingKeyUl`, `SharingKeyUlIsSet`,
    `MaxPacketLossRateDl`, `MaxPacketLossRateDlIsSet`, `MaxPacketLossRateUl`, `MaxPacketLossRateUlIsSet`,
    `DefQosFlowIndication`, `DefQosFlowIndicationIsSet`, `ExtMaxDataBurstVol`, `ExtMaxDataBurstVolIsSet`,
    `PacketDelayBudget`, `PacketDelayBudgetIsSet`, `PacketErrorRate`, `PacketErrorRateIsSet`
) VALUES (
             'non-gbr-qos-5qi-5', 5, 1, '', 0, '', 0,
             '', 0, '', 0, 8, 'NOT_PREEMPT',
             'PREEMPTABLE', 1, 0, 0, 10, 1,
             0, 0, 0, 0, 0,
             0, '', 0, '', 0,
             0, 0, 0, 0,
             0, 0, 0, 0,
             0, 0, '', 0
         );

-- Profiling: gbr-qos-5qi-1
INSERT INTO `QosData` (
    `QosId`, `r_5qi`, `r_5qiIsSet`, `MaxbrUl`, `MaxbrUlIsSet`, `MaxbrDl`, `MaxbrDlIsSet`,
    `GbrUl`, `GbrUlIsSet`, `GbrDl`, `GbrDlIsSet`, `Arp_PriorityLevel`, `Arp_PreemptCap_value_value`,
    `Arp_PreemptVuln_value_value`, `ArpIsSet`, `Qnc`, `QncIsSet`, `PriorityLevel`, `PriorityLevelIsSet`,
    `AverWindow`, `AverWindowIsSet`, `MaxDataBurstVol`, `MaxDataBurstVolIsSet`, `ReflectiveQos`,
    `ReflectiveQosIsSet`, `SharingKeyDl`, `SharingKeyDlIsSet`, `SharingKeyUl`, `SharingKeyUlIsSet`,
    `MaxPacketLossRateDl`, `MaxPacketLossRateDlIsSet`, `MaxPacketLossRateUl`, `MaxPacketLossRateUlIsSet`,
    `DefQosFlowIndication`, `DefQosFlowIndicationIsSet`, `ExtMaxDataBurstVol`, `ExtMaxDataBurstVolIsSet`,
    `PacketDelayBudget`, `PacketDelayBudgetIsSet`, `PacketErrorRate`, `PacketErrorRateIsSet`
) VALUES (
             'gbr-qos-5qi-1', 1, 1, '3 Mbps', 1, '3 Mbps', 1,
             '512 Kbps', 1, '512 Kbps', 1, 3, 'MAY_PREEMPT',
             'NOT_PREEMPTABLE', 1, 0, 0, 20, 1,
             0, 0, 0, 0, 0,
             0, '', 0, '', 0,
             0, 0, 0, 0,
             0, 0, 0, 0,
             0, 0, '', 0
         );


-- ---------------------------------------------------------------------
-- 2. POPULATE PccRuleODB & PccRuleODB_RefQosData
-- ---------------------------------------------------------------------
-- Rule: non-gbr-rule-5qi-5
INSERT INTO `PccRuleODB` (
    `FlowInfos`, `FlowInfosIsSet`, `AppId`, `AppIdIsSet`, `AppDescriptor`, `AppDescriptorIsSet`,
    `ContVer`, `ContVerIsSet`, `PccRuleId`, `Precedence`, `PrecedenceIsSet`, `AfSigProtocol`, `AfSigProtocolIsSet`,
    `AppReloc`, `AppRelocIsSet`, `RefQosDataIsSet`, `RefAltQosParamsIsSet`, `RefTcDataIsSet`, `RefChgDataIsSet`,
    `RefChgN3gDataIsSet`, `RefUmDataIsSet`, `RefUmN3gDataIsSet`, `RefCondData`, `RefCondDataIsSet`, `RefQosMonIsSet`,
    `AddrPreserInd`, `AddrPreserIndIsSet`, `TscaiInputDl`, `TscaiInputDlIsSet`, `TscaiInputUl`, `TscaiInputUlIsSet`,
    `DdNotifCtrl`, `DdNotifCtrlIsSet`, `DdNotifCtrl2`, `DdNotifCtrl2IsSet`, `DisUeNotif`, `DisUeNotifIsSet`
) VALUES (
             '[{"flowDescription": "permit out ip from any to assigned", "packetFilterUsage": true}]', 1, '', 0, '', 0,
             0, 0, 'non-gbr-rule-5qi-5', 20, 1, '', 0,
             0, 0, 1, 0, 0, 0,
             0, 0, 0, '', 0, 0,
             0, 0, '', 0, '', 0,
             '', 0, '', 0, 0, 0
         );

INSERT INTO `PccRuleODB_RefQosData` (`object_id`, `index`, `value`)
VALUES ('non-gbr-rule-5qi-5', 0, 'non-gbr-qos-5qi-5');


-- Rule: gbr-rule-5qi-1
INSERT INTO `PccRuleODB` (
    `FlowInfos`, `FlowInfosIsSet`, `AppId`, `AppIdIsSet`, `AppDescriptor`, `AppDescriptorIsSet`,
    `ContVer`, `ContVerIsSet`, `PccRuleId`, `Precedence`, `PrecedenceIsSet`, `AfSigProtocol`, `AfSigProtocolIsSet`,
    `AppReloc`, `AppRelocIsSet`, `RefQosDataIsSet`, `RefAltQosParamsIsSet`, `RefTcDataIsSet`, `RefChgDataIsSet`,
    `RefChgN3gDataIsSet`, `RefUmDataIsSet`, `RefUmN3gDataIsSet`, `RefCondData`, `RefCondDataIsSet`, `RefQosMonIsSet`,
    `AddrPreserInd`, `AddrPreserIndIsSet`, `TscaiInputDl`, `TscaiInputDlIsSet`, `TscaiInputUl`, `TscaiInputUlIsSet`,
    `DdNotifCtrl`, `DdNotifCtrlIsSet`, `DdNotifCtrl2`, `DdNotifCtrl2IsSet`, `DisUeNotif`, `DisUeNotifIsSet`
) VALUES (
             '[{"flowDescription": "permit out ip from any to any", "packetFilterUsage": true}]', 1, '', 0, '', 0,
             0, 0, 'gbr-rule-5qi-1', 10, 1, '', 0,
             0, 0, 1, 0, 0, 0,
             0, 0, 0, '', 0, 0,
             0, 0, '', 0, '', 0,
             '', 0, '', 0, 0, 0
         );

INSERT INTO `PccRuleODB_RefQosData` (`object_id`, `index`, `value`)
VALUES ('gbr-rule-5qi-1', 0, 'gbr-qos-5qi-1');


-- ---------------------------------------------------------------------
-- 3. POPULATE SupiPolicyDecision & SupiPolicyDecision_PccRuleIds
-- ---------------------------------------------------------------------
-- SUPI: imsi-208950000000031
INSERT INTO `SupiPolicyDecision` (`Supi`, `SupiIsSet`, `PccRuleIdsIsSet`)
VALUES ('imsi-208950000000031', 1, 1);

INSERT INTO `SupiPolicyDecision_PccRuleIds` (`object_id`, `index`, `value`) VALUES
                                                                                ('imsi-208950000000031', 0, 'non-gbr-rule-5qi-5'),
                                                                                ('imsi-208950000000031', 1, 'gbr-rule-5qi-1');


-- SUPI: imsi-208950000000032
INSERT INTO `SupiPolicyDecision` (`Supi`, `SupiIsSet`, `PccRuleIdsIsSet`)
VALUES ('imsi-208950000000032', 1, 1);

INSERT INTO `SupiPolicyDecision_PccRuleIds` (`object_id`, `index`, `value`) VALUES
    ('imsi-208950000000032', 0, 'gbr-rule-5qi-1');