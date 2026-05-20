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
  start -f udp_1pkt_src_ip_split.py -m 1gbps -t cache_size=255,src_ip=192.168.20.100,dst_ip=12.1.1.2
"""

import os
import argparse

# Specific imports avoiding star imports based on review feedback
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import Ether
from trex_stl_lib.api import (STLScVmRaw, STLVmFlowVar, STLVmWrFlowVar, 
                              STLVmFixIpv4, STLPktBuilder, STLStream, STLTXCont)


# Module-level ArgumentParser implementation as suggested by the reviewer
def create_stream_parser():
    parser = argparse.ArgumentParser(description='Argparser for TRex Stream Generation', 
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--cache_size', type=int, default=255, help="The cache size.")
    parser.add_argument('--src_ip', type=str, default="192.168.20.100", help="Base Source IP")
    parser.add_argument('--dst_ip', type=str, default="12.1.1.2", help="Destination IP")
    return parser

# Instantiate parser once globally
TUNABLES_PARSER = create_stream_parser()


class STLS1(object):

    def __init__(self):
        self.fsize = 1400

    def create_stream(self, direction, cache_size, src_ip, dst_ip):
        """Create a single UDP stream with source IP varying."""
        # HW will add 4 bytes ethernet FCS
        size = self.fsize - 4 

        base_pkt = Ether() / IP(src=src_ip, dst=dst_ip) / UDP(dport=2152, sport=2152)
        pad_len = max(0, size - len(base_pkt))
        pad = pad_len * 'x'
                             
        # Generate IP range increment logic dynamically based on src_ip input
        ip_parts = src_ip.split('.')
        # Increment the last octet by 100 for the max range
        ip_parts[-1] = str(min(254, int(ip_parts[-1]) + 100))
        max_ip = ".".join(ip_parts)

        vm = STLScVmRaw([
            STLVmFlowVar("ip_src", min_value=src_ip, max_value=max_ip, size=4, step=1, op="inc"),
            STLVmWrFlowVar(fv_name="ip_src", pkt_offset="IP.src"), # write ip to packet IP.src
            STLVmFixIpv4(offset="IP")                              # fix checksum
        ], cache_size=cache_size)

        pkt = STLPktBuilder(pkt=base_pkt/pad, vm=vm)
        stream = STLStream(packet=pkt, mode=STLTXCont())
        
        return stream

    def get_streams(self, direction=0, tunables=None, **kwargs):
        """Standard TRex callback to fetch streams."""
        tunables = tunables if tunables is not None else []
        # Parse arguments using the globally defined parser
        args, _ = TUNABLES_PARSER.parse_known_args(tunables)
        
        # Create 1 stream using parsed parameters
        return [self.create_stream(direction, args.cache_size, args.src_ip, args.dst_ip)]


def register():
    """TRex entry point."""
    return STLS1()
