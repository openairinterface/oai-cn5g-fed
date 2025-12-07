import copy
import json

smf_config_json = """
{
  "TLS": {
    "enable_tls": false
  },
  "http_request_timeout": 3000,
  "http_version": "1",
  "local_subscription_infos": [
    {
      "dnn": "oai",
      "qos_profile": {
        "5qi": 9,
        "arp_preempt_capability": "NOT_PREEMPT",
        "arp_preempt_vulnerability": "NOT_PREEMPTABLE",
        "arp_priority": 1,
        "priority": 0,
        "session_ambr_dl": "400Mbps",
        "session_ambr_ul": "200Mbps"
      },
      "snssai": {
        "sd": "ffffff",
        "sst": 1
      },
      "ssc_mode": 1
    },
    {
      "dnn": "oai.ipv4",
      "qos_profile": {
        "5qi": 9,
        "arp_preempt_capability": "NOT_PREEMPT",
        "arp_preempt_vulnerability": "NOT_PREEMPTABLE",
        "arp_priority": 1,
        "priority": 0,
        "session_ambr_dl": "200Mbps",
        "session_ambr_ul": "100Mbps"
      },
      "snssai": {
        "sd": "000001",
        "sst": 1
      },
      "ssc_mode": 1
    },
    {
      "dnn": "default",
      "qos_profile": {
        "5qi": 9,
        "arp_preempt_capability": "NOT_PREEMPT",
        "arp_preempt_vulnerability": "NOT_PREEMPTABLE",
        "arp_priority": 1,
        "priority": 0,
        "session_ambr_dl": "100Mbps",
        "session_ambr_ul": "50Mbps"
      },
      "snssai": {
        "sd": "00007b",
        "sst": 222
      },
      "ssc_mode": 1
    },
    {
      "dnn": "default",
      "qos_profile": {
        "5qi": 9,
        "arp_preempt_capability": "NOT_PREEMPT",
        "arp_preempt_vulnerability": "NOT_PREEMPTABLE",
        "arp_priority": 1,
        "priority": 0,
        "session_ambr_dl": "100Mbps",
        "session_ambr_ul": "50Mbps"
      },
      "snssai": {
        "sd": "ffffff",
        "sst": 1
      },
      "ssc_mode": 1
    }
  ],
  "log_level": "debug",
  "register_nf": true,
  "sbi": {
    "api_version": "v1",
    "interface_name": "eth0",
    "url": "oai-smf:8080"
  },
  "smf_info": {
    "sNssaiSmfInfoList": [
      {
        "dnnSmfInfoList": [
          {
            "dnn": "oai"
          },
          {
            "dnn": "default"
          }
        ],
        "sNssai": {
          "sd": "ffffff",
          "sst": 1
        }
      },
      {
        "dnnSmfInfoList": [
          {
            "dnn": "oai.ipv4"
          }
        ],
        "sNssai": {
          "sd": "000001",
          "sst": 1
        }
      },
      {
        "dnnSmfInfoList": [
          {
            "dnn": "default"
          }
        ],
        "sNssai": {
          "sd": "00007b",
          "sst": 222
        }
      }
    ]
  },
  "supported_features": {
    "use_external_nssf": false,
    "use_local_pcc_rules": true,
    "use_local_subscription_info": true
  },
  "ue_dns": {
    "primary_dns_ipv4": "172.21.3.100",
    "primary_dns_ipv6": "2001:4860:4860::8888",
    "secondary_dns_ipv4": "8.8.8.8",
    "secondary_dns_ipv6": "2001:4860:4860::8888"
  },
  "upfs": [
    {
      "config": {
        "enable_dl_pdr_in_session_establishment": false,
        "enable_qers": false,
        "enable_usage_reporting": false,
        "local_n3_ipv4": ""
      },
      "host": "oai-upf",
      "port": 8805,
      "upf_info": {
        "interfaceUpfInfoList": [
          {
            "interfaceType": "N3",
            "networkInstance": "access.oai.org"
          },
          {
            "interfaceType": "N6",
            "networkInstance": "core.oai.org"
          }
        ],
        "sNssaiUpfInfoList": []
      }
    }
  ]
}
"""

smf_config_dict = json.loads(smf_config_json)

# used for the tests to see if update is working
smf_config_dict_updated = copy.deepcopy(smf_config_dict)
smf_config_dict_updated["http_version"] = 2
smf_config_dict_updated["smf_info"]["sNssaiSmfInfoList"] = [{"dnnSmfInfoList": [{"dnn": "oai"}]}]
