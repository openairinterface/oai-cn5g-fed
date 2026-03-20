# SPDX-License-Identifier: LicenseRef-CSSL-1.0

# Variables that are relevant for robot framework

EXT_DN1_IP = "192.168.79.141"
EXT_DN2_IP = "192.168.79.142"
EXT_DN3_IP = "192.168.79.143"
EXT_DN_EBPF_IP = "192.168.81.144"
EXT_DN1_IP_N3 = "192.168.81.141"

EXT_DN1_NAME = "oai-ext-dn"
EXT_DN2_NAME = "oai-ext-dn-2"
EXT_DN3_NAME = "oai-ext-dn-3"
EXT_DN_EBPF_NAME = "oai-ext-dn-ebpf"

ebf_upf_config = {
    "host": "oai-upf-ebpf",
    "sbi": {
        "port": 8080,
        "api_version": "v1",
        "interface_name": "demo-oai-test"
    },
    "n4": {
        "interface_name": "demo-oai-test"
    },
    "n3": {
        "interface_name": "demo-n3-test"
    },
    "n6": {
        "interface_name": "demo-n6-test"
    }
}
