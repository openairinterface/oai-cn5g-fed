# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------
#
# SMF (N7) and PCF (N5) policy-control HTTP API integration tests.
#
# These drive the SMF's Nsmf_Callback SM-policy update endpoint [TS 29.512
# 4.2.3.2] and the PCF's Npcf_PolicyAuthorization app-sessions API [TS 29.514
# 4.2] against a running core with a UE that holds a live PDU session.
#
# The SBI here speaks cleartext HTTP/2 with prior knowledge, which neither
# RequestsLibrary nor httpx can produce, so the assertions live in standalone
# curl-based Python scripts under scripts/policy/. This suite deploys the core,
# holds a real PDU session open with omec gnbsim, and runs those scripts against
# it, asserting on their exit code. Each script prints its own per-check report.


*** Settings ***
Library    Process
Library    CNTestLib.py
Library    OmecGnbsimLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    Policy Suite Setup
Suite Teardown    Policy Suite Teardown

Test Teardown    Policy Test Teardown

*** Variables ***
# Generated-topology SBI endpoints (see template/docker-compose-all-nfs.yaml).
${SMF_HOST}          192.168.79.133
${PCF_HOST}          192.168.79.139
${SBI_PORT}          8080

# The AF/curl exec target. The core network images (trf-gen, oai-smf, oai-pcf)
# ship no curl, so a small curlimages/curl sidecar is started sharing oai-ext-dn's
# network namespace: it lands on the same on-net IP (192.168.79.141) and provides
# a real curl with HTTP/2, matching how an AF would originate the request on-net.
${AF_CONTAINER}      oai-af-curl
${AF_IP}             192.168.79.141

# The omec "policyhold" profile uses DNN "default" (pool 12.1.1.0/26) on slice
# sst 222 / sd 00007B; the PCF app-session must line up with that session.
${UE_POOL_PREFIX}    12.1.1.
${SESSION_DNN}       default
${SESSION_SST}       222
${SESSION_SD}        00007B
${QOS_REFERENCE}     OAI_QOS_GBR_VIDEO_1

${SMF_SCRIPT}        ${CURDIR}/scripts/policy/smf_pcf_n7_tests.py
${PCF_SCRIPT}        ${CURDIR}/scripts/policy/pa_app_session_tests.py

*** Test Cases ***

SMF N7 SM-Policy Update Notification
    [Documentation]    POSTs an SmPolicyNotification to the SMF's N7 update callback
    ...                and asserts a spec-compliant response. With a live session and
    ...                its real scid this exercises the delta computation and N4/N1N2
    ...                staging downstream of the callback; without one it still
    ...                validates the callback routing, parsing and response envelope.
    [Tags]    SMF
    Bring Up Ue Session
    ${scid} =    Wait Until Keyword Succeeds    30s    3s    Get Smf Scid    require_found=${TRUE}
    ${result} =    Run Process    python3    ${SMF_SCRIPT}    lifecycle
    ...    env:SMF_HOST=${SMF_HOST}    env:SMF_PORT=${SBI_PORT}
    ...    env:PCF_CONTAINER=${AF_CONTAINER}    env:SCID=${scid}
    ...    stdout=${OUTPUT_DIR}/n7_test_stdout.txt    stderr=STDOUT
    Log    ${result.stdout}
    Should Be Equal As Integers    ${result.rc}    0    N7 policy notification test failed

PCF N5 Policy Authorization App-Session Lifecycle
    [Documentation]    Runs create -> get -> patch (modify/add/remove) -> reject-case
    ...                -> delete -> get against the PCF's app-sessions API, bound to
    ...                the live UE address and the operator qosReference
    ...                OAI_QOS_GBR_VIDEO_1.
    [Tags]    PCF
    ${ue_ip} =    Bring Up Ue Session
    ${result} =    Run Process    python3    ${PCF_SCRIPT}    lifecycle
    ...    env:PCF_HOST=${PCF_HOST}    env:PCF_PORT=${SBI_PORT}
    ...    env:AF_CONTAINER=${AF_CONTAINER}    env:UE_IPV4=${ue_ip}
    ...    env:DNN=${SESSION_DNN}    env:SNSSAI_SST=${SESSION_SST}    env:SNSSAI_SD=${SESSION_SD}
    ...    env:QOS_REFERENCE=${QOS_REFERENCE}    env:NOTIF_URI=http://${AF_IP}/notifications
    ...    stdout=${OUTPUT_DIR}/n5_test_stdout.txt    stderr=STDOUT
    Log    ${result.stdout}
    Should Be Equal As Integers    ${result.rc}    0    N5 app-session lifecycle test failed

*** Keywords ***

Policy Suite Setup
    [Documentation]    Deploys the core with PCF, then starts an on-net curl sidecar
    ...                that the policy scripts exec into to speak HTTP/2 to the SBI.
    Launch NRF CN With PCF For Policy Tests
    Start Af Curl Sidecar

Start Af Curl Sidecar
    [Documentation]    Runs a curlimages/curl container sharing oai-ext-dn's network
    ...                namespace, so it reaches the SBI on 192.168.79.141 with a real
    ...                curl that supports HTTP/2 prior knowledge.
    ${img} =    Get Curl Image
    Run Process    docker    rm    -f    ${AF_CONTAINER}
    ${result} =    Run Process    docker    run    -d    --name    ${AF_CONTAINER}
    ...    --network    container:oai-ext-dn    --entrypoint    sleep    ${img}    infinity
    Should Be Equal As Integers    ${result.rc}    0
    ...    Failed to start curl sidecar ${AF_CONTAINER}: ${result.stderr}

Stop Af Curl Sidecar
    Run Process    docker    rm    -f    ${AF_CONTAINER}

Bring Up Ue Session
    [Documentation]    Starts one UE that registers, establishes a PDU session and
    ...                then holds it (the profile waits ~40s before deregistering),
    ...                and returns the IPv4 the SMF allocated to it. The HTTP test
    ...                runs inside that hold window; Policy Test Teardown then waits
    ...                for the UE to deregister and the gnbsim container to exit.
    Prepare Omec Gnbsim    policyhold    ${1}
    # Prepare Omec Gnbsim forces perUserTimeout to max(60, ueCount); raise it back
    # above the in-profile hold so the held UE is not failed as a timeout.
    @{timeout_path} =    Create List    configuration    customProfiles    policyhold    perUserTimeout
    Replace In Gnbsim Config    ${timeout_path}    ${180}
    Start Trace    ${TEST_NAME}
    Start Omec Gnbsim
    ${ue_ip} =    Wait Until Keyword Succeeds    90s    2s    Get Ue Ipv4 From Smf    ${UE_POOL_PREFIX}
    RETURN    ${ue_ip}

Policy Test Teardown
    Run Keyword And Ignore Error    Collect All Omec Gnbsim Logs
    Run Keyword And Ignore Error    Wait Until Keyword Succeeds    60s    2s    Check Omec Gnbsim Done
    Run Keyword And Ignore Error    Stop Omec Gnbsim
    Run Keyword And Ignore Error    Down Omec Gnbsim
    Stop Trace    ${TEST_NAME}

Policy Suite Teardown
    Run Keyword And Ignore Error    Stop Af Curl Sidecar
    Stop Cn
    Collect All Logs
    Stop Trace    core_network
    Down Cn
    ${docu} =    Create Cn Documentation
    Set Suite Documentation    ${docu}    append=${TRUE}
