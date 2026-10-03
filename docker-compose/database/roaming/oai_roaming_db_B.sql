SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

CREATE TABLE `AccessAndMobilitySubscriptionData` (
  `ueid` varchar(15) NOT NULL,
  `servingPlmnid` varchar(15) NOT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `gpsis` json DEFAULT NULL,
  `internalGroupIds` json DEFAULT NULL,
  `sharedVnGroupDataIds` json DEFAULT NULL,
  `subscribedUeAmbr` json DEFAULT NULL,
  `nssai` json DEFAULT NULL,
  `ratRestrictions` json DEFAULT NULL,
  `forbiddenAreas` json DEFAULT NULL,
  `serviceAreaRestriction` json DEFAULT NULL,
  `coreNetworkTypeRestrictions` json DEFAULT NULL,
  `rfspIndex` int(10) DEFAULT NULL,
  `subsRegTimer` int(10) DEFAULT NULL,
  `ueUsageType` int(10) DEFAULT NULL,
  `mpsPriority` tinyint(1) DEFAULT NULL,
  `mcsPriority` tinyint(1) DEFAULT NULL,
  `activeTime` int(10) DEFAULT NULL,
  `sorInfo` json DEFAULT NULL,
  `sorInfoExpectInd` tinyint(1) DEFAULT NULL,
  `sorafRetrieval` tinyint(1) DEFAULT NULL,
  `sorUpdateIndicatorList` json DEFAULT NULL,
  `upuInfo` json DEFAULT NULL,
  `micoAllowed` tinyint(1) DEFAULT NULL,
  `sharedAmDataIds` json DEFAULT NULL,
  `odbPacketServices` json DEFAULT NULL,
  `serviceGapTime` int(10) DEFAULT NULL,
  `mdtUserConsent` json DEFAULT NULL,
  `mdtConfiguration` json DEFAULT NULL,
  `traceData` json DEFAULT NULL,
  `cagData` json DEFAULT NULL,
  `stnSr` varchar(50) DEFAULT NULL,
  `cMsisdn` varchar(50) DEFAULT NULL,
  `nbIoTUePriority` int(10) DEFAULT NULL,
  `nssaiInclusionAllowed` tinyint(1) DEFAULT NULL,
  `rgWirelineCharacteristics` varchar(50) DEFAULT NULL,
  `ecRestrictionDataWb` json DEFAULT NULL,
  `ecRestrictionDataNb` tinyint(1) DEFAULT NULL,
  `expectedUeBehaviourList` json DEFAULT NULL,
  `primaryRatRestrictions` json DEFAULT NULL,
  `secondaryRatRestrictions` json DEFAULT NULL,
  `edrxParametersList` json DEFAULT NULL,
  `ptwParametersList` json DEFAULT NULL,
  `iabOperationAllowed` tinyint(1) DEFAULT NULL,
  `wirelineForbiddenAreas` json DEFAULT NULL,
  `wirelineServiceAreaRestriction` json DEFAULT NULL,
  PRIMARY KEY (`ueid`,`servingPlmnid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `AccessAndMobilitySubscriptionData` (`ueid`, `servingPlmnid`, `nssai`) VALUES
('999100000000031', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000032', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000033', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000034', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000035', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000036', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000037', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000038', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000039', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}'),
('999100000000040', '99910', '{"defaultSingleNssais": [{"sst": 1, "sd": "000001"}, {"sst": 222, "sd": "00007B"}]}');

CREATE TABLE `Amf3GppAccessRegistration` (
  `ueid` varchar(15) NOT NULL,
  `amfInstanceId` varchar(50) NOT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `purgeFlag` tinyint(1) DEFAULT NULL,
  `pei` varchar(50) DEFAULT NULL,
  `imsVoPs` json DEFAULT NULL,
  `deregCallbackUri` varchar(50) NOT NULL,
  `amfServiceNameDereg` json DEFAULT NULL,
  `pcscfRestorationCallbackUri` varchar(50) DEFAULT NULL,
  `amfServiceNamePcscfRest` json DEFAULT NULL,
  `initialRegistrationInd` tinyint(1) DEFAULT NULL,
  `guami` json NOT NULL,
  `backupAmfInfo` json DEFAULT NULL,
  `drFlag` tinyint(1) DEFAULT NULL,
  `ratType` json NOT NULL,
  `urrpIndicator` tinyint(1) DEFAULT NULL,
  `amfEeSubscriptionId` varchar(50) DEFAULT NULL,
  `epsInterworkingInfo` json DEFAULT NULL,
  `ueSrvccCapability` tinyint(1) DEFAULT NULL,
  `registrationTime` varchar(50) DEFAULT NULL,
  `vgmlcAddress` json DEFAULT NULL,
  `contextInfo` json DEFAULT NULL,
  `noEeSubscriptionInd` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`ueid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `AuthenticationStatus` (
  `ueid` varchar(20) NOT NULL,
  `nfInstanceId` varchar(50) NOT NULL,
  `success` tinyint(1) NOT NULL,
  `timeStamp` varchar(50) NOT NULL,
  `authType` varchar(25) NOT NULL,
  `servingNetworkName` varchar(50) NOT NULL,
  `authRemovalInd` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`ueid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `AuthenticationSubscription` (
  `ueid` varchar(20) NOT NULL,
  `authenticationMethod` varchar(25) NOT NULL,
  `encPermanentKey` varchar(50) DEFAULT NULL,
  `protectionParameterId` varchar(50) DEFAULT NULL,
  `sequenceNumber` json DEFAULT NULL,
  `authenticationManagementField` varchar(50) DEFAULT NULL,
  `algorithmId` varchar(50) DEFAULT NULL,
  `encOpcKey` varchar(50) DEFAULT NULL,
  `encTopcKey` varchar(50) DEFAULT NULL,
  `vectorGenerationInHss` tinyint(1) DEFAULT NULL,
  `n5gcAuthMethod` varchar(15) DEFAULT NULL,
  `rgAuthenticationInd` tinyint(1) DEFAULT NULL,
  `supi` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ueid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `AuthenticationSubscription` (`ueid`, `authenticationMethod`, `encPermanentKey`, `protectionParameterId`, `sequenceNumber`, `authenticationManagementField`, `algorithmId`, `encOpcKey`, `encTopcKey`, `vectorGenerationInHss`, `n5gcAuthMethod`, `rgAuthenticationInd`, `supi`) VALUES
('999100000000031', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000031'),
('999100000000032', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000032'),
('999100000000033', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000033'),
('999100000000034', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000034'),
('999100000000035', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000035'),
('999100000000036', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000036'),
('999100000000037', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000037'),
('999100000000038', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000038'),
('999100000000039', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000039'),
('999100000000040', '5G_AKA', '0C0A34601D4F07677303652C0462535B', '0C0A34601D4F07677303652C0462535B', '{"sqn": "000000000020", "sqnScheme": "NON_TIME_BASED", "lastIndexes": {"ausf": 0}}', '8000', 'milenage', '63bfa50ee6523365ff14c1f45f88737d', NULL, NULL, NULL, NULL, '999100000000040');

CREATE TABLE `SdmSubscriptions` (
  `ueid` varchar(15) NOT NULL,
  `subsId` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  `nfInstanceId` varchar(50) NOT NULL,
  `implicitUnsubscribe` tinyint(1) DEFAULT NULL,
  `expires` varchar(50) DEFAULT NULL,
  `callbackReference` varchar(2048) NOT NULL,
  `amfServiceName` json DEFAULT NULL,
  `monitoredResourceUris` json NOT NULL,
  `singleNssai` json DEFAULT NULL,
  `dnn` varchar(50) DEFAULT NULL,
  `subscriptionId` varchar(50) DEFAULT NULL,
  `plmnId` json DEFAULT NULL,
  `immediateReport` tinyint(1) DEFAULT NULL,
  `report` json DEFAULT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `contextInfo` json DEFAULT NULL,
  PRIMARY KEY (`subsId`,`ueid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `SessionManagementSubscriptionData` (
  `ueid` varchar(15) NOT NULL,
  `servingPlmnid` varchar(15) NOT NULL,
  `singleNssai` json NOT NULL,
  `dnnConfigurations` json DEFAULT NULL,
  `internalGroupIds` json DEFAULT NULL,
  `sharedVnGroupDataIds` json DEFAULT NULL,
  `sharedDnnConfigurationsId` varchar(50) DEFAULT NULL,
  `odbPacketServices` json DEFAULT NULL,
  `traceData` json DEFAULT NULL,
  `sharedTraceDataId` varchar(50) DEFAULT NULL,
  `expectedUeBehavioursList` json DEFAULT NULL,
  `suggestedPacketNumDlList` json DEFAULT NULL,
  `3gppChargingCharacteristics` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`ueid`,`servingPlmnid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Insert 10 subscribers with lboRoamingAllowed: true and without staticIpAddress for dynamic VPLMN breakout allocation
INSERT INTO `SessionManagementSubscriptionData` (`ueid`, `servingPlmnid`, `singleNssai`, `dnnConfigurations`) VALUES
('999100000000031', '99910', '{"sst": 222, "sd": "00007B"}', '{"oai":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000032', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000033', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000034', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000035', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000036', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000037', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000038', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000039', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}'),
('999100000000040', '99910', '{"sst": 222, "sd": "00007B"}', '{"default":{"pduSessionTypes":{"defaultSessionType":"IPV4"},"sscModes":{"defaultSscMode":"SSC_MODE_1"},"5gQosProfile":{"5qi":6,"arp":{"priorityLevel":1,"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE"},"priorityLevel":1},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"lboRoamingInformation":{"lboRoamingAllowed":true}}}');

CREATE TABLE `SmfRegistrations` (
  `ueid` varchar(15) NOT NULL,
  `subpduSessionId` int(10) NOT NULL,
  `smfInstanceId` varchar(50) NOT NULL,
  `smfSetId` varchar(50) DEFAULT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `pduSessionId` int(10) NOT NULL,
  `singleNssai` json NOT NULL,
  `dnn` varchar(50) DEFAULT NULL,
  `emergencyServices` tinyint(1) DEFAULT NULL,
  `pcscfRestorationCallbackUri` varchar(50) DEFAULT NULL,
  `plmnId` json NOT NULL,
  `pgwFqdn` varchar(50) DEFAULT NULL,
  `epdgInd` tinyint(1) DEFAULT NULL,
  `deregCallbackUri` varchar(50) DEFAULT NULL,
  `registrationReason` json DEFAULT NULL,
  `registrationTime` varchar(50) DEFAULT NULL,
  `contextInfo` json DEFAULT NULL,
  PRIMARY KEY (`ueid`,`subpduSessionId`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `SmfSelectionSubscriptionData` (
  `ueid` varchar(15) NOT NULL,
  `servingPlmnid` varchar(15) NOT NULL,
  `supportedFeatures` varchar(50) DEFAULT NULL,
  `subscribedSnssaiInfos` json DEFAULT NULL,
  `sharedSnssaiInfosId` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`ueid`,`servingPlmnid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- Roaming subscription for the configured UE; TS 29.503 DnnInfo carries LBO permission.
UPDATE `SessionManagementSubscriptionData` SET `dnnConfigurations`='{"oai":{"sscModes":{"defaultSscMode":"SSC_MODE_1"},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"5gQosProfile":{"5qi":6,"arp":{"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE","priorityLevel":1},"priorityLevel":1},"pduSessionTypes":{"defaultSessionType":"IPV4"}}}' WHERE ueid='999100000000031' AND servingPlmnid='99910';
INSERT INTO `AccessAndMobilitySubscriptionData` (`ueid`,`gpsis`,`nssai`,`stnSr`,`cMsisdn`,`cagData`,`sorInfo`,`upuInfo`,`rfspIndex`,`traceData`,`activeTime`,`mcsPriority`,`micoAllowed`,`mpsPriority`,`ueUsageType`,`subsRegTimer`,`servingPlmnid`,`forbiddenAreas`,`mdtUserConsent`,`serviceGapTime`,`sorafRetrieval`,`nbIoTUePriority`,`ratRestrictions`,`sharedAmDataIds`,`internalGroupIds`,`mdtConfiguration`,`sorInfoExpectInd`,`subscribedUeAmbr`,`odbPacketServices`,`ptwParametersList`,`supportedFeatures`,`edrxParametersList`,`ecRestrictionDataNb`,`ecRestrictionDataWb`,`iabOperationAllowed`,`sharedVnGroupDataIds`,`nssaiInclusionAllowed`,`primaryRatRestrictions`,`serviceAreaRestriction`,`sorUpdateIndicatorList`,`wirelineForbiddenAreas`,`expectedUeBehaviourList`,`secondaryRatRestrictions`,`rgWirelineCharacteristics`,`coreNetworkTypeRestrictions`,`wirelineServiceAreaRestriction`) VALUES ('999100000000031',NULL,'{"defaultSingleNssais":[{"sd":"000001","sst":1},{"sd":"00007B","sst":222}]}',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'99920',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL) ON DUPLICATE KEY UPDATE `nssai`=VALUES(`nssai`);
INSERT INTO `SessionManagementSubscriptionData` (`ueid`,`traceData`,`singleNssai`,`servingPlmnid`,`internalGroupIds`,`dnnConfigurations`,`odbPacketServices`,`sharedTraceDataId`,`sharedVnGroupDataIds`,`expectedUeBehavioursList`,`suggestedPacketNumDlList`,`sharedDnnConfigurationsId`,`3gppChargingCharacteristics`) VALUES ('999100000000031',NULL,'{"sd":"00007B","sst":222}','99920',NULL,'{"oai":{"sscModes":{"defaultSscMode":"SSC_MODE_1"},"sessionAmbr":{"uplink":"100Mbps","downlink":"100Mbps"},"5gQosProfile":{"5qi":6,"arp":{"preemptCap":"NOT_PREEMPT","preemptVuln":"NOT_PREEMPTABLE","priorityLevel":1},"priorityLevel":1},"pduSessionTypes":{"defaultSessionType":"IPV4"}}}',NULL,NULL,NULL,NULL,NULL,NULL,NULL) ON DUPLICATE KEY UPDATE `singleNssai`=VALUES(`singleNssai`),`dnnConfigurations`=VALUES(`dnnConfigurations`);
INSERT INTO `SmfSelectionSubscriptionData` (`ueid`,`servingPlmnid`,`subscribedSnssaiInfos`) VALUES ('999100000000031','99910','{"222-00007B":{"dnnInfos":[{"dnn":"oai","defaultDnnIndicator":true,"lboRoamingAllowed":true}]}}') ON DUPLICATE KEY UPDATE `subscribedSnssaiInfos`=VALUES(`subscribedSnssaiInfos`);
INSERT INTO `SmfSelectionSubscriptionData` (`ueid`,`servingPlmnid`,`subscribedSnssaiInfos`) VALUES ('999100000000031','99920','{"222-00007B":{"dnnInfos":[{"dnn":"oai","defaultDnnIndicator":true,"lboRoamingAllowed":true}]}}') ON DUPLICATE KEY UPDATE `subscribedSnssaiInfos`=VALUES(`subscribedSnssaiInfos`);

COMMIT;
