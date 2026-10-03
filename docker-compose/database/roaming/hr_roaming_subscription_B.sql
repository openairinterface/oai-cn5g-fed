-- SPDX-License-Identifier: MIT
-- Home-routed roaming test: the home PLMN (999/10) does not allow local
-- breakout for DNN "oai" when imsi-999100000000031 roams in PLMN 999/20
-- (TS 29.503 DnnInfo.lboRoamingAllowed). The visited AMF then selects a
-- V-SMF locally and the H-SMF through the NRFs and SEPPs.
UPDATE `SmfSelectionSubscriptionData`
SET `subscribedSnssaiInfos`='{"222-00007B":{"dnnInfos":[{"dnn":"oai","defaultDnnIndicator":true,"lboRoamingAllowed":false}]}}'
WHERE `ueid`='999100000000031' AND `servingPlmnid`='99920';
