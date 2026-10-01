# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    OperatingSystem
Library    Process
Library    String
Library    Collections
Library    CNTestLib.py
Library    RfSimLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    LMF Suite Setup
Suite Teardown    LMF Suite Teardown

*** Variables ***
${LMF_URL}           http://${LMF_IP}:8080/nlmf-loc/v1/determine-location
${LMF_INPUT_DATA}    ${CURDIR}/template/lmf_input_data.json
# 51 PRB: carrier centre 3609.12 MHz, SSB 234 subcarriers above point A (see template/gnb-positioning.conf)
${UE_OPTIONS}        -E --rfsim -r 51 --numerology 1 --band 78 -C 3609120000 --ssb 234 --uicc0.imsi REPLACE_IMSI --rfsimulator.[0].serveraddr REPLACE_IP --log_config.global_log_options level,nocolor,time

*** Test Cases ***
Determine Location UL-TDOA
    [Tags]  LMF  AMF
    [Documentation]    Request the UE location from the LMF, which runs NRPPa UL-TDOA via the AMF towards
    ...    the rfsim gNB (4 TRPs, one per RX antenna). rfsim has an ideal channel, so only the
    ...    exchange is checked, not the accuracy of the estimate.
    [Setup]    Start Trace    determine_location_ul_tdoa
    [Teardown]    Stop Trace    determine_location_ul_tdoa
    ${result} =    Run Process    curl    --http2-prior-knowledge    -sS    --max-time    60
    ...    -H    Content-Type: application/json    -d    @${LMF_INPUT_DATA}
    ...    -w    \n\%{http_code}    -X    POST    ${LMF_URL}
    Should Be Equal As Integers    ${result.rc}    0    curl failed: ${result.stderr}
    ${body}    ${code} =    Split String From Right    ${result.stdout}    \n    1
    Log    ${body}
    Should Be Equal    ${code}    200    LMF returned ${code}: ${body}
    # OAI LMF answers with a local (cartesian) estimate, not a geographic locationEstimate
    ${location} =    Evaluate    json.loads($body)    json
    Dictionary Should Contain Key    ${location}    localLocationEstimate
    Should Be Equal    ${location}[localLocationEstimate][shape]    POINT
    Dictionary Should Contain Key    ${location}[localLocationEstimate]    point

    # The UL-RTOA k values the gNB measured must reach the LMF unchanged, for every TRP
    ${gnb} =    Get Gnb Container Names
    ${gnb_log} =    Run    docker logs ${gnb}[0] 2>&1
    ${lmf_log} =    Run    docker logs oai-lmf 2>&1
    ${gnb_k} =    Evaluate    sorted(set(re.findall(r'(?<!: )TRP (\\d+), ToA .*?k value (\\d+)', $gnb_log)))    re
    ${lmf_k} =    Evaluate    sorted(set(re.findall(r'trpId: (\\d+) insert key k1 = (\\d+)', $lmf_log)))    re
    Length Should Be    ${gnb_k}    4
    Lists Should Be Equal    ${gnb_k}    ${lmf_k}

*** Keywords ***
LMF Suite Setup
    @{list} =    Create List    oai-amf    oai-smf    oai-udm    oai-nrf    oai-udr    oai-ausf    oai-lmf    mysql    oai-ext-dn    oai-upf
    Prepare Scenario    ${list}    nrf-cn-lmf
    Start Trace    core_network
    Start CN
    Check Core Network Health Status

    Prepare RAN    ${1}    ${1}    gnb_config=template/gnb-positioning.conf    ue_options=${UE_OPTIONS}    use_n3_net=${FALSE}
    Start All gNB
    Check RAN Elements Health Status
    Start All NR UE
    Check RAN Elements Health Status
    ${ue} =    Get UE Container Names
    Wait Until Keyword Succeeds    60s    2s    Get UE IP Address    ${ue}[0]

LMF Suite Teardown
    Stop NR UE
    Stop gNB
    Collect All Ran Logs
    ${docu} =    Create RAN Docu
    Set Suite Documentation    ${docu}    append=${TRUE}
    Down NR UE
    Down gNB
    Suite Teardown Default
