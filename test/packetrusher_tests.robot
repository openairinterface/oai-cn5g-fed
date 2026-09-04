# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------
#
# Handover, paging and scale tests driven by PacketRusher.
#
# Complements omec_gnbsim_tests.robot rather than replacing it. gnbsim keeps the
# lifecycle and idle cycle tests because it reports per-procedure latencies
# natively; PacketRusher covers what gnbsim cannot:
#
#   - N2 handover, which gnbsim cannot complete (it sends a HandoverRequired the
#     AMF fails to encode, so the AMF emits a zero length SCTP write)
#   - Xn handover and paging, which gnbsim does not implement at all
#   - multi UE scale, for comparison against the gnbsim numbers at the same count
#
# PacketRusher has no latency instrumentation and none is derived here: it writes a
# pcap with --pcap that is kept as a debugging artefact, but per-procedure timings
# come from the gnbsim suite, which reports them natively.

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    PacketRusherLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    Launch CN For Packet Rusher
Suite Teardown    Packet Rusher Suite Teardown

Test Teardown    Packet Rusher Test Teardown

*** Variables ***
${SESSION_UE_COUNT}      ${500}

# The template default pool is 12.1.1.0/26, i.e. 62 addresses, which cannot serve
# ${SESSION_UE_COUNT} UEs. The ext-DN route and its healthcheck move with it.
${UE_SUBNET}           12.1.0.0/16

# How long to let a run proceed before inspecting it. PacketRusher does not exit:
# multi-ue keeps the UEs registered until it is stopped.
${HANDOVER_RUN_TIME}   30s
${SCALE_RUN_TIME}      120s

# Time in ms PacketRusher waits before triggering each procedure. The handover
# delay has to leave room for the tunnel to come up and the ping to start first.
${HANDOVER_DELAY}      30000
${DEREG_DELAY}         15000

# Paging: how long before the UE goes idle, and how long it stays there. The
# reconnect delay must be long enough that only the network can wake it.
${IDLE_DELAY}          15000
${RECONNECT_DELAY}     300000
# For the idle cycle the UE is meant to return on its own, so this stays short.
${IDLE_RETURN_DELAY}   10000

# The ping must outlast the handover trigger. At a 0.1s interval each lost packet
# is 100 ms of interruption, which is the resolution of the measurement.
${PING_DURATION}       45
${PING_INTERVAL}       0.1
# Generous: this catches a user plane that broke, not small regressions.
${MAX_INTERRUPTION_MS}    5000

# UPF stress. The floor is deliberately low: it catches a broken datapath, not a
# performance regression. Raise it once there is a baseline on the target machine.
${IPERF_DURATION}      10
${MIN_THROUGHPUT_MBPS}    50

*** Test Cases ***

N2 Handover Between Two gNBs
    [Documentation]    AMF controlled (N2) handover of a single UE with an active PDU
    ...                session and a GTP-U tunnel.
    ...
    ...                A ping runs continuously across the handover rather than after
    ...                it: a ping taken afterwards only shows the tunnel works on the
    ...                target gNB and would pass even if the user plane dropped for
    ...                seconds during the switch. With a fixed send interval the lost
    ...                packets measure the interruption instead of hiding it.
    ...
    ...                --tunnel requires --dedicatedGnb, which PacketRusher enforces,
    ...                and the tunnel needs the gtp5g module loaded on the host. gtp5g
    ...                is namespace aware, so the privileged container creates the
    ...                interface in its own netns and host networking is not needed.
    [Tags]    AMF  SMF  UPF  NRF
    Prepare Packet Rusher    N2 Handover
    ...    multi-ue -n 1 --dedicatedGnb --tunnel --timeBeforeNgapHandover ${HANDOVER_DELAY}
    Start Packet Rusher

    # Wait for the tunnel to exist, but start pinging before the handover fires
    Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    has successfully been configured
    ${stats} =    Ping Across Handover    208950000000031    ${EXT_DN1_IP}
    ...    duration=${PING_DURATION}    interval=${PING_INTERVAL}

    Check Packet Rusher Running
    Registered Ues Should Be    ${1}
    Handover Should Have Completed
    Handover Interruption Should Be Below    ${MAX_INTERRUPTION_MS}    ${stats}

Xn Handover Between Two gNBs
    [Documentation]    Xn (direct, RAN controlled) handover using PathSwitchRequest.
    ...
    ...                NON-MANDATORY: the OAI core does not support Xn handover, so
    ...                this is expected to fail today. It is kept so the suite covers
    ...                the procedure and starts passing on its own once support lands.
    ...                gnbsim cannot express this test at all.
    [Tags]    AMF  SMF  UPF  NRF
    TRY
        Prepare Packet Rusher    Xn Handover
        ...    multi-ue -n 1 --dedicatedGnb --tunnel --timeBeforeXnHandover ${HANDOVER_DELAY}
        Start Packet Rusher
        Sleep    ${HANDOVER_RUN_TIME}
        Check Packet Rusher Running
        Registered Ues Should Be    ${1}
        Packet Rusher Log Should Contain    PathSwitchRequest
    EXCEPT    AS    ${error_message}
        Log    Non-mandatory test failed - Xn handover is not supported by the OAI core: ${error_message}    level=ERROR
    END

Paging Of An Idle UE
    [Documentation]    Network triggered service request: the UE goes to CM-IDLE, the
    ...                ext-DN sends downlink traffic to its address, the core pages it
    ...                and the UE answers with a Service Request.
    ...
    ...                NON-MANDATORY: paging support is still being added to the OAI
    ...                core, so this is expected to fail for now. PacketRusher itself
    ...                implements the full path (NGAP Paging handler, 5G-TMSI match,
    ...                Service Request); gnbsim cannot express this test at all.
    ...
    ...                --timeBeforeReconnecting is deliberately long: PacketRusher
    ...                otherwise brings the UE back on its own about a second after it
    ...                goes idle, which would mask whether paging did anything.
    [Tags]    AMF  SMF  UPF  NRF
    TRY
        Prepare Packet Rusher    Paging
        ...    multi-ue -n 1 --dedicatedGnb --tunnel --timeBeforeIdle ${IDLE_DELAY} --timeBeforeReconnecting ${RECONNECT_DELAY}
        Start Packet Rusher

        Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    has successfully been configured
        ${ue_ip} =    Get Ue Ip From Log
        Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    Switching to 5GMM-IDLE

        Trigger Downlink Traffic    ${EXT_DN1_NAME}    ${ue_ip}

        Wait Until Keyword Succeeds    30s  2s    Packet Rusher Log Should Contain    Receive Paging
        Wait Until Keyword Succeeds    30s  2s    Packet Rusher Log Should Contain    Initiating Service Request
        Packet Rusher Log Should Contain    Receive Service Accept
    EXCEPT    AS    ${error_message}
        Log    Non-mandatory test failed - paging support is still being added to the OAI core: ${error_message}    level=ERROR
    END

Idle Cycle Single UE
    [Documentation]    AN release and return: the UE establishes a PDU session, goes to
    ...                CM-IDLE, then comes back on its own with a Service Request. ICMP
    ...                runs before the release and again after the return, so a pass
    ...                means the user plane genuinely came back rather than just the
    ...                signalling completing.
    ...
    ...                The PacketRusher counterpart of the gnbsim idlecycle profile,
    ...                kept so the two testers can be compared on the same procedure.
    ...                Distinct from the paging test above: here the UE wakes itself on
    ...                a timer, there the network has to page it.
    [Tags]    AMF  SMF  UPF  NRF
    Prepare Packet Rusher    Idle Cycle
    ...    multi-ue -n 1 --dedicatedGnb --tunnel --timeBeforeIdle ${IDLE_DELAY} --timeBeforeReconnecting ${IDLE_RETURN_DELAY}
    Start Packet Rusher

    Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    has successfully been configured
    Ping From Ue    208950000000031    ${EXT_DN1_IP}

    Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    Switching to 5GMM-IDLE
    Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    Initiating Service Request
    Wait Until Keyword Succeeds    30s  2s    Packet Rusher Log Should Contain    Receive Service Accept

    # The point of the test: user plane after coming back from idle
    Ping From Ue    208950000000031    ${EXT_DN1_IP}
    Check Packet Rusher Running

UPF Throughput Single UE
    [Documentation]    Stresses the UPF datapath with iperf3 through a single UE's
    ...                GTP-U tunnel, uplink then downlink.
    ...
    ...                Every byte crosses N3 and the UPF's forwarding path, so this
    ...                measures the UPF rather than the simulator. The UPF runs the
    ...                simple switch datapath by default (enable_bpf_datapath: no in
    ...                the template), which is the configuration under test here.
    ...
    ...                The assertion is a floor, not a target: it catches a datapath
    ...                that has fallen over or collapsed to a fraction of its rate,
    ...                without failing on normal run to run variation.
    [Tags]    UPF  SMF  AMF  NRF
    Prepare Packet Rusher    UPF Throughput    multi-ue -n 1 --dedicatedGnb --tunnel
    Start Packet Rusher
    Wait Until Keyword Succeeds    60s  2s    Packet Rusher Log Should Contain    has successfully been configured

    Start Iperf3 Server    ${EXT_DN1_NAME}

    ${uplink} =    Run Iperf3 From Ue    208950000000031    ${EXT_DN1_IP}
    ...    duration=${IPERF_DURATION}
    ${downlink} =    Run Iperf3 From Ue    208950000000031    ${EXT_DN1_IP}
    ...    duration=${IPERF_DURATION}    reverse=${TRUE}

    Throughput Should Be Above    ${MIN_THROUGHPUT_MBPS}    ${uplink}
    Throughput Should Be Above    ${MIN_THROUGHPUT_MBPS}    ${downlink}
    Check Packet Rusher Running

Multi UE Registration And Deregistration
    [Documentation]    ${SESSION_UE_COUNT} UEs registering at the same time, each
    ...                establishing a PDU session and then deregistering. Deliberately
    ...                mirrors the gnbsim lifecycle test at the same UE count so the
    ...                two testers can be compared.
    ...
    ...                No tunnel here: --tunnel implies --dedicatedGnb, which needs one
    ...                N2/N3 address per gNB and so cannot scale to ${SESSION_UE_COUNT}
    ...                on this network. This is a control plane comparison.
    [Tags]    AMF  AUSF  NRF  UDM  UDR  SMF  UPF
    Prepare Packet Rusher    Multi UE ${SESSION_UE_COUNT}
    ...    multi-ue -n ${SESSION_UE_COUNT} --timeBetweenRegistration 0 --timeBeforeDeregistration ${DEREG_DELAY}
    Start Packet Rusher
    Sleep    ${SESSION_UE_COUNT}
    Registered Ues Should Be    ${SESSION_UE_COUNT}

*** Keywords ***

Launch CN For Packet Rusher
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   packetrusher

    # Enough subscribers for the largest test in the suite
    Add Subscribers To Database    ${SESSION_UE_COUNT}

    # Widen the UE address pool and move the ext-DN route to match
    ${dnns} =    Evaluate    [{"dnn":"oai","pdu_session_type":"IPV4","ipv4_subnet":"12.2.1.0/24"}, {"dnn":"oai.ipv4","pdu_session_type":"IPV4","ipv4_subnet":"12.3.1.0/24"}, {"dnn":"default","pdu_session_type":"IPV4","ipv4_subnet":"${UE_SUBNET}"}, {"dnn":"ims","pdu_session_type":"IPV4V6","ipv4_subnet":"14.1.1.2/24"}]
    @{replace_list} =    Create List    dnns
    Replace In Config    ${replace_list}    ${dnns}
    Set Ext Dn Ue Subnet    ${UE_SUBNET}

    Start CN
    Check Core Network Health Status

    # The route is installed at runtime, so assert it rather than assume it. Without
    # it downlink traffic towards a UE is silently dropped, which would make the
    # paging test fail for the wrong reason.
    Ext Dn Route Should Exist    ${UE_SUBNET}

Packet Rusher Test Teardown
    Run Keyword And Ignore Error    Collect All Packet Rusher Logs
    Run Keyword And Ignore Error    Stop Packet Rusher
    Run Keyword And Ignore Error    Down Packet Rusher
    # The kernel reuses the SCTP association id for the next container. If the AMF
    # has not finished tearing the old one down first, its delayed "Remove gNB with
    # association id N" deletes the gNB context the new container just created, the
    # NG Setup fails and PacketRusher then retries onto addresses it does not own.
    Sleep    5s

Packet Rusher Suite Teardown
    Stop Cn
    Collect All Logs
    Down Cn
    ${docu}=  Create Cn Documentation
    Set Suite Documentation    ${docu}   append=${TRUE}
    ${pr_docu} =   Create Packet Rusher Docu
    Set Suite Documentation    ${pr_docu}   append=${TRUE}
