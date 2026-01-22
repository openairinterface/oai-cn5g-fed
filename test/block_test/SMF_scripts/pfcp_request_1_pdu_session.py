import time
import uuid
from datetime import datetime
from threading import Thread, Event

import scapy.sendrecv
from scapy.contrib.gtp import GTP_U_Header, GTPPDUSessionContainer
from scapy.contrib.pfcp import IE_ApplyAction, IE_CreateFAR, IE_CreatePDR, IE_DestinationInterface, \
    IE_FAR_Id, \
    IE_ForwardingParameters, IE_FSEID, IE_NetworkInstance, IE_NodeId, IE_PDI, IE_PDR_Id, IE_Precedence, \
    IE_RecoveryTimeStamp, IE_SourceInterface, IE_UE_IP_Address, IE_FTEID, IE_OuterHeaderCreation, \
    IE_OuterHeaderRemoval, \
    PFCP, \
    PFCPAssociationSetupRequest, PFCPSessionEstablishmentRequest, \
    PFCPSessionModificationRequest, \
    IE_CPFunctionFeatures, PFCPSessionEstablishmentResponse, IE_CreatedPDR, IE_QFI, PFCPHeartbeatResponse, \
    IE_SequenceNumber, PFCPHeartbeatRequest
from scapy.layers.inet import IP, UDP

from scapy.all import sniff


SMF_IP = "192.168.199.95"
UPF_IP_N3 = "192.168.10.10"
UPF_IP_N4 = "192.168.199.14"
UPF_IP_N6 = "192.168.20.10" 
UE_IP = "192.168.10.100"
#UE_IP = "12.1.1.3"
gNB_IP = "192.168.10.100"
GOOGLE_DNS_IP = "8.8.8.8" 

SEQ = 16770408

FTEID_UL = 0x00000001
FTEID_DL = 0x00000002

# UE_IP_UL = "12.1.1.2"



def seid():
    #return uuid.uuid4().int & (1 << 64) - 1
    return 1


def ie_fteid_set(fteid, ipv4):
    return IE_FTEID(V4=1, TEID=fteid, ipv4=ipv4)


def ie_fteid():
    return IE_FTEID(CH=1, V4=1)


def ie_fteid_ch(chid):
    return IE_FTEID(CH=1, CHID=1, choose_id=chid, V4=1)


def outer_header_creation(fteid, ipv4):
    return IE_OuterHeaderCreation(
        GTPUUDPIPV4=1, TEID=fteid, ipv4=ipv4)


def create_pdr_ul(pdr_id, far_id, nwi, sdf_filter, source_iface, ip, sd):
    return IE_CreatePDR(IE_list=[
        IE_PDR_Id(id=pdr_id),
        IE_Precedence(precedence=0),
        IE_PDI(IE_list=[
            IE_SourceInterface(interface=source_iface),
            ie_fteid_ch(42),
            IE_NetworkInstance(instance=nwi),
            IE_UE_IP_Address(ipv4=ip, V4=1, SD=sd),
            # IE_SDF_Filter(FD=1,
            #              flow_description=sdf_filter),
            IE_QFI(QFI=8)
        ]),
        IE_OuterHeaderRemoval(header="GTP-U/UDP/IPv4"),
        IE_FAR_Id(id=far_id),
    ])


def create_pdr_dl(pdr_id, far_id, nwi, sdf_filter, source_iface, ip, sd):
    return IE_CreatePDR(IE_list=[
        IE_PDR_Id(id=pdr_id),
        IE_Precedence(precedence=0),
        IE_PDI(IE_list=[
            IE_SourceInterface(interface=source_iface),
            IE_NetworkInstance(instance=nwi),
            # IE_SDF_Filter(FD=1, flow_description=sdf_filter),
            IE_UE_IP_Address(ipv4=ip, V4=1, SD=sd)
        ]),
        IE_FAR_Id(id=far_id)
    ])


def create_far_ul(far_id, nwi):
    return IE_CreateFAR(IE_list=[
        IE_FAR_Id(id=far_id),
        IE_ApplyAction(FORW=1),
        IE_ForwardingParameters(IE_list=[
            # IE_DestinationInterface(interface="SGi-LAN/N6-LAN"),
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
            outer_header_creation(fteid, ipv4)
        ])
    ])


def session_establishment_ul(seid_):
    return PFCPSessionEstablishmentRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=SMF_ID),
        IE_FSEID(seid=seid_, ipv4="192.168.100.1", v4=1),
        create_pdr_ul(1, 1, "access.oai.org", "permit out ip from any to assigned", "Access", UE_IP, 0),
        create_far_ul(1, "core.oai.org")
    ])


def session_modification_dl(seid_):
    return PFCPSessionModificationRequest(IE_list=[
        # IE_NodeId(id_type="FQDN", id=SMF_ID),
        IE_FSEID(seid=seid_, ipv4="192.168.100.1", v4=1),
        create_pdr_dl(2, 2, "core.oai.org", "permit out ip from any to assigned", "Core", UE_IP, 1),
        create_far_dl(2, "access.oai.org", FTEID_DL, gNB_IP),
    ])


# def icmp_request_ul(fteid, dst ="8.8.8.8"):
#     res = scapy.sendrecv.sr1(IP(src=f"{gNB_IP}", dst="192.168.101.2", flags=["DF"]) /
#                              UDP(sport=2152, dport=2152) / GTP_U_Header(teid=fteid) / GTPPDUSessionContainer(type=1,
#                                                                                                              QFI=8) /
#                              IP(src=f"{UE_IP}", dst=dst, flags=["DF"]) / ICMP()/(b"1"*48)
#                              )
#     print(res)


def association():
    ts = int((datetime.now() - datetime(1900, 1, 1)).total_seconds())
    return (PFCPAssociationSetupRequest(IE_list=[
        IE_NodeId(id_type="FQDN", id=SMF_IP),
        IE_RecoveryTimeStamp(timestamp=ts),
        IE_CPFunctionFeatures(OVRL=1, LOAD=1)
    ]))


def send_receive_pfcp(msg, seid_=None, recv=True, seq=None):
    global SEQ
    seq = seq if seq else SEQ

    pfcp = PFCP(version=1, seq=seq,
                S=0 if seid_ is None else 1,
                seid=0 if seid_ is None else seid_)

    SEQ += 1
    pkt = IP(src="192.168.100.1", dst="192.168.100.2", proto=17) / UDP(sport=8805, dport=8805) / pfcp / msg
    # sr1 only returns first answered packet
    if recv:
        res = scapy.sendrecv.sr1(pkt)
        print(res)
        return res
    else:
        scapy.sendrecv.send(pkt)


class Sniffer(Thread):
    def __init__(self, if_name, filter, heartbeat=True):
        super().__init__()
        self.if_name = if_name
        self.filter = filter
        self.heartbeat = heartbeat
        self.stop = Event()

    def run(self):
        sniff(iface=self.if_name, filter=self.filter, prn=self.callback, store=0, stop_filter=self.should_stop)

    def join(self, timeout=None):
        self.stop.set()
        super().join(timeout)

    def callback(self, pkt):
        print(f"Received packet: {pkt}")
        try:
            callback_resp = pkt[PFCPHeartbeatRequest]
            seq_number = callback_resp[IE_SequenceNumber].number
            send_receive_pfcp(PFCPHeartbeatResponse, recv=False, seq=seq_number)
        except IndexError: # also traces other responses
            pass


    def should_stop(self, packet):
        return self.stop.is_set()

def main():
    #heartbeat_sniffer = Sniffer(if_name="demo-oai", filter="dst host 192.168.100.2 and udp port 8805")
    #icmp_sniffer = Sniffer(if_name="cn5g-access", filter="dst host 192.168.72.1 and icmp")

    # print("Starting heartbeat and ICMP sniffer in background")
    #heartbeat_sniffer.start()
    #icmp_sniffer.start()

    print("Send PFCP association setup")
    send_receive_pfcp(association())
    s = seid()
    print("Now sleep for 10 seconds while we answer heartbeats")
    time.sleep(1)
    print("Send PFCP session establishment")
    res = send_receive_pfcp(session_establishment_ul(s), seid_=0)
    session_resp = res[PFCPSessionEstablishmentResponse]
    created_fteid = session_resp[IE_CreatedPDR][IE_FTEID].TEID
    print(f"Created FTEID: {hex(created_fteid)}")
    time.sleep(1)

    print("Send PFCP session modification")
    send_receive_pfcp(session_modification_dl(s), seid_=s)

    time.sleep(1)

    # TODO this hangs currently, because scapy does not find the return value. I really would like to verify here
    # if there is a response
    #icmp_request_ul(created_fteid, "192.168.73.135")
    # icmp_request_ul(created_fteid, "8.8.8.8")

    time.sleep(1)

if __name__ == "__main__":
    main()

