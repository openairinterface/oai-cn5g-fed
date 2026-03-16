#!/usr/bin/env python3
"""
Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The OpenAirInterface Software Alliance licenses this file to You under
the OAI Public License, Version 1.1  (the "License"); you may not use this file
except in compliance with the License.
You may obtain a copy of the License at

      http://www.openairinterface.org/?page_id=698

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
For more information about the OpenAirInterface (OAI) Software Alliance:
      contact@openairinterface.org
------------------------------------------------------------------------------

Usage:
  python3 pfcp_qos_10_with_prio.py --smf_ip 10.112.125.185 --upf_ip_n4 10.112.68.24 --gnb_ip 192.168.10.100 --first_seq_number 16770408
"""

import time
import argparse
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

import scapy.sendrecv
from scapy.layers.inet import IP, UDP
from scapy.contrib.pfcp import PFCP, \
    IE_ApplyAction, IE_CreateFAR, IE_CreatePDR, IE_CreateQER, IE_QER_Id, \
    IE_GateStatus, IE_MBR, IE_GBR, IE_DestinationInterface, IE_FAR_Id, \
    IE_ForwardingParameters, IE_FSEID, IE_NetworkInstance, IE_NodeId, \
    IE_PDI, IE_PDR_Id, IE_PDNType, IE_APN_DNN, IE_Precedence, \
    IE_RecoveryTimeStamp, IE_SourceInterface, IE_UE_IP_Address, IE_FTEID, \
    IE_OuterHeaderCreation, IE_OuterHeaderRemoval, PFCPAssociationSetupRequest, \
    PFCPSessionEstablishmentRequest, PFCPSessionModificationRequest, \
    IE_CPFunctionFeatures, PFCPSessionEstablishmentResponse, IE_CreatedPDR, IE_QFI

# ================= Configuration & Constants =================
# OAI-UPF unit is kbps (1 Gbps = 1,000,000 kbps)
BASE_SEID = 0x00000001
BASE_FTEID_DL = 0x00000010
MAX_PFCP_RETRIES = 3
PFCP_TIMEOUT = 2

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class UserQoS:
    """Dataclass to hold User QoS parameters"""
    ip: str
    mbr: int
    gbr: int

USERS: List[UserQoS] = [
    # === prio 1 (2 users) - High: GBR=10Gbps, MBR=15Gbps ===
    UserQoS("12.1.1.2", 15000000, 10000000),
    UserQoS("12.1.1.3", 15000000, 10000000),

    # === prio 2 (3 users) - Medium: GBR=5Gbps, MBR=10Gbps ===
    UserQoS("12.1.1.4", 10000000, 5000000),
    UserQoS("12.1.1.5", 10000000, 5000000),
    UserQoS("12.1.1.6", 10000000, 5000000),

    # === prio 3 (5 users) - Low: GBR=2Gbps, MBR=5Gbps ===
    UserQoS("12.1.1.7", 5000000, 2000000),
    UserQoS("12.1.1.8", 5000000, 2000000),
    UserQoS("12.1.1.9", 5000000, 2000000),
    UserQoS("12.1.1.10", 5000000, 2000000),
    UserQoS("12.1.1.11", 5000000, 2000000),
]
# -----------------------------------------------------------------------------

def create_qer(qer_id: int, qfi: int, ul_mbr: int, dl_mbr: int, ul_gbr: int, dl_gbr: int):
    """Create QER Information Element with MBR, GBR and QFI tag."""
    return IE_CreateQER(IE_list=[
        IE_QER_Id(id=qer_id),
        IE_GateStatus(ul=0, dl=0),
        IE_QFI(QFI=qfi),
        IE_MBR(ul=ul_mbr, dl=dl_mbr),
        IE_GBR(ul=ul_gbr, dl=dl_gbr)
    ])

def create_pdr(pdr_id: int, far_id: int, qer_id: int, nwi: str, source_iface: str, ip: str, sd: int, precedence: int, direction: str):
    """Create PDR Information Element dynamically based on direction (UL/DL)."""
    pdi_list = [
        IE_SourceInterface(interface=source_iface),
        IE_NetworkInstance(instance=nwi),
        IE_UE_IP_Address(ipv4=ip, V4=1, SD=sd)
    ]
    
    if direction.upper() == "UL":
        pdi_list.insert(1, IE_FTEID(CH=1, CHID=1, choose_id=42, V4=1))
        
    ie_list = [
        IE_PDR_Id(id=pdr_id),
        IE_Precedence(precedence=precedence),
        IE_PDI(IE_list=pdi_list),
        IE_FAR_Id(id=far_id),
        IE_QER_Id(id=qer_id)
    ]
    
    if direction.upper() == "UL":
        ie_list.insert(3, IE_OuterHeaderRemoval(header="GTP-U/UDP/IPv4"))
        
    return IE_CreatePDR(IE_list=ie_list)

def create_far_ul(far_id: int, nwi: str):
    """Create FAR for Uplink forwarding."""
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            IE_DestinationInterface(interface="Core"),
            IE_NetworkInstance(instance=nwi),
        ])
    ])

def create_far_dl(far_id: int, nwi: str, fteid: int, ipv4: str):
    """Create FAR for Downlink forwarding with GTP encapsulation."""
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            IE_DestinationInterface(interface="Access"),
            IE_NetworkInstance(instance=nwi),
            IE_OuterHeaderCreation(GTPUUDPIPV4=1, TEID=fteid, ipv4=ipv4)
        ])
    ])

def session_establishment_ul(seid_: int, ue_ip: str, smf_ip: str, pdr_id_ul: int, far_id_ul: int, qer_id: int, mbr: int, gbr: int, precedence: int, qfi: int):
    """Generate PFCP Session Establishment Request for UL."""
    return PFCPSessionEstablishmentRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=smf_ip),
        IE_FSEID(seid=seid_, ipv4=smf_ip, v4=1),
        create_qer(qer_id, qfi=qfi, ul_mbr=mbr, dl_mbr=mbr, ul_gbr=gbr, dl_gbr=gbr),
        create_pdr(pdr_id_ul, far_id_ul, qer_id, "access.oai.org", "Access", ue_ip, 0, precedence, "UL"),
        create_far_ul(far_id_ul, "core.oai.org"),
        IE_PDNType(pdn_type=1),
        IE_APN_DNN(apn_dnn="internet"),
    ])

def session_modification_dl(seid_: int, ue_ip: str, fteid_dl: int, smf_ip: str, gnb_ip: str, pdr_id_dl: int, far_id_dl: int, qer_id: int, precedence: int):
    """Generate PFCP Session Modification Request for DL."""
    return PFCPSessionModificationRequest(IE_list=[
        IE_FSEID(seid=seid_, ipv4=smf_ip, v4=1),
        create_pdr(pdr_id_dl, far_id_dl, qer_id, "core.oai.org", "Core", ue_ip, 1, precedence, "DL"),
        create_far_dl(far_id_dl, "access.oai.org", fteid_dl, gnb_ip),
    ])

def association(smf_ip: str):
    """Generate PFCP Association Setup Request."""
    ts = int((datetime.now() - datetime(1900, 1, 1)).total_seconds())
    return PFCPAssociationSetupRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=smf_ip),
        IE_RecoveryTimeStamp(timestamp=ts),
        IE_CPFunctionFeatures(OVRL=1, LOAD=1)
    ])

def send_receive_pfcp(msg, seid_=None, recv=True, seq=None, seq_counter=None, smf_ip=None, upf_ip_n4=None):
    """Send PFCP message and optionally wait for response with retry mechanism."""
    if seq_counter is None: 
        raise ValueError("seq_counter needed")
    seq = seq if seq else seq_counter
    pfcp = PFCP(version=1, seq=seq, S=0 if seid_ is None else 1, seid=0 if seid_ is None else seid_)
    pkt = IP(src=smf_ip, dst=upf_ip_n4, proto=17) / UDP(sport=8805, dport=8805) / pfcp / msg
    
    if not recv:
        scapy.sendrecv.send(pkt, verbose=0)
        return None

    # Implement retry logic to handle packet drops gracefully
    for attempt in range(MAX_PFCP_RETRIES):
        res = scapy.sendrecv.sr1(pkt, verbose=0, timeout=PFCP_TIMEOUT)
        if res:
            return res
        logger.warning(f"Timeout waiting for PFCP response. Retry attempt {attempt + 1}/{MAX_PFCP_RETRIES}")
        time.sleep(1)
        
    raise TimeoutError(f"Failed to receive PFCP response after {MAX_PFCP_RETRIES} retries.")

def generate_unique_seid(base: int, off: int): 
    return base + off

def generate_unique_fteid(base: int, off: int): 
    return base + off

def get_qos_params_from_gbr(gbr_kbps: int):
    """Map GBR bandwidth to Priority (Precedence) and QFI values."""
    if gbr_kbps >= 10000000:   return 10, 1  # High Priority
    elif gbr_kbps >= 5000000:  return 50, 5  # Medium Priority
    else:                      return 100, 9 # Low Priority

def create_pdu_sessions(smf_ip: str, upf_ip_n4: str, gnb_ip: str, first_seq_number: int):
    """Main workflow to establish PFCP sessions for multiple users."""
    logger.info(f"Sending PFCP Association Request to {upf_ip_n4}...")
    try:
        send_receive_pfcp(association(smf_ip), seq_counter=first_seq_number, smf_ip=smf_ip, upf_ip_n4=upf_ip_n4)
    except TimeoutError as e:
        logger.error(f"Association failed: {e}")
        return
        
    time.sleep(1)

    pdr_id = 0
    far_id = 0
    current_seq = first_seq_number

    for idx, user in enumerate(USERS):
        i = idx + 1
        unique_seid = generate_unique_seid(BASE_SEID, idx)
        unique_fteid_dl = generate_unique_fteid(BASE_FTEID_DL, idx)

        pdr_id_ul, far_id_ul = pdr_id + 1, far_id + 1
        pdr_id_dl, far_id_dl = pdr_id + 2, far_id + 2
        qer_id = i

        pdr_id += 2
        far_id += 2
        current_seq += 1

        prio_val, qfi_val = get_qos_params_from_gbr(user.gbr)

        logger.info(f"Creating Session {i}: IP={user.ip}, TEID=0x{unique_fteid_dl:02x} | "
                    f"GBR={user.gbr/1000000:.1f}G -> Precedence={prio_val}, QFI={qfi_val}")

        try:
            # 1. UL (Establishment)
            res = send_receive_pfcp(
                session_establishment_ul(unique_seid, user.ip, smf_ip, pdr_id_ul, far_id_ul, qer_id, 
                                         user.mbr, user.gbr, prio_val, qfi_val),
                seid_=0, seq_counter=current_seq, smf_ip=smf_ip, upf_ip_n4=upf_ip_n4
            )

            if res and PFCPSessionEstablishmentResponse in res:
                # 2. DL (Modification)
                current_seq += 1
                send_receive_pfcp(
                    session_modification_dl(unique_seid, user.ip, unique_fteid_dl, smf_ip, gnb_ip, 
                                            pdr_id_dl, far_id_dl, qer_id, prio_val),
                    seid_=unique_seid, seq_counter=current_seq, smf_ip=smf_ip, upf_ip_n4=upf_ip_n4
                )
            else:
                logger.error(f"Session {i} setup failed during UL establishment.")
        except TimeoutError as e:
            logger.error(f"Session {i} failed: {e}")

        time.sleep(0.05)

def main():
    parser = argparse.ArgumentParser(description="Configure PFCP sessions with Priority QERs.")
    parser.add_argument("--smf_ip", default="10.112.125.185", help="IP address of the SMF")
    parser.add_argument("--upf_ip_n4", default="10.112.68.24", help="N4 IP address of the UPF")
    parser.add_argument("--gnb_ip", default="192.168.10.100", help="IP address of the gNB")
    parser.add_argument("--first_seq_number", type=int, default=16770408, help="Initial PFCP Sequence Number")
    
    args = parser.parse_args()
    create_pdu_sessions(args.smf_ip, args.upf_ip_n4, args.gnb_ip, args.first_seq_number)

if __name__ == "__main__":
    main()
    