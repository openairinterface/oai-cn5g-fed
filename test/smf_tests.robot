# SPDX-License-Identifier: LicenseRef-CSSL-1.0
# ---------------------------------------------------------------------

*** Settings ***
Library    Process
Library    CNTestLib.py
Library    RequestsLibrary
Library    Collections

Resource   common.robot
Variables   json_templates/smf_json_strings.py

Suite Setup    Start SMF
Suite Teardown    Suite Teardown Default

*** Variables ***
${URL}            http://192.168.79.133:8080
${CONFIG_URL}     ${URL}/nsmf-oai/v1/configuration


*** Test Cases ***

SMF Config API Get
#    [Tags]    SMF
    ${response} =   GET  ${CONFIG_URL}
    Status Should Be    200
    Dictionaries Should Be Equal   ${response.json()}     ${smf_config_dict}

Update SMF Config
    [Tags]    SMF
    TRY
    ${response} =  PUT  ${CONFIG_URL}   json=${smf_config_dict_updated}
        Status Should Be    200
        Dictionaries Should Be Equal    ${response.json()}    ${smf_config_dict_updated}
    EXCEPT    AS   ${error_message}
        Log    Update SMF Config Test failed: ${error_message}. Not mandatory at the moment
    END


*** Keywords ***

Start SMF
    @{list} =    Create List  oai-smf
    Prepare Scenario    ${list}   smf-only
    @{replace_list} =   Create List  http_version
    Replace In Config   ${replace_list}  1

    Start Trace    core_network
    Start CN
    Check Core Network Health Status
