import time
from datetime import datetime
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

# ================= Configuration =================
# OAI-UPF unit is kbps
# 1 Gbps = 1,000,000 kbps

USERS = [
    # === prio 1 (2 users) - High: GBR=10Gbps, MBR=15Gbps ===
    ("12.1.1.2",  15000000, 10000000),
    ("12.1.1.3",  15000000, 10000000),

    # === prio 2 (3 users) - Medium: GBR=5Gbps, MBR=10Gbps ===
    ("12.1.1.4",  10000000, 5000000),
    ("12.1.1.5",  10000000, 5000000),
    ("12.1.1.6",  10000000, 5000000),

    # === prio 3 (5 users) - Low: GBR=2Gbps, MBR=5Gbps ===
    ("12.1.1.7",  5000000, 2000000),
    ("12.1.1.8",  5000000, 2000000),
    ("12.1.1.9",  5000000, 2000000),
    ("12.1.1.10", 5000000, 2000000),
    ("12.1.1.11", 5000000, 2000000),
]

# -----------------------------------------------------------------------------

# [Fix 1] Added QFI parameter
def create_qer(qer_id, qfi, ul_mbr, dl_mbr, ul_gbr, dl_gbr):
    """Create QER with MBR, GBR and QFI tag"""
    return IE_CreateQER(IE_list=[
        IE_QER_Id(id=qer_id),
        IE_GateStatus(ul=0, dl=0),
        IE_QFI(QFI=qfi),  # Dynamically set QFI
        IE_MBR(ul=ul_mbr, dl=dl_mbr),
        IE_GBR(ul=ul_gbr, dl=dl_gbr)
    ])

# [Fix 2] Added precedence parameter
def create_pdr_ul(pdr_id, far_id, qer_id, nwi, source_iface, ip, sd, precedence):
    return IE_CreatePDR(IE_list=[
        IE_PDR_Id(id=pdr_id),
        IE_Precedence(precedence=precedence), # Dynamically set priority (lower value = higher priority)
        IE_PDI(IE_list=[
            IE_SourceInterface(interface=source_iface),
            IE_FTEID(CH=1, CHID=1, choose_id=42, V4=1),
            IE_NetworkInstance(instance=nwi),
            IE_UE_IP_Address(ipv4=ip, V4=1, SD=sd),
        ]),
        IE_OuterHeaderRemoval(header="GTP-U/UDP/IPv4"),
        IE_FAR_Id(id=far_id),
        IE_QER_Id(id=qer_id)
    ])

# [Fix 2] Added precedence parameter
def create_pdr_dl(pdr_id, far_id, qer_id, nwi, source_iface, ip, sd, precedence):
    return IE_CreatePDR(IE_list=[
        IE_PDR_Id(id=pdr_id),
        IE_Precedence(precedence=precedence), # Dynamically set priority
        IE_PDI(IE_list=[
            IE_SourceInterface(interface=source_iface),
            IE_NetworkInstance(instance=nwi),
            IE_UE_IP_Address(ipv4=ip, V4=1, SD=sd)
        ]),
        IE_FAR_Id(id=far_id),
        IE_QER_Id(id=qer_id)
    ])

def create_far_ul(far_id, nwi):
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            IE_DestinationInterface(interface="Core"),
            IE_NetworkInstance(instance=nwi),
        ])
    ])

def create_far_dl(far_id, nwi, fteid, ipv4):
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            IE_DestinationInterface(interface="Access"),
            IE_NetworkInstance(instance=nwi),
            IE_OuterHeaderCreation(GTPUUDPIPV4=1, TEID=fteid, ipv4=ipv4)
        ])
    ])

# [Fix 3] Added precedence and qfi parameters
def session_establishment_ul(seid_, ue_ip, smf_ip, pdr_id_ul, far_id_ul, qer_id, mbr, gbr, precedence, qfi):
    return PFCPSessionEstablishmentRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=smf_ip),
        IE_FSEID(seid=seid_, ipv4=smf_ip, v4=1),
        # Pass QFI
        create_qer(qer_id, qfi=qfi, ul_mbr=mbr, dl_mbr=mbr, ul_gbr=gbr, dl_gbr=gbr),
        # Pass Precedence
        create_pdr_ul(pdr_id_ul, far_id_ul, qer_id, "access.oai.org", "Access", ue_ip, 0, precedence=precedence),
        create_far_ul(far_id_ul, "core.oai.org"),
        IE_PDNType(pdn_type=1),
        IE_APN_DNN(apn_dnn="internet"),
    ])

# [Fix 3] Added precedence parameter
def session_modification_dl(seid_, ue_ip, fteid_dl, smf_ip, gnb_ip, pdr_id_dl, far_id_dl, qer_id, precedence):
    return PFCPSessionModificationRequest(IE_list=[
        IE_FSEID(seid=seid_, ipv4=smf_ip, v4=1),
        create_pdr_dl(pdr_id_dl, far_id_dl, qer_id, "core.oai.org", "Core", ue_ip, 1, precedence=precedence),
        create_far_dl(far_id_dl, "access.oai.org", fteid_dl, gnb_ip),
    ])

def association(smf_ip):
    ts = int((datetime.now() - datetime(1900, 1, 1)).total_seconds())
    return (PFCPAssociationSetupRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=smf_ip),
        IE_RecoveryTimeStamp(timestamp=ts),
        IE_CPFunctionFeatures(OVRL=1, LOAD=1)
    ]))

def send_receive_pfcp(msg, seid_=None, recv=True, seq=None, seq_counter=None, smf_ip=None, upf_ip_n4=None):
    if seq_counter is None: raise ValueError("seq_counter needed")
    seq = seq if seq else seq_counter
    pfcp = PFCP(version=1, seq=seq, S=0 if seid_ is None else 1, seid=0 if seid_ is None else seid_)
    pkt = IP(src=smf_ip, dst=upf_ip_n4, proto=17) / UDP(sport=8805, dport=8805) / pfcp / msg
    if recv:
        res = scapy.sendrecv.sr1(pkt, verbose=0, timeout=2)
        return res
    else:
        scapy.sendrecv.send(pkt, verbose=0)

def generate_unique_seid(base, off): return base + off
def generate_unique_fteid(base, off): return base + off

# [New] Core logic: Calculate priority and QFI based on GBR bandwidth
def get_qos_params_from_gbr(gbr_kbps):
    """
    High (>=10G): Precedence=10 (high), QFI=1
    Med  (>=5G) : Precedence=50 (medium), QFI=5
    Low  (Other): Precedence=100 (low), QFI=9
    """
    if gbr_kbps >= 10000000:   return 10, 1  # High Priority
    elif gbr_kbps >= 5000000:  return 50, 5  # Medium Priority
    else:                      return 100, 9 # Low Priority

def create_pdu_sessions(smf_ip, upf_ip_n4, gnb_ip, first_seq_number):
    print(f"\nSending PFCP Association Request to {upf_ip_n4}...")
    send_receive_pfcp(association(smf_ip), seq_counter=first_seq_number, smf_ip=smf_ip, upf_ip_n4=upf_ip_n4)
    time.sleep(1)

    base_seid = 0x00000001
    base_fteid_dl = 0x00000010

    pdr_id = 0
    far_id = 0
    current_seq = first_seq_number

    for idx, (user_ip, user_mbr, user_gbr) in enumerate(USERS):
        i = idx + 1
        unique_seid = generate_unique_seid(base_seid, idx)
        unique_fteid_dl = generate_unique_fteid(base_fteid_dl, idx)

        pdr_id_ul = pdr_id + 1
        far_id_ul = far_id + 1
        pdr_id_dl = pdr_id + 2
        far_id_dl = far_id + 2
        qer_id = i

        pdr_id += 2
        far_id += 2
        current_seq += 1

        # [Fix 4] Calculate and get QOS parameters
        prio_val, qfi_val = get_qos_params_from_gbr(user_gbr)

        print(f"Creating Session {i}: IP={user_ip}, TEID=0x{unique_fteid_dl:02x} | "
              f"GBR={user_gbr/1000000:.1f}G -> Precedence={prio_val}, QFI={qfi_val}")

        # 1. UL (Establishment) - Pass prio_val and qfi_val
        res = send_receive_pfcp(
            session_establishment_ul(unique_seid, user_ip, smf_ip, pdr_id_ul, far_id_ul, qer_id, 
                                     user_mbr, user_gbr, precedence=prio_val, qfi=qfi_val),
            seid_=0, seq_counter=current_seq, smf_ip=smf_ip, upf_ip_n4=upf_ip_n4
        )

        if res and PFCPSessionEstablishmentResponse in res:
            # 2. DL (Modification) - Pass prio_val
            current_seq += 1
            send_receive_pfcp(
                session_modification_dl(unique_seid, user_ip, unique_fteid_dl, smf_ip, gnb_ip, 
                                        pdr_id_dl, far_id_dl, qer_id, precedence=prio_val),
                seid_=unique_seid, seq_counter=current_seq, smf_ip=smf_ip, upf_ip_n4=upf_ip_n4
            )
        else:
            print(f"Error: Session {i} setup failed.")

        time.sleep(0.05)

def main():
    smf_ip      = "10.112.125.185"
    upf_ip_n4   = "10.112.68.24"
    gnb_ip      = "192.168.10.100"
    first_seq_number = 16770408

    create_pdu_sessions(smf_ip, upf_ip_n4, gnb_ip, first_seq_number)

if __name__ == "__main__":
    main()