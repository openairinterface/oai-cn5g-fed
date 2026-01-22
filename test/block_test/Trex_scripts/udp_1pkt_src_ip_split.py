from trex_stl_lib.api import *
import argparse


# split the range of IP to cores 
#
class STLS1(object):

    def __init__ (self):
        self.fsize  =1400;

    def create_stream (self, direction, cache_size):
        # Create base packet and pad it to size
        size = self.fsize - 4; # HW will add 4 bytes ethernet FCS
        src_ip = '192.168.20.100'
        dst_ip = '12.1.1.2'
        #if direction:
        #    src_ip, dst_ip = dst_ip, src_ip

        base_pkt = Ether()/IP(src=src_ip,dst=dst_ip)/UDP(dport=2152,sport=2152)

        pad = max(0, size - len(base_pkt)) * 'x'
                             
        vm = STLScVmRaw( [   STLVmFlowVar ( "ip_src",  min_value="192.168.20.100",
                                            max_value="192.168.20.200", size=4, step=1,op="inc"),
                             STLVmWrFlowVar (fv_name="ip_src", pkt_offset= "IP.src" ), # write ip to packet IP.src
                             STLVmFixIpv4(offset = "IP")                                # fix checksum
                                  ]
                              ,cache_size = cache_size # the cache size
                              );

        pkt = STLPktBuilder(pkt = base_pkt/pad,
                            vm = vm)
        stream = STLStream(packet = pkt,
                         mode = STLTXCont())
        #print(stream.to_code())
        return stream


    def get_streams (self, direction, tunables, **kwargs):
        parser = argparse.ArgumentParser(description='Argparser for {}'.format(os.path.basename(__file__)), 
                                         formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--cache_size',
                            type=int,
                            default=255,
                            help="The cache size."
                                 "The cache size is limited to the pool size.")
        args = parser.parse_args(tunables)
        # create 1 stream 
        return [ self.create_stream(direction, args.cache_size) ]


# dynamic load - used for trex console or simulator
def register():
    return STLS1()