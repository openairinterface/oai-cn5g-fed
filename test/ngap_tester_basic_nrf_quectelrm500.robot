# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    NGAPTesterLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    NGAP Tester Suite Setup For Quectel
Suite Teardown    Suite Teardown Default

Test Setup    Test Setup NGAP Tester
Test Teardown    Test Teardown NGAP Tester

*** Test Cases ***

NGAP Tester TC 1 Basic NRF quectelrm500
    [Tags]    AMF  AUSF  NRF  NSSF  PCF  SMF  UDM  UDR  UPF
    Run NGAP Tester Test   TC1     quectelrm500

NGAP Tester TC 1X2 Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    Run NGAP Tester Test   TC1X2   quectelrm500

NGAP Tester TC 1V4V6 Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    Run NGAP Tester Test   TC1V4V6   quectelrm500

NGAP Tester TC 23502_49122 Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    TRY
        Run NGAP Tester Test   TC23502_49122   quectelrm500
    EXCEPT    AS   ${error_message}
        Log   Non-mandatory NGAP Tester test failed: TC23502_49122  level=ERROR
    END

NGAP Tester TC 23502_4913 Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    TRY
        Run NGAP Tester Test   TC23502_4913   quectelrm500
    EXCEPT    AS   ${error_message}
        Log   Non-mandatory NGAP Tester test failed: TC23502_4913  level=ERROR
    END

NGAP Tester TC 24501_54137B_T3560 Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    TRY
        Run NGAP Tester Test   TC24501_54137B_T3560   quectelrm500
    EXCEPT    AS   ${error_message}
        Log   Non-mandatory NGAP Tester test failed: TC24501_54137B_T3560  level=ERROR
    END

NGAP Tester TC 24501_54137EF Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    Run NGAP Tester Test   TC24501_54137EF   quectelrm500

NGAP Tester TC N Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    Run NGAP Tester Test   TCN   quectelrm500

NGAP Tester TC SERVICE_REQUEST_24501_5611c Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611c   quectelrm500

NGAP Tester TC SERVICE_REQUEST_24501_5611d Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    # TODO, this test case should not fail
    TRY
        Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611d   quectelrm500
    EXCEPT    AS   ${error_message}
        Log   Non-mandatory NGAP Tester test failed: TC_SERVICE_REQUEST_24501_5611d  level=ERROR
    END

NGAP Tester TC SERVICE_REQUEST_24501_5611d_Easy Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611d_easy   quectelrm500

NGAP Tester TC SERVICE_REQUEST_24501_5611e Basic NRF quectelrm500
    [Tags]    AMF  SMF  UPF
    TRY
        Run NGAP Tester Test   TC_SERVICE_REQUEST_24501_5611e   quectelrm500
    EXCEPT    AS   ${error_message}
        Log   Non-mandatory NGAP Tester test failed: TC_SERVICE_REQUEST_24501_5611e  level=ERROR
    END


*** Keywords ***
NGAP Tester Suite Setup For Quectel
    @{list} =    Create List  oai-amf   oai-smf   oai-udm   oai-nrf  oai-udr  oai-ausf  mysql  oai-ext-dn  oai-upf
    Prepare Scenario    ${list}   nrf-cn
    # Quectel uses integrity algorithms, we have to change priority here
    @{replace_list} =   Create List  amf  supported_integrity_algorithms
    @{algorithms} =     Create List  NIA2
    Replace In Config   ${replace_list}   ${algorithms}

    Start Trace    core_network
    Start CN
    Check Core Network Health Status