# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    CNTestLib.py
Library    OcuDuLib.py
Resource   common.robot

Variables    vars.py

Suite Setup       O-CU/DU Suite Setup
Suite Teardown    O-CU/DU Suite Teardown

*** Test Cases ***
Attach And Ping Through O-CU/DU gNB
    [Documentation]    Attach one OAI NR UE to an O-CU/DU gNB over ZMQ and ping the ext-DN.
    [Tags]    OCUDU    AMF    SMF    UPF    NRF    AUSF    UDM    UDR
    ${ue_ip} =    Wait Until Keyword Succeeds
    ...    90s    2s    Get OcuDu UE IP Address
    Should Match Regexp    ${ue_ip}    ^12\\.1\\.1\\.[0-9]+$
    Ping From OcuDu UE    ${EXT_DN1_IP}

*** Keywords ***
O-CU/DU Suite Setup
    @{containers} =    Create List
    ...    oai-amf    oai-smf    oai-udm    oai-nrf    oai-udr
    ...    oai-ausf    mysql    oai-ext-dn    oai-upf
    Prepare Scenario    ${containers}    nrf-cn-ocudu
    Start Trace    core_network
    Start CN
    Check Core Network Health Status

    Prepare OcuDu RAN
    Start OcuDu gNB
    Wait Until Keyword Succeeds    60s    2s    Check OcuDu gNB Health Status
    Start OcuDu NR UE
    Wait Until Keyword Succeeds    60s    2s    Check OcuDu RAN Health Status

O-CU/DU Suite Teardown
    Stop OcuDu RAN
    Collect All OcuDu Logs
    ${docu} =    Create OcuDu Docu
    Set Suite Documentation    ${docu}    append=${TRUE}
    Down OcuDu RAN
    Suite Teardown Default
