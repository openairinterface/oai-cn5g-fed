# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    CNTestLib.py
Library    GNBSimTestLib.py

Resource   common.robot

Suite Teardown    Suite Teardown SMF UPF Tests

Test Teardown  SMF UPF Test Teardown

Variables   vars.py

*** Test Cases ***

SMF Initiated PFCP Association With NRF
    [Tags]    SMF
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   smf-initiated-with-nrf
    Start CN And Verify GNBSIM
    # In current version, UPF does not send FQDN, but only IP address
    # maybe not a very stable test design to grep for log outputs
    #Log Should Contain    oai-smf   NRF UPF with host name 192.168.79.134 was not found in configuration, take default configuration
    Log Should Contain    oai-smf   Received N4 ASSOCIATION SETUP RESPONSE from an UPF

SMF Takes Correct UPF Config With NRF
    [Teardown]    Simple SMF UPF Test Teardown
    [Tags]    SMF
    @{list} =    Create List  oai-smf   oai-upf   oai-nrf
    Prepare Scenario    ${list}  smf-takes-correct-upf-config-nrf
    # Put a UPF config in SMF that is not default
    @{replace_list} =   Create List  smf  upfs
    @{upf_config} =   Evaluate    [{"host": "192.168.79.134", "config": {"enable_usage_reporting": "true"}}]
    Replace In Config   ${replace_list}   ${upf_config}

    Start Trace    ${TEST NAME}
    Start Cn
    Check Core Network Health Status
    
    #Log Should Contain    oai-smf   Found NRF UPF with host name 192.168.79.134 in configuration
    Log Should Contain    oai-smf   Received N4 ASSOCIATION SETUP RESPONSE from an UPF
    Log Should Contain    oai-smf   enable_usage_reporting.................: Yes

SMF Initiated PFCP Association Without NRF
    [Tags]    SMF
    @{list} =    Create List  oai-amf   oai-smf   oai-udm  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   smf-initiated-without-nrf
    Deactive NF Registration In CN Config

    Add Dependency    oai-smf  oai-upf

    Start CN And Verify GNBSIM

    Log Should Contain    oai-smf   Received N4 ASSOCIATION SETUP RESPONSE from an UPF

UPF Initiated PFCP Association Without NRF
    [Tags]    SMF   UPF
    @{list} =    Create List  oai-amf   oai-smf   oai-udm  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   upf-initiated-without-nrf
    Deactive NF Registration In CN Config

    # Put a fake UPF in SMF so that it does not initiate PFCP association
    @{replace_list} =   Create List  smf  upfs
    @{fake_upf} =  Create List
    Replace In Config   ${replace_list}   ${fake_upf}

    # Put SMF in UPF so that it initiates PFCP association
    @{replace_list} =   Create List  upf  smfs
    @{smf_host} =  Evaluate    [ {"host": "oai-smf"}]
    Replace In Config   ${replace_list}   ${smf_host}

    Add Dependency    oai-upf  oai-smf

    Start CN And Verify GNBSIM

    Log Should Contain    oai-smf   Received N4 ASSOCIATION SETUP REQUEST

*** Keywords ***

Start CN and Verify GNBSIM
    Start Trace    ${TEST NAME}
    Start Cn
    Check Core Network Health Status

    ${gnbsim_name} =   Prepare Gnbsim
    Set Test Variable   ${GNBSIM_IN_USE}   ${gnbsim_name}
    Start Gnbsim    ${gnbsim_name}

    Check Gnbsim IP  ${gnbsim_name}

    Ping From Gnbsim    ${gnbsim_name}  ${EXT_DN1_IP}


Simple SMF UPF Test Teardown
    Stop Trace    ${TEST_NAME}
    Stop Cn
    Collect All Logs    ${TEST_NAME}
    Down Cn

SMF UPF Test Teardown
    Stop Gnbsim   ${GNBSIM_IN_USE}
    Collect All Gnbsim Logs
    Down Gnbsim    ${GNBSIM_IN_USE}
    Simple SMF UPF Test Teardown

Suite Teardown SMF UPF Tests
    ${docu}=  Create Cn Documentation
    Set Suite Documentation    ${docu}   append=${TRUE}
    ${gnbsim_docu} =   Create Gnbsim Docu
    Set Suite Documentation    ${gnbsim_docu}   append=${TRUE}
    ${ngap_docu} =    Create Ngap Tester Docu
    Set Suite Documentation    ${ngap_docu}   append=${TRUE}
