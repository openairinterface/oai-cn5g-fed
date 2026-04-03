# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    GNBSimTestLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    Launch EBPF CN
Suite Teardown    Suite Teardown Default

Test Setup    Test Setup eBPF Tests
Test Teardown    Test Teardown eBPF Tests

*** Test Cases ***

Attach and Ping eBPF
    [Tags]  UPF
    Start Gnbsim    ${GNBSIM_IN_USE}
    ${ip} =   Check Gnbsim IP    ${GNBSIM_IN_USE} 
    
    Ping From Gnbsim    ${GNBSIM_IN_USE}  ${EXT_DN_EBPF_IP}
    Ping From Gnbsim    ${GNBSIM_IN_USE}  8.8.8.8

eBPF Bandwidth 400Mbits
    [Tags]  UPF
    Start Gnbsim    ${GNBSIM_IN_USE}
    ${ip} =   Check Gnbsim IP    ${GNBSIM_IN_USE}

    # UPLINK
    Start Iperf3 Server     ${EXT_DN_EBPF_NAME}
    Start Iperf3 Client     ${GNBSIM_IN_USE}  ${ip}  ${EXT_DN_EBPF_NAME}  bandwidth=400
    Wait and Verify Iperf3 Result   ${GNBSIM_IN_USE}  400

    # DOWNLINK
    Start Iperf3 Server     ${GNBSIM_IN_USE}
    Start Iperf3 Client     ${EXT_DN_EBPF_NAME}  ${EXT_DN_EBPF_IP}  ${ip}  bandwidth=400
    Wait and Verify Iperf3 Result   ${EXT_DN_EBPF_NAME}  400

*** Keywords ***

Test Setup eBPF Tests
    ${gnbsim_name} =   Prepare Gnbsim    single_interface=${FALSE}
    Set Test Variable   ${GNBSIM_IN_USE}   ${gnbsim_name}
    Start Trace    ${TEST_NAME}   signaling_only=${FALSE}

Test Teardown eBPF Tests
    Stop Gnbsim   ${GNBSIM_IN_USE}
    Collect All Gnbsim Logs
    Down Gnbsim    ${GNBSIM_IN_USE}
    Stop Trace    ${TEST_NAME}
