# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    NGAPTesterLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    Launch eBPF CN
Suite Teardown    Suite Teardown Default

Test Setup    Test Setup NGAP Tester
Test Teardown    Test Teardown NGAP Tester

*** Test Cases ***
# TODO all test cases fail because of no user plane, but eBPF setup is fine (see eBPF tests)

#NGAP Tester TC 1 Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    Run NGAP Tester Test   TC1     default    ${FALSE}
#
#NGAP Tester TC 1X2 Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    Run NGAP Tester Test   TC1X2   default    ${FALSE}
#
#NGAP Tester TC 1V4V6 Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    Run NGAP Tester Test   TC1V4V6   default   ${FALSE}
#
#NGAP Tester TC 23502_49122 Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    TRY
#        Run NGAP Tester Test   TC23502_49122   default   ${FALSE}
#    EXCEPT    AS   ${error_message}
#        Log   Non-mandatory NGAP Tester test failed: TC23502_49122  level=ERROR
#    END
#
#NGAP Tester TC 23502_4913 Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    TRY
#        Run NGAP Tester Test   TC23502_4913   default   ${FALSE}
#    EXCEPT    AS   ${error_message}
#        Log   Non-mandatory NGAP Tester test failed: TC23502_4913  level=ERROR
#    END
#
#NGAP Tester TC 24501_54137B_T3560 Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    TRY
#        Run NGAP Tester Test   TC24501_54137B_T3560   default   ${FALSE}
#    EXCEPT    AS   ${error_message}
#        Log   Non-mandatory NGAP Tester test failed: TC24501_54137B_T3560  level=ERROR
#    END
#
#NGAP Tester TC 24501_54137EF Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    Run NGAP Tester Test   TC24501_54137EF   default   ${FALSE}
#
#NGAP Tester TC N Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    Run NGAP Tester Test   TCN   default   ${FALSE}
#
#NGAP Tester TC SERVICE_REQUEST_24501_5611c Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611c   default   ${FALSE}
#
#NGAP Tester TC SERVICE_REQUEST_24501_5611d Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    # TODO, this test case should not fail
#    TRY
#        Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611d   default   ${FALSE}
#    EXCEPT    AS   ${error_message}
#        Log   Mandatory NGAP Tester test failed: TC_SERVICE_REQUEST_24501_5611d  level=ERROR
#    END
#
#NGAP Tester TC SERVICE_REQUEST_24501_5611e Basic NRF EBPF Default
#    [Tags]    AMF  SMF  UPF
#    TRY
#        Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611e   default   ${FALSE}
#    EXCEPT    AS   ${error_message}
#        Log   Non-mandatory NGAP Tester test failed: TC_SERVICE_REQUEST_24501_5611e  level=ERROR
#    END
