# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    GNBSimTestLib.py
Resource   common.robot

Variables    vars.py

Suite Setup    Launch NRF CN With PCF HTTP1
Suite Teardown    Suite Teardown Default

Test Setup    Test Setup With Gnbsim
Test Teardown    Test Teardown With Gnbsim

*** Test Cases ***

Attach and Ping HTTP1
    [Tags]    AMF  SMF  UDM  NRF  UDR  AUSF  UPF  PCF
    Start Gnbsim    ${GNBSIM_IN_USE}
    ${ip} =   Check Gnbsim IP    ${GNBSIM_IN_USE}

    Ping From Gnbsim    ${GNBSIM_IN_USE}  ${EXT_DN1_IP}
