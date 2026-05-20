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
  python3 pfcp_request_1_pdu_session.py --smf_node_id 192.168.199.95 --smf_n4_ip 192.168.100.1 --upf_n4_ip 192.168.100.2 --ue_ip 192.168.10.100 --gnb_ip 192.168.10.100
"""

import time
import argparse
import logging
from datetime import datetime
from threading import Thread, Event

import scapy.sendrecv
from scapy.all import sniff
from scapy.contrib.gtp import GTP_U_Header, GTPPDUSessionContainer
from scapy.layers.inet import IP, UDP
from scapy.contrib.pfcp import (IE_ApplyAction, IE_CreateFAR, IE_CreatePDR, IE_DestinationInterface,
                                IE_FAR_Id, IE_ForwardingParameters, IE_FSEID, IE_NetworkInstance, 
                                IE_NodeId, IE_PDI, IE_PDR_Id, IE_Precedence, IE_RecoveryTimeStamp, 
                                IE_SourceInterface, IE_UE_IP_Address, IE_FTEID, IE_OuterHeaderCreation, 
                                IE_OuterHeaderRemoval, PFCP, PFCPAssociationSetupRequest, 
                                PFCPSessionEstablishmentRequest, PFCPSessionModificationRequest, 
                                IE_CPFunctionFeatures, PFCPSessionEstablishmentResponse, IE_CreatedPDR, 
                                IE_QFI, PFCPHeartbeatResponse, IE_SequenceNumber, PFCPHeartbeatRequest)

# ================= Configuration & Constants =================
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_SEQ = 16770408
FTEID_UL = 0x00000001
FTEID_DL = 0x00000002
MAX_PFCP_RETRIES = 3
PFCP_TIMEOUT = 2
SEQ_COUNTER = DEFAULT_SEQ

# -----------------------------------------------------------------------------

def seid():
    """Return static SEID for single session."""
    return 1

def ie_fteid_set(fteid, ipv4):
    return IE_FTEID(V4=1, TEID=fteid, ipv4=ipv4)

def ie_fteid():
    return IE_FTEID(CH=1, V4=1)

def ie_fteid_ch(chid):
    """Return FTEID element configured for ID choice."""
    return IE_FTEID(CH=1, CHID=1, choose_id=chid, V4=1)

def outer_header_creation(fteid, ipv4):
    """Create OuterHeaderCreation Element."""
    return IE_OuterHeaderCreation(GTPUUDPIPV4=1, TEID=fteid, ipv4=ipv4)

def create_pdr(pdr_id: int, far_id: int, nwi: str, sdf_filter: str, source_iface: str, ip: str, sd: int, direction: str):
    """Combine PDR creation for both UL and DL directions dynamically."""
    pdi_list = [
        IE_SourceInterface(interface=source_iface),
        IE_NetworkInstance(instance=nwi),
        IE_UE_IP_Address(ipv4=ip, V4=1, SD=sd)
    ]
    
    if direction.upper() == "UL":
        pdi_list.insert(1, ie_fteid_ch(42))
        pdi_list.append(IE_QFI(QFI=8))

    ie_list = [
        IE_PDR_Id(id=pdr_id),
        IE_Precedence(precedence=0),
        IE_PDI(IE_list=pdi_list),
        IE_FAR_Id(id=far_id)
    ]

    if direction.upper() == "UL":
        ie_list.insert(3, IE_OuterHeaderRemoval(header="GTP-U/UDP/IPv4"))
        
    return IE_CreatePDR(IE_list=ie_list)

def create_far_ul(far_id: int, nwi: str):
    """Create UL FAR."""
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            IE_DestinationInterface(interface="Core"),
            IE_NetworkInstance(instance=nwi),
        ])
    ])

def create_far_dl(far_id: int, nwi: str, fteid: int, ipv4: str):
    """Create DL FAR with Outer Header Creation."""
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            IE_DestinationInterface(interface="Access"),
            IE_NetworkInstance(instance=nwi),
            outer_header_creation(fteid, ipv4)
        ])
    ])

def session_establishment_ul(seid_: int, smf_node_id: str, smf_n4_ip: str, ue_ip: str):
    """Generate PFCP Session Establishment Request (UL)."""
    return PFCPSessionEstablishmentRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=smf_node_id),
        IE_FSEID(seid=seid_, ipv4=smf_n4_ip, v4=1),
        create_pdr(1, 1, "access.oai.org", "permit out ip from any to assigned", "Access", ue_ip, 0, "UL"),
        create_far_ul(1, "core.oai.org")
    ])

def session_modification_dl(seid_: int, smf_n4_ip: str, ue_ip: str, gnb_ip: str):
    """Generate PFCP Session Modification Request (DL)."""
    return PFCPSessionModificationRequest(IE_list=[
        IE_FSEID(seid=seid_, ipv4=smf_n4_ip, v4=1),
        create_pdr(2, 2, "core.oai.org", "permit out ip from any to assigned", "Core", ue_ip, 1, "DL"),
        create_far_dl(2, "access.oai.org", FTEID_DL, gnb_ip),
    ])

def association(smf_node_id: str):
    """Generate Setup Association Request."""
    ts = int((datetime.now() - datetime(1900, 1, 1)).total_seconds())
    return PFCPAssociationSetupRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=smf_node_id),
        IE_RecoveryTimeStamp(timestamp=ts),
        IE_CPFunctionFeatures(OVRL=1, LOAD=1)
    ])

def send_receive_pfcp(msg, smf_n4_ip: str, upf_n4_ip: str, seid_=None, recv=True, seq=None):
    """Send PFCP message to UPF and handle retries gracefully."""
    global SEQ_COUNTER
    current_seq = seq if seq else SEQ_COUNTER
    if not seq:
        SEQ_COUNTER += 1

    pfcp = PFCP(version=1, seq=current_seq,
                S=0 if seid_ is None else 1,
                seid=0 if seid_ is None else seid_)

    pkt = IP(src=smf_n4_ip, dst=upf_n4_ip, proto=17) / UDP(sport=8805, dport=8805) / pfcp / msg
    
    if not recv:
        scapy.sendrecv.send(pkt, verbose=0)
        return None

    for attempt in range(MAX_PFCP_RETRIES):
        res = scapy.sendrecv.sr1(pkt, verbose=0, timeout=PFCP_TIMEOUT)
        if res:
            logger.debug(f"Received PFCP response: {res.summary()}")
            return res
        logger.warning(f"Timeout waiting for PFCP response. Retry {attempt + 1}/{MAX_PFCP_RETRIES}")
        time.sleep(1)

    raise TimeoutError("Failed to receive PFCP response after maximum retries.")


class Sniffer(Thread):
    def __init__(self, if_name, filter_str, smf_n4_ip, upf_n4_ip, heartbeat=True):
        super().__init__()
        self.if_name = if_name
        self.filter = filter_str
        self.smf_n4_ip = smf_n4_ip
        self.upf_n4_ip = upf_n4_ip
        self.heartbeat = heartbeat
        self.stop_evt = Event()

    def run(self):
        sniff(iface=self.if_name, filter=self.filter, prn=self.callback, store=0, stop_filter=self.should_stop)

    def join(self, timeout=None):
        self.stop_evt.set()
        super().join(timeout)

    def callback(self, pkt):
        logger.debug(f"Received packet: {pkt}")
        try:
            if PFCPHeartbeatRequest in pkt:
                callback_resp = pkt[PFCPHeartbeatRequest]
                seq_number = callback_resp[IE_SequenceNumber].number
                send_receive_pfcp(PFCPHeartbeatResponse(), self.smf_n4_ip, self.upf_n4_ip, recv=False, seq=seq_number)
        except IndexError:
            pass

    def should_stop(self, packet):
        return self.stop_evt.is_set()

def main():
    parser = argparse.ArgumentParser(description="Test 1 PFCP PDU Session Setup")
    parser.add_argument("--smf_node_id", default="192.168.199.95", help="Node ID of the SMF (FQDN or IP)")
    parser.add_argument("--smf_n4_ip", default="192.168.100.1", help="N4 Interface IP of the SMF")
    parser.add_argument("--upf_n4_ip", default="192.168.100.2", help="N4 Interface IP of the UPF")
    parser.add_argument("--ue_ip", default="192.168.10.100", help="IP address of the UE")
    parser.add_argument("--gnb_ip", default="192.168.10.100", help="IP address of the gNB")
    args = parser.parse_args()

    # heartbeat_sniffer = Sniffer(if_name="demo-oai", filter=f"dst host {args.upf_n4_ip} and udp port 8805", 
    #                             smf_n4_ip=args.smf_n4_ip, upf_n4_ip=args.upf_n4_ip)
    # icmp_sniffer = Sniffer(if_name="cn5g-access", filter="dst host 192.168.72.1 and icmp",
    #                        smf_n4_ip=args.smf_n4_ip, upf_n4_ip=args.upf_n4_ip)
    
    # logger.info("Starting heartbeat and ICMP sniffer in background")
    # heartbeat_sniffer.start()
    # icmp_sniffer.start()

    logger.info("Sending PFCP association setup...")
    try:
        send_receive_pfcp(association(args.smf_node_id), args.smf_n4_ip, args.upf_n4_ip)
    except TimeoutError as e:
        logger.error(f"Association failed: {e}")
        return

    s = seid()
    logger.info("Now sleeping for 1 second while we answer heartbeats...")
    time.sleep(1)

    logger.info("Sending PFCP session establishment...")
    try:
        res = send_receive_pfcp(session_establishment_ul(s, args.smf_node_id, args.smf_n4_ip, args.ue_ip), 
                                args.smf_n4_ip, args.upf_n4_ip, seid_=0)
        session_resp = res[PFCPSessionEstablishmentResponse]
        created_fteid = session_resp[IE_CreatedPDR][IE_FTEID].TEID
        logger.info(f"Created FTEID: {hex(created_fteid)}")
    except (TimeoutError, TypeError, KeyError) as e:
        logger.error(f"Session establishment failed: {e}")
        return

    time.sleep(1)

    logger.info("Sending PFCP session modification...")
    try:
        send_receive_pfcp(session_modification_dl(s, args.smf_n4_ip, args.ue_ip, args.gnb_ip), 
                          args.smf_n4_ip, args.upf_n4_ip, seid_=s)
    except TimeoutError as e:
        logger.error(f"Session modification failed: {e}")
        return

    time.sleep(1)
    
    # icmp_request_ul(created_fteid, "192.168.73.135")
    # icmp_request_ul(created_fteid, "8.8.8.8")
    # time.sleep(1)

    logger.info("PFCP session configuration finished successfully.")

if __name__ == "__main__":
    main()
    