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

Usage within TRex Console:
  start -f udp_10_pkt_src_ip_split.py -m 100gbps
"""

# Specific imports avoiding star imports based on review feedback
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from trex_stl_lib.api import (STLScVmRaw, STLVmFixIpv4, STLPktBuilder, 
                              STLStream, STLTXCont, STLFlowStats)

# Configuration Constants
# Large offset (2000) is chosen to ensure unique source ports across different packet groups 
# (which have 64 sub-streams each) without overlapping port ranges.
SPORT_OFFSET_MULTIPLIER = 2000

# Mapping structure defining priority and bandwidth percentage for each User/Packet Group
# Target Total MBR = 85Gbps. Input = 100Gbps.
# We ensure EVERY user receives > MBR to saturate the pipe.
USER_QOS_MAP = {
    1:  {"prio": "High", "percent": 16.0}, # MBR=15G, Input=16G
    2:  {"prio": "High", "percent": 16.0},
    3:  {"prio": "Med",  "percent": 11.0}, # MBR=10G, Input=11G
    4:  {"prio": "Med",  "percent": 11.0},
    5:  {"prio": "Med",  "percent": 11.0},
    6:  {"prio": "Low",  "percent": 7.0},  # MBR=5G, Input=7G
    7:  {"prio": "Low",  "percent": 7.0},
    8:  {"prio": "Low",  "percent": 7.0},
    9:  {"prio": "Low",  "percent": 7.0},
    10: {"prio": "Low",  "percent": 7.0},
}

class STLS1(object):

    def __init__(self):
        self.fsize = 1400
        self.dst_mac = "6c:b3:11:29:5a:87" # Make sure this is the real MAC of the NIC
        self.src_ip = '192.168.20.100'
        self.app_dport = 5000
        self.app_sport_min = 1025

    def create_stream(self, stream_name: str, dst_ip: str, packet_id: int, total_rate_percent: float, sub_id: int, total_sub_streams: int):
        """Create a sub-stream with specific QoS distribution rules."""
        # Optimize hash strategy using the defined multiplier
        sport = self.app_sport_min + (packet_id * SPORT_OFFSET_MULTIPLIER) + sub_id

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
        """Generate streams based on mapped QoS profiles."""
        streams = []
        base_ip_prefix = "12.1.1"
        sub_streams_count = 64

        for i in range(1, 11):
            user_ip = f"{base_ip_prefix}.{i + 1}"
            pg_id = i
            
            # Fetch mapped configuration using the data structure
            qos_config = USER_QOS_MAP.get(i, {"prio": "Unknown", "percent": 1.0})
            prio = qos_config["prio"]
            total_percent = qos_config["percent"]

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
    """TRex entry point."""
    return STLS1()
