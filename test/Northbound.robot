*** Settings ***
Library    OperatingSystem
Library    RfSimLib.py
Library    MobSimTestLib.py
Library    NotificationTest.py    WITH NAME    NotifTest
Library    5gcsdk/src/main/init_handler.py    WITH NAME    Handler
Library    MobSimTestLib.py

Resource   common.robot

Variables    vars.py

Suite Setup    Northbound Suite Setup
Suite Teardown    Northbound Suite Teardown

*** Test Cases ***
Check AMF Registration Notifications
    [tags]  North
    [Setup]    Test Setup For Northbound 
    [Teardown]    Test Teardown for Northbound 
    [Documentation]    Check Callback registration notification
    ${logs} =    Get AMF Report Logs
    Wait Until Keyword Succeeds  60s  6s    Check AMF Reg Callback    ${3}    ${logs}

Check AMF Location Report  
    [tags]  North
    [Setup]    Test Setup For Northbound 
    [Teardown]    Test Teardown for Northbound 
    [Documentation]    Check Callback Location Notification
    ${logs} =    Get AMF Report Logs
    Wait Until Keyword Succeeds  60s  6s    Check AMF Location Report Callback    '${logs}'    ${3}

Check SMF Notifications
    [tags]  North
    [Setup]    Test Setup For Northbound 
    [Teardown]    Test Teardown for Northbound 
    [Documentation]    Check SMF Callback Notification (PDU Session Establishment)
    ${logs} =    Get UE Info From SMF Log
    Wait Until Keyword Succeeds  60s  6s    Check SMF Callback    '${logs}'    ${3}

#Disabling the test case due to issues in SMF v2.1.0 works
#Check SMF Traffic Notification
#    [tags]   North
#    [Setup]    Test Setup For Northbound 
#    [Teardown]    Test Teardown for Northbound 
#    [Documentation]    Check SMF Traffic Notification Callback
#    @{UEs}=    Get UE container Names
#    Start Iperf3 Server     ${EXT_DN1_NAME}
#    FOR     ${ue}   IN    @{UEs}   
#        ${ip}=   Get UE IP Address   ${ue}
#        ${supi}=   Get UE SUPI    ${ue}
#        Start Iperf3 Client     ${ue}  ${ip}  ${EXT_DN1_IP_N3}  bandwidth=3
#        Run Keyword And Ignore Error   Wait and Verify Iperf3 Result    ${ue}  ${3}  #for bandwidth check, not important
#        ${result_Iperf}=    Get Iperf3 Results   ${ue}
#        Wait Until Keyword Succeeds  60s  6s   Check Ue Traffic Notification   ${result_Iperf}  ${supi}
#    END

Check AMF Deregistration Notification
    [tags]  North
    [Setup]    Test Setup for Deregistration
    [Teardown]    Test Teardown With RAN
    [Documentation]    Remove all UEs added during the test and check their DEREGISTRATION Notifications
    ${logs} =    Get AMF Report Logs
    Wait Until Keyword Succeeds  60s  6s    Check AMF Dereg Callback    ${logs}    ${3}

Check AMF Mobility Location Report
    [tags]  North
    [Setup]    Test Setup With MobSim
    [Teardown]    Test Teardown With MobSim
    [Documentation]    Check AMF Mobility Location Report Callback
    Wait Until Keyword Succeeds  120s  3s    Check AMF Location Mobility Report Callback
    
*** Keywords ***
Northbound Suite Setup 
    Launch Northbound Test CN
   
    Start All gNB
    Check RAN Elements Health Status
    Launch Mongo
    Handler.Start Handler
    Sleep   10s
    
    @{UEs}=    Get UE container Names
    FOR   ${ue}   IN    @{UEs}   
        Start NR UE    ${ue}
        Sleep  2s
    END    
    Wait Until Keyword Succeeds  60s  1s  Check RAN Elements Health Status

Northbound Suite Teardown
    Stop NR UE
    Run Keyword And Ignore Error    Handler.Stop Handler
    Down Mongo
    Stop gNB
    Collect All Ran Logs
    ${docu}=   Create RAN Docu
    Set Suite Documentation    ${docu}   append=${TRUE}
    Down NR UE
    Down gNB
    Suite Teardown Default
Launch Mongo
    Run    docker run -d -p 27017:27017 --name=mongo-northbound mongo:latest

Down Mongo   
     Run    docker stop mongo-northbound
     Run    docker rm mongo-northbound

Test Setup For Northbound
    Start Trace    ${TEST_NAME}

Test Teardown For Northbound
    Stop Trace    ${TEST_NAME}

Test Setup for Deregistration
    Test Setup For Northbound 
    Stop NR UE
    Down NR UE

Test Teardown With RAN
    Handler.Stop Handler
    Down Mongo
    Stop gNB
    Collect All RAN Logs
    Down gNB
    Test Teardown For Northbound

Test Setup With MobSim
    Test Setup For Northbound
    Prepare MobSim    ${3}    ${1}
    Update Event Rate    ${0.08}
    Launch Mongo
    Handler.Start Handler
    Start MobSim
    Sleep   15s

Test Teardown With MobSim
    Stop MobSim
    Collect All Mobsim Logs
    ${docu}=   Create MobSim Docu
    Set Suite Documentation    ${docu}   append=${TRUE}
    Down MobSim
    Handler.Stop Handler
    Down Mongo
    Test Teardown For Northbound

Get AMF Report Logs
    ${logs}    Run    docker logs oai-amf | sed -n '/--UEs. Information--/,/----------------------------/p' 
    RETURN    ${logs}

Get AMF Location Report Logs
    ${logs}    Run    docker logs oai-amf | sed -n '/"type":"LOCATION_REPORT"/p' 
    RETURN    ${logs}

Get UE Info From SMF Log
     ${logs}    Run    docker logs oai-smf | sed -n '/SMF CONTEXT:/,/^[[:space:]]*$/p' 
     RETURN    ${logs}
