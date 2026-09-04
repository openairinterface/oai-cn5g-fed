# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------
#
# Multi-UE attach/detach and service request tests driven by omec-project gnbsim.
#
# These replace the happy-path half of the ngap-tester suites and add what
# ngap-tester never covered: registering many UEs sequentially or all at once,
# and measuring how long each procedure actually took.
#
# gnbsim reports per-UE latencies in microseconds for registration, PDU session
# establishment, service request, UE context release and deregistration; the
# tests assert on those rather than only on pass/fail.

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    OmecGnbsimLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    Launch CN For Omec Gnbsim
Suite Teardown    Omec Gnbsim Suite Teardown

Test Teardown    Omec Gnbsim Test Teardown

*** Variables ***
# Generous ceilings: these catch a procedure that has broken down, not
# small performance regressions, which would make the suite flaky.
${MAX_REG_MS}          5000
${MAX_DEREG_MS}        5000
${MAX_SERVICE_MS}      5000

# Full-cycle scale: register + PDU session + ~2 s of ping + deregister, all UEs
# started at the same time. Every UE holds an address out of the DNN pool for the
# duration, and each also drives an N3 tunnel, so this is heavier per UE than the
# registration-only tests above.
${SESSION_UE_COUNT}    ${500}

# UE pool widened from the template's 12.1.1.0/24, which would cap a run at 254
# sessions. The ext-DN route and its healthcheck are moved to match.
${UE_SUBNET}           12.1.0.0/16

# Repeated Lifecycle Leak Check: how many UEs per iteration and how many
# iterations. Both are meant to be overridden on the command line.
${LEAK_UE_COUNT}       ${100}
# Which gnbsim profile each iteration runs. "lifecycle" releases the PDU session
# explicitly before deregistering; "dereg" deregisters with the session still up,
# which is the path the SMF fix_ue_deregistration_procedure change targets.
${LEAK_PROFILE}        lifecycle
${TEST_ITERATIONS}     ${3}

*** Test Cases ***

Full UE Lifecycle Single UE
    [Documentation]    One UE through the complete lifecycle: register, establish a PDU
    ...                session, send 4 ICMP packets, release the PDU session, then
    ...                deregister. The UE context release happens as part of the
    ...                deregistration, see the config template for why it is not a
    ...                separate step.
    ...
    ...                None of gnbsim's predefined profile types covers this sequence, so
    ...                it is a custom profile; see the iterations block in the config
    ...                template for the exact ordering. Ping comes before the session
    ...                release because there is no user plane left afterwards.
    [Tags]    AMF  AUSF  NRF  UDM  UDR  SMF  UPF
    Run Gnbsim Profile    lifecycle    ${1}
    Procedure Should Be Reported For All Ues    TotalRegTime               ${1}
    Procedure Should Be Reported For All Ues    TotalPduEstTime            ${1}
    Procedure Should Be Reported For All Ues    TotalDeregistrationTime    ${1}
    # gnbsim publishes no statistics for these two, so assert them explicitly or the
    # report never shows that the ICMP and the session release were checked
    Procedure Should Pass For All Ues    USER-DATA-PACKET-GENERATION-PROCEDURE          ${1}
    Procedure Should Pass For All Ues    UE-REQUESTED-PDU-SESSION-RELEASE-PROCEDURE     ${1}
    Procedure Time Should Be Below    TotalRegTime      ${MAX_REG_MS}
    Procedure Time Should Be Below    TotalDeregistrationTime    ${MAX_DEREG_MS}

Multiple UE test 
    #Full UE Lifecycle ${SESSION_UE_COUNT} UEs Simultaneously
    [Documentation]    The same lifecycle as the single UE test, run by
    ...                ${SESSION_UE_COUNT} UEs started at the same time.
    ...
    ...                ICMP is reply driven, as everywhere else, so this only passes if
    ...                the echo replies come back for every UE. That has been measured
    ...                to fail at this scale: all UEs established their PDU session and
    ...                then saw zero replies. The failure is kept visible on purpose.
    [Tags]    AMF  AUSF  NRF  UDM  UDR  SMF  UPF
    Run Gnbsim Profile    lifecycle    ${SESSION_UE_COUNT}    exec_in_parallel=${TRUE}    timeout=1800s
    Procedure Should Be Reported For All Ues    TotalRegTime               ${SESSION_UE_COUNT}
    Procedure Should Be Reported For All Ues    TotalPduEstTime            ${SESSION_UE_COUNT}
    Procedure Should Be Reported For All Ues    TotalDeregistrationTime    ${SESSION_UE_COUNT}
    # The ICMP result is otherwise invisible in the report: gnbsim publishes no
    # statistics for user data generation
    Procedure Should Pass For All Ues    USER-DATA-PACKET-GENERATION-PROCEDURE          ${SESSION_UE_COUNT}
    Procedure Should Pass For All Ues    UE-REQUESTED-PDU-SESSION-RELEASE-PROCEDURE     ${SESSION_UE_COUNT}
    Log Procedure Times    TotalRegTime
    Log Procedure Times    TotalPduEstTime
    Log Procedure Times    TotalDeregistrationTime

Idle Cycle Single UE
    [Documentation]    One UE through an idle/active cycle: register, establish a PDU
    ...                session, ICMP, AN release to CM-IDLE, Service Request to come
    ...                back, ICMP again, then deregister.
    ...
    ...                The second ICMP round is the point of the test: the Service
    ...                Request reactivates the existing PDU session rather than creating
    ...                a new one, so pings working again is what proves the user plane
    ...                actually returned. ICMP is reply driven here, so the procedure
    ...                only passes if the echo replies come back.
    [Tags]    AMF  AUSF  NRF  UDM  UDR  SMF  UPF
    Run Gnbsim Profile    idlecycle    ${1}
    Procedure Should Be Reported For All Ues    TotalRegTime            ${1}
    Procedure Should Be Reported For All Ues    TotalPduEstTime         ${1}
    Procedure Should Be Reported For All Ues    TotalServiceReqTime     ${1}
    Procedure Should Be Reported For All Ues    TotalCtxReleaseTime     ${1}
    Procedure Should Be Reported For All Ues    TotalDeregistrationTime    ${1}
    # Twice: once before the AN release and once after the Service Request. The
    # second round is what proves the user plane actually came back
    Procedure Should Pass For All Ues    USER-DATA-PACKET-GENERATION-PROCEDURE    ${1}    times_per_ue=${2}
    Procedure Time Should Be Below    TotalServiceReqTime    ${MAX_SERVICE_MS}

Release And Re-establish PDU Session Single UE
    [Documentation]    One UE that establishes a PDU session, releases it, and then
    ...                establishes a second one without ever deregistering in
    ...                between. This is what a modem does across an mbimcli
    ...                --disconnect / --connect pair, and no other test in the suite
    ...                asks the core for a second session while the UE stays
    ...                registered.
    ...
    ...                The second ICMP round is the point of the test. An SMF that
    ...                releases a session's resources twice hands the PDR, QER, FAR
    ...                and URR ids back to their generators before the UE's Release
    ...                Complete arrives, and the RAN then rejects the second
    ...                establishment with 5GSM cause #26, insufficient resources. A
    ...                session that is accepted but has no user plane fails here too,
    ...                because ICMP is reply driven.
    [Tags]    AMF  AUSF  NRF  UDM  UDR  SMF  UPF
    Run Gnbsim Profile    relcycle    ${1}
    Procedure Should Be Reported For All Ues    TotalRegTime               ${1}
    Procedure Should Be Reported For All Ues    TotalDeregistrationTime    ${1}
    # times_per_ue is what makes this test bite: the UE runs both of these twice,
    # so a run that gave up after the release would otherwise still look like a pass
    Procedure Should Pass For All Ues    PDU-SESSION-ESTABLISHMENT-PROCEDURE           ${1}    times_per_ue=${2}
    Procedure Should Pass For All Ues    USER-DATA-PACKET-GENERATION-PROCEDURE         ${1}    times_per_ue=${2}
    Procedure Should Pass For All Ues    UE-REQUESTED-PDU-SESSION-RELEASE-PROCEDURE    ${1}

Repeated Lifecycle Leak Check
    [Documentation]    Runs the lifecycle ${LEAK_UE_COUNT} UEs at a time,
    ...                ${TEST_ITERATIONS} times in a row, against a core network that
    ...                is deployed once and never restarted.
    ...
    ...                The point is not the individual runs but what the core keeps in
    ...                between: after every UE has deregistered the AMF's statistics
    ...                table must be empty. A count that grows from one iteration to
    ...                the next means UE contexts are leaking, and a later iteration
    ...                failing while the first passed points the same way.
    ...
    ...                Set the counts on the command line, for example
    ...                --variable TEST_ITERATIONS:5 --variable LEAK_UE_COUNT:80
    [Tags]    AMF  AUSF  NRF  UDM  UDR  SMF  UPF
    FOR    ${iteration}    IN RANGE    1    ${TEST_ITERATIONS} + 1
        Log    --- iteration ${iteration} of ${TEST_ITERATIONS} ---    console=${TRUE}
        Run Gnbsim Profile    ${LEAK_PROFILE}    ${LEAK_UE_COUNT}    exec_in_parallel=${TRUE}    timeout=1800s
        Procedure Should Be Reported For All Ues    TotalRegTime               ${LEAK_UE_COUNT}
        Procedure Should Be Reported For All Ues    TotalDeregistrationTime    ${LEAK_UE_COUNT}
        Procedure Should Pass For All Ues    USER-DATA-PACKET-GENERATION-PROCEDURE    ${LEAK_UE_COUNT}
        Log Procedure Times    TotalRegTime
        Log Procedure Times    TotalDeregistrationTime

        # The gnbsim container has to go before the check, otherwise its NGAP
        # association keeps the AMF holding the contexts legitimately
        Collect Gnbsim Metrics    ${TEST_NAME} iteration ${iteration}
        Stop Omec Gnbsim
        Down Omec Gnbsim
        # Run Gnbsim Profile starts a trace named after the test. Inside this loop the
        # name repeats, so it must be closed or the next iteration fails with
        # "There is already a trace running!"
        Stop Trace    ${TEST_NAME}

        # The statistics table is refreshed only every statistics_timer_interval
        # seconds, so allow more than one interval before believing it
        Wait Until Keyword Succeeds    90s  10s    Core Should Have No Ue Context
    END

*** Keywords ***

Launch CN For Omec Gnbsim
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   omec-gnbsim

    # Enough subscribers for the largest test in the suite
    Add Subscribers To Database    ${SESSION_UE_COUNT}

    # Widen the UE address pool so PDU sessions are not capped at 62 addresses
    ${dnns} =    Evaluate    [{"dnn":"oai","pdu_session_type":"IPV4","ipv4_subnet":"12.2.1.0/24"}, {"dnn":"oai.ipv4","pdu_session_type":"IPV4","ipv4_subnet":"12.3.1.0/24"}, {"dnn":"default","pdu_session_type":"IPV4","ipv4_subnet":"${UE_SUBNET}"}, {"dnn":"ims","pdu_session_type":"IPV4V6","ipv4_subnet":"14.1.1.2/24"}]
    @{replace_list} =    Create List    dnns
    Replace In Config    ${replace_list}    ${dnns}
    @{replace_list} =    Create List    log_level    general
    Replace In Config    ${replace_list}    info

    Set Ext Dn Ue Subnet    ${UE_SUBNET}

    Start Trace    core_network
    Start CN
    Check Core Network Health Status

Run Gnbsim Profile
    [Documentation]    Runs one gnbsim profile to completion and asserts it passed.
    ...                The wait scales with the UE count: a sequential run of N UEs
    ...                cannot finish faster than N times the per-UE procedure time.
    [Arguments]    ${profile}    ${ue_count}=${1}    ${exec_in_parallel}=${FALSE}    ${timeout}=120s
    Prepare Omec Gnbsim    ${profile}    ${ue_count}    ${exec_in_parallel}
    Start Trace    ${TEST_NAME}
    Start Omec Gnbsim
    # gnbsim exits on its own
    Wait Until Keyword Succeeds    ${timeout}  2s    Check Omec Gnbsim Done
    Check Omec Gnbsim Result

Omec Gnbsim Test Teardown
    Run Keyword And Ignore Error    Collect All Omec Gnbsim Logs
    Run Keyword And Ignore Error    Collect Gnbsim Metrics    ${TEST_NAME}
    Run Keyword And Ignore Error    Stop Omec Gnbsim
    Run Keyword And Ignore Error    Down Omec Gnbsim
    Stop Trace    ${TEST_NAME}

Omec Gnbsim Suite Teardown
    Stop Cn
    Collect All Logs
    Stop Trace   core_network
    Down Cn
    ${docu}=  Create Cn Documentation
    Set Suite Documentation    ${docu}   append=${TRUE}
    ${gnbsim_docu} =   Create Omec Gnbsim Docu
    Set Suite Documentation    ${gnbsim_docu}   append=${TRUE}
    ${metrics} =   Create Gnbsim Metrics Report
    Set Suite Documentation    ${metrics}   append=${TRUE}
    Log    ${metrics}
