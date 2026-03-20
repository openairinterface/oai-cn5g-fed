# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    GNBSimTestLib.py
Library    NGAPTesterLib.py
Library    RfSimLib.py

Variables    vars.py

# This file is intended to define common robot framework keywords that are used in many tests and suites

*** Variables ***


*** Keywords ***

Launch NRF CN with PCF
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf  oai-pcf
    Prepare Scenario    ${list}   nrf-cn-pcf
    @{replace_list} =  Create List  smf  support_features  use_local_pcc_rules
    Replace In Config    ${replace_list}  no
    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Launch NRF CN with PCF HTTP1
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf  oai-pcf
    Prepare Scenario    ${list}   nrf-cn-pcf
    @{replace_list} =  Create List  smf  support_features  use_local_pcc_rules
    Replace In Config    ${replace_list}  no
    @{replace_list} =  Create List  smf  support_features  use_local_subscription_info
    Replace In Config    ${replace_list}  no
    @{replace_list} =  Create List   http_version
    Replace In Config    ${replace_list}  1

    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Launch NRF CN For QoS
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-ext-dn-2  oai-ext-dn-3  oai-upf  oai-pcf
    Prepare Scenario    ${list}   nrf-cn-qos
    @{replace_list} =  Create List  smf  support_features  use_local_pcc_rules
    Replace In Config    ${replace_list}  no
    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Launch NRF CN
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   nrf-cn
    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Launch Non NRF CN
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   nonnrf-cn
    Deactive NF Registration In CN Config
    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Launch EBPF CN
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn-ebpf  oai-upf-ebpf

    Prepare Scenario    ${list}   nrf-cn-ebpf
    @{replace_list} =  Create List  nfs  upf  
    Replace In Config    ${replace_list}  ${ebf_upf_config}
    @{replace_list} =  Create List  upf  support_features  enable_bpf_datapath
    Replace In Config    ${replace_list}  yes
    @{replace_list} =  Create List  upf  remote_n6_gw
    Replace In Config    ${replace_list}  oai-ext-dn-ebpf

    # TODO because of NRF issue #4, we need this dependency
    Add Dependency   oai-upf-ebpf   oai-smf

    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Launch Northbound Test CN
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn   vpp-upf
    Prepare Scenario    ${list}   Northbound

    @{replace_list} =  Create List    http_version
    Replace In Config     ${replace_list}   ${1}

    @{replace_list} =  Create List    smf  upfs  ${0}  host
    Replace In Config    ${replace_list}  vpp-upf.node.5gcn.mnc95.mcc208.3gppnetwork.org

    @{replace_list} =  Create List    amf  supported_encryption_algorithms  ${0}  
    Replace In Config    ${replace_list}  NEA2

    @{replace_list} =  Create List    amf  supported_integrity_algorithms  ${0}  
    Replace In Config    ${replace_list}  NIA2
    
    @{replace_list} =  Create List  smf  upfs  ${0}  config  enable_usage_reporting
    Replace In Config    ${replace_list}  yes

    Start Trace    core_network
    Start CN
    Check Core Network Health Status

    Prepare RAN     ${1}   ${3}
    ${replace_list} =  Create List  rfsimulator
    Replace In gNB Config    ${replace_list}  { serveraddr = "server"; };  add
    ${replace_list} =  Create List  ulsch_max_frame_inactivity
    Replace In gNB Config    ${replace_list}  None  delete
    ${replace_list} =  Create List  amf_ip_address
    Replace In gNB Config    ${replace_list}  ({ipv4 = "192.168.79.132"  replace
    ${replace_list} =  Create List  GNB_IPV4_ADDRESS_FOR_NG_AMF
    Replace In gNB Config    ${replace_list}  "192.168.79.140"  replace
    ${replace_list} =  Create List  GNB_IPV4_ADDRESS_FOR_NGU
    Replace In gNB Config    ${replace_list}  "192.168.80.140"  replace
    ${replace_list} =  Create List  GNB_INTERFACE_NAME_FOR_NGU
    Replace In gNB Config    ${replace_list}  None  delete
    ${replace_list} =  Create List  GNB_INTERFACE_NAME_FOR_NG_AMF
    Replace In gNB Config    ${replace_list}  None  delete
    ${replace_list} =  Create List  tracking_area_code
    Replace In gNB Config    ${replace_list}  0xa000  replace

Suite Teardown Default
    Stop Cn
    Collect All Logs
    Stop Trace   core_network
    Down Cn
    ${docu}=  Create Cn Documentation
    Set Suite Documentation    ${docu}   append=${TRUE}
    ${gnbsim_docu} =   Create Gnbsim Docu
    Set Suite Documentation    ${gnbsim_docu}   append=${TRUE}
    ${ngap_docu} =    Create Ngap Tester Docu
    Set Suite Documentation    ${ngap_docu}   append=${TRUE}

Check Core Network Health Status
    Wait Until Keyword Succeeds  60s  1s    Check CN Health Status

Check RAN Elements Health Status
    Wait Until Keyword Succeeds  60s  1s    Check RAN Health Status


Wait and Verify Iperf3 Result
    [Arguments]    ${container}  ${mbits}=50
    Wait Until Keyword Succeeds    60s  1s   Iperf3 Is Finished    ${container}
    TRY
        Iperf3 Results Should Be    ${container}  ${mbits}
    EXCEPT    AS   ${error_message}
        Log   IPerf3 Results is wrong, ignored for now: ${error_message}   level=ERROR
    END

Wait and Verify Iperf3 Result Strict
    [Arguments]    ${container}  ${mbits}=50
    Wait Until Keyword Succeeds    60s  1s   Iperf3 Is Finished    ${container}
    Iperf3 Results Should Be    ${container}  ${mbits}


Check gnbsim IP
    [Arguments]    ${gnbsim_name}
    Wait Until Keyword Succeeds    30s  1s  Check Gnbsim Ongoing   ${gnbsim_name}
    ${ip} =    Get Gnbsim Ip    ${gnbsim_name}    # to get the output we parse again
    RETURN      ${ip}

Run NGAP Tester Test
    [Arguments]    ${TC_NAME}    ${MT_PROFILE}=default     ${single_interface}=${TRUE}
    Prepare Ngap Tester    ${TC_NAME}   ${MT_PROFILE}   ${single_interface}
    IF  not ${single_interface}
        @{replace_list} =    Create List  configuration  gnbs  gnb1  n3IpAddr
        Replace In Ngap Tester Config    ${replace_list}  192.168.80.171
        @{replace_list} =    Create List  configuration  trafficReflector  ipAddr
        Replace In Ngap Tester Config    ${replace_list}  192.168.81.179
    END

    Start Ngap Tester
    Wait Until Keyword Succeeds   30s   1s    Check Ngap Tester Done
    Check NGAP Tester Result

Test Setup NGAP Tester
    Check Cn Health Status
    # set single interface currently to true to receive better traces, if we have eBPF support, we should fix this
    Start Trace   ${TEST_NAME}   signaling_only=${FALSE}   single_interface=${True}

Test Teardown NGAP Tester
     Stop Ngap Tester
     ${doc} =    Get Ngap Tester Description
     Set Test Documentation    ${doc}
     Collect All Ngap Tester Logs
     Down Ngap Tester
     Stop Trace   ${TEST_NAME}

Deactive NF Registration in CN Config
    @{replace_list} =  Create List  register_nf  general
    Replace In Config    ${replace_list}  no
    @{replace_list} =  Create List  amf  support_features_options  enable_smf_selection
    Replace In Config    ${replace_list}  no

Test Setup With Gnbsim
    ${gnbsim_name} =   Prepare Gnbsim
    Set Test Variable   ${GNBSIM_IN_USE}   ${gnbsim_name}
    Start Trace    ${TEST_NAME}

Test Teardown With Gnbsim
    Stop Gnbsim   ${GNBSIM_IN_USE}
    Collect All Gnbsim Logs
    Down Gnbsim    ${GNBSIM_IN_USE}
    Stop Trace    ${TEST_NAME}
