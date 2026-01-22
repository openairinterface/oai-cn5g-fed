from trex_stl_lib.api import *

class STLS1(object):

    def __init__(self):
        self.fsize = 1400
        self.dst_mac = "6c:b3:11:29:5a:87" # Make sure this is the real MAC of the NIC
        self.src_ip = '192.168.20.100'
        self.app_dport = 5000
        self.app_sport_min = 1025

    def create_stream(self, stream_name, dst_ip, packet_id, total_rate_percent, sub_id, total_sub_streams):
        # Optimize hash strategy
        sport = self.app_sport_min + (packet_id * 2000) + sub_id

        base_pkt = (
            Ether(dst=self.dst_mac) /
            IP(src=self.src_ip, dst=dst_ip) /
            UDP(dport=self.app_dport, sport=sport)
        )

        pad_len = max(0, self.fsize - len(base_pkt) - 4)
        pad = pad_len * 'x'

        vm = STLScVmRaw([
            STLVmFixIpv4(offset="IP"),
        ])

        pkt = STLPktBuilder(pkt=base_pkt / pad, vm=vm)

        return STLStream(
            name=stream_name,
            packet=pkt,
            # Distribute the user's total bandwidth requirement evenly across sub-streams
            mode=STLTXCont(percentage=total_rate_percent / total_sub_streams),
            flow_stats=STLFlowStats(pg_id=packet_id)
        )

    def get_streams(self, direction=0, tunables=None, **kwargs):
        streams = []
        base_ip_prefix = "12.1.1"

        sub_streams_count = 64

        for i in range(1, 11):
            user_ip = f"{base_ip_prefix}.{i + 1}"
            pg_id = i

            # =================================================================
            # [OPTIMIZED DISTRIBUTION]
            # Target Total MBR = 85Gbps. Input = 100Gbps.
            # We need to ensure EVERY user receives > MBR to saturate the pipe.
            #
            # Previous: High=20%(20G), Med=12%(12G), Low=4%(4G < 5G MBR!) -> Bottleneck
            # New:      High=16%(16G), Med=11%(11G), Low=7%(7G > 5G MBR)  -> Saturated
            # Sum:      16*2 + 11*3 + 7*5 = 32 + 33 + 35 = 100%
            # =================================================================
            if i <= 2:
                prio = "High"
                # MBR=15G, Input=16G
                total_percent = 16.0
            elif i <= 5:
                prio = "Med"
                # MBR=10G, Input=11G
                total_percent = 11.0
            else:
                prio = "Low"
                # MBR=5G, Input=7G
                total_percent = 7.0

            for sub in range(sub_streams_count):
                name = f"U{i:02d}_{prio}_sub{sub:02d}"
                streams.append(self.create_stream(
                    stream_name=name,
                    dst_ip=user_ip,
                    packet_id=pg_id,
                    total_rate_percent=total_percent,
                    sub_id=sub,
                    total_sub_streams=sub_streams_count
                ))

        return streams

def register():
    return STLS1()