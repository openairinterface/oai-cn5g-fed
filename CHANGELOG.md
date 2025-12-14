# RELEASE NOTES: #

## v2.2.0 -- December 2025 ##

* Archived Network Function:
  * UPF-VPP
* Helm charts moved to `oai/orchestration/charts`
* Tutorials
  - Add tutorial for Ethernet PDU session
  - Add tutorial for QOS
  - Add tutorial for PCF provisioning
* Future Fixes for all NFs
  - Add support for Ubuntu 24.04
  - Add support for RHEL 10, update container images to UBI 10
  - Fix build issue in non-containerized environment (except UPF)
* `AMF` changes:
  * Features
    - AMF Location Service APIs
    - AMF Mobile Terminated Service APIs
    - AMF Status Change APIs
    - AM Policy Association Retrieval/Update/Termination
    - SMF Selection Subscription Data Retrieval
    - Access and Mobility Subscription Data Retrieval
    - UE Context In SMF Data Retrieval
    - AMF Registration for 3GPP Access
    - PCF discovery
    - TLS support
  * Fixes
    - Address UE-originated de-registration request in race condition
    - Integrity check for Security Mode complete
    - NR Cell ID
    - MCC, MNC with 3 digits
    - Release NAS signalling after the completion of the registration procedure: FOR is set to nN Follow-on request pending
    - Use SUPI as UE identity
    - Disable SCTP delays to support multiple UEs at the same time
* `SMF` changes:
  * Features
    - Ethernet PDU session
    - Support framed routing
    - Support QoS enforcement
    - Support SMF Registration/De-registration towards UDM
    - SM Policy Association Establishment/Modification/Termination
    - SM Policy Notification
    - SM Context Status Notify
    - Trigger the association with the UPFs in the configuration file even NRF discovery option is enabled
    - Support TLS
  * Fixes
    - Default QoS info: ARP values
    - Add NF Service List in SMF profile
    - Fix SmfEventExposurePathSubscriptionsSubscriptionId
    - Fix SMF SM context update endpoint
    - Add SubscriptionID for SubscriptionData
    - Fix NRF URI
    - Fix NRF NF Discovery SearchNFInstances URI
    - Fix UDM SDM URI
    - Mime parser with insensitive content-type
    - SD with/without 0x prefix
    - Add fix for QoSFlowDescriptons and QoSFlows IE length
    - Fix GTP TEID IE
* Miscellaneous
  - Code refactoring: NAS SM IEs, NGAP IEs
* `UPF` changes:
  * Features
    - Framed routing for simple switch UPF
    - Ethernet PDU session
    - Configure eBPF map sizes via config file
    - Manipulate BPF debug logging
    - Support QoS enforcement
  * Fixes
    - Fix the pFAR add to map
    - Apply SEID fix on framed routing change
    - Fix XDP_DROP does not exit in TC
    - Update code to manage the TC BPF program separately
  * Future Fixes
    - Add support for framed routing for eBPF UPF
    - Improve throughput of simple switch UPF
* `NRF` changes:
  * Fixes
    - Update LTTNG to v0.15.0 to avoid building issue
* `UDR` changes:
  * Fixes
    - Use SUPI as UE identity
    - Use MySQL query with lowercase in JSON
    - Fix MySQL query to work with SD with/without 0x prefix
    - Update LTTNG to v0.15.0 to avoid building issue
* `UDM` changes:
  * Fixes
    - Update LTTNG to v0.15.0 to avoid building issues
* `AUSF` changes:
  * Fixes
    - Fix UEAuthenticationCtx, AuthResult IEs
    - Update LTTNG to v0.15.0 to avoid build issues
* `LMR` changes:
  * Fixes
    - Fix gNB ID encoding
    - Update LTTNG to v0.15.0 to avoid build issues
* `PCF` changes:
  * Features
    - PCF Provisioning API: Introduced support for provisioning Policy Decisions,
    PCC Rules, QoS Data, and Traffic Control Data
  * Fixes
    - HTTP/2 PUT request for each endpoint
    - LTTNG build issue
* `NSSF` changes:
  * Fixes
    - Update LTTNG to v0.15.0 to avoid build issues

## v2.1.0 -- August 2024 ##

* 1 new Network Funtion:
  * LMF
* Testing
  * Using a Robot Framework based test pipeline now
* Tutorials:
  - Remove ipv4 addresses from basic tutorial
  - Use correct SD values on DB, slicing and for VPP UPF
* Tech Debt for all Network Functions
  - Stopping support for RHEL8/Rocky8 in favor of RHEL9/Rocky9
  - HTTP client cpr library refactoring effort
  - Move SBI models to common src git submodule
* `AMF` changes:
  * Features
    - Adding NRPPA protocol support
    - Support Non UE N2 Info message
    - Support Multiple PDU sessions service request
    - Adding gNB statistics
    - Adding NGAP Utils
    - Adding LTTNg tracepoints for logging
    - Using hexadecimal values for SD in all APIs
    - Updating UE info statistics on AMF after service request
    - Exposing NCGI in UE Location Report notification
    - Use HTTP Request Timeout from conf file
  * Fixes
    - Fix issue for JSON iterator comparison
    - Fix multiple sessions response handling
    - Fix NF registration/deregistration when discovering NRFs from NSSF
    - Fix PDU session resource context request null pointer
    - Fix issue for retrieving GUTI from 5G-S-TMSI
    - Fix HTTP/2 server shutdown
    - Fix shutdown threads procedure
    - Fix UE Context Release procedure
    - Fix buffer-overflow issue
    - Fix AMF UE NGAP ID (uint64_t, 40 bits)
    - Fix Nas buffer allocation length
    - Fix issue for N2 handover
    - Fix GUTI decode
    - Fix NAS Decode: check buffer length before decoding
    - Fix issue for mobility registration update procedure
    - Fix HTTP client by using SBI task to send HTTP request
  * Tech Debt
    - Cleanup common utils
    - Move NAS to common src git submodule
    - Move NGAP to common src git submodule
    - Move conversions from AMF to common src git submodule
    - Separate all in one implementation
* `AUSF` changes:
  * Features
    - Add connection handling mechanism
    - Use HTTP Request Timeout parameter from Conf file
  * Fixes
    - Fix HTTP/2 server shutdown
    - Fix of the shutdown for the task manager
    - Fix issue for SD
  * Tech Debt
    - Remove NRF dependency from AUSF
    - Code refactor cleanup
    - Removing unneccessary packages from target images
    - Cleanup AUSF client
* `NRF` changes:
  * Features
    - Adding debug info
  * Fixes
    - Fix for Boost::signals2 issue
    - Fix exception handling
    - Fix HTTP/2 server shutdown
  * Tech Debt
    - Removing unneccessary packages from target images
* `NSSF` changes:
  * Fixes
    - Fix HTTP/2 server shutdown
* `PCF` changes:
  * Features
    - Add possibility to read QoS values from file
  * Fixes
    - Fix HTTP/2 server shutdown
    - Use new FlowDirection fix
  * Tech Debt
    - Resynch PCF with common source git-submodule and use utils from there
* `SMF` changes:
  * Features
    - Use HTTP Request Timeout parameter from Conf file
    - Support advanced `UpfInfo` from config file, allows to configure different UPF flavors without NRF
    - Resolve UPF from config file 10 times every 2 seconds, allowing flexibility in start order
  * Fixes
    - Fix multiple PDU session SEID handling
    - Fix issue for PDU session establishment
    - Fix: properly ending any thread and not generating seg fault when stopping smf process
    - Fix N1/N2 handling between AMF and SMF when gNB exits
    - Fix(handover): Check if N2 SM Info is set in HO Complete
    - Fix: smf expecting CreatedPDR in n4_session_establishment_response when UPF that does not support TEID Creation
    - Fix: NGAP S-AMBR encoding from bitrate string
    - Fix: Allow lower-case SD values and also allow 0xSD values in config
    - Fix HTTP/2 server shutdown
    - Fix error message upon PFCP session establishment request
    - Fix SMF crash on startup when peer UPF is not reachable
  * Tech Debt
    - Graph refactor, preparation for QoS handling
    - Resynch SMF with common source git-submodule and use utils from there
* `PCF` changes:
  * Features
    - Add possibility to read QoS values from file
  * Fixes
    - Fix HTTP/2 server shutdown
    - Use new FlowDirection fix
  * Tech Debt
    - Resynch PCF with common source git-submodule and use utils from there
* `UDM` changes:
  * Features
    - Update UDM APP structure
    - Use HTTP Request Timeout parameter from Conf file
  * Fixes
    - Fix HTTP/2 server shutdown
  * Tech Debt
    - Code cleanup
    - Removing unneccessary packages from target images
    - Cleanup UDM client and add connection handling mechanism
* `UDR` changes:
  * Features
    - Add NRF connection handling mechanism
    - Use HTTP Request Timeout parameter from Conf file
  * Fixes
    - Fix HTTP/2 server shutdown
    - Fix duplicated HTTP/1 route
    - Fix: remove PID section in main
  * Tech Debt
    - Remove NRF dependency from UDR
    - Code cleanup
* `UPF` changes:
  * Features
    - Add connection handling between UPF and NRF
    - Use HTTP Request Timeout parameter from Conf file
    - QoS initial support
    - N4 interoperability improved
    - Performance improvement: CPU usage is further reduced
  * Fixes
    - Fixes: thread management especially at shutdown.
    - Fix FDQN IPv4-only resolution
    - Fix Using SD in string hex in UPF profile to send to NRF
    - Fix to update TEID after a reconnection with FiveG_S_TMSI
  * Tech Debt
    - Remove NRF dependency from UPF
    - Bumping up libbpf and bpftool versions:
      - libbpf to `master` (currently above `v1.4.5`)
      - bpftool to `v7.3.0`
      - This should allow to build on newer systems

## v2.0.1 -- January 2024 ##

* `AMF` changes:
  * Features
    - NGAP AMF status indication
    - Add UE Retention Information support
    - Update NAS with Rel 16.14.0 IEs
      *  Refactoring code for Encode/Decode functions
      *  Cleanup NAS lib
  * Fixes
    - Fix typo for N1N2MessageSubscribe
    - Fix issue when receiving PDU session reject from SMF
  * Tech debt
    - Reformating of the SCTP code
    - Refactor promise handling
    - Removing dependencies to libconfig++ (Only YAML file can be read as configuration)
* `SMF` changes:
  * Features
    - Add N1/N2 info in the message response to AMF if available
  * Fixes
    - Remove NRF dependency from SMF
  * Tech debt
    - Refactor SMF PFCP associations to always use UPF info
* `UDM` changes:
  * Fixes
    - Remove NRF dependency from SMF
* `UDR` changes:
  * Tech debt
    - Fixed builds
    - Refactor mongoDB

## v2.0.0 -- December 2023 ##

* 2 new Network Functions:
  * NWDAF
  * UPF: we are obsoleting `openair-spgwu-tiny` in favor of 5G-only UPF implementation
    - It supports 2 implementations:
      * The `Simple-Switch` from `openair-spgwu-tiny`
      * An `eBPF`-based solution
* Tutorials:
  * All tutorials are now using `oai-upf` instead of `openair-spgwu-tiny`
  * New tutorials:
    - Mongo-DB for User Subscription management (instead of mysql) example
    - A traffic steering example
    - A traffic redirection example
    - UPF simple example using the eBPF implementation
    - NWDAF simple example
* Helm Charts:
  * All charts are now using `oai-upf` instead of `openair-spgwu-tiny`
  * Removed the use of `helm-spray`
  * Charts updated to latest YAML configuration scheme
* Common features/fixes for all Network Functions:
  * Support for a YAML-based configuration file
    - Make DNS configurable per DNN
    - Add CIDR DNN configuration
    - implement UpfInfo parsing for YAML config
* Tech Debt for all Network Functions:
  * Updated common models to 3GPP TS 29.571 Release 16.13.0 and moved them to the shared common submodule
  * Published images on Docker-Hub are using now Ubuntu-22 as base image
    - Ubuntu-18 is no longer supported
  * Switching to clang-format-12
* `AMF` changes:
  * Features
    - Service request handling
    - Update API Server name/structure
    - N2 info notify
    - Updated NGAP library to 38.413 V16.14.0
    - Location Report Notification for N2 Handover
    - LMF Determine Location & DownlinkUeAssociatedNrppaTranport support
  * Fixes
    - Fixed: Add NSSAI info in AMF profile to send to NRF
    - Fixed: Http1/2 - only spawning one HTTP server
    - Fixed: HTTP2 support for Configuration/Location-related APIs
    - Fixed: Display NRCellID in hex to associate between UE and gNB
    - Fixed: Use AMF ID as string to register to NRF
    - Added missing HTTP2 APIs for N1 Message Notify, N1N2MessageSubscribe/Unsubscribe, Status Notification
    - Free allocated memory in Destructor of NGAP msg instead of using Delete operator
    - Added retry mechanism for NF Registration/Update
    - Removed unnecessary config parameter: generate_random (database)
    - Fixed N1/N2 message unsubscribe API
    - Fixed issue when decoding PduSessionResourceSetupResponse
  * Tech debt
    - Code refactoring: ITTI between SBI and other tasks, NGAP IEs
    - Code cleanup: NAS IEs, N2, removed usused code, Used new instead of malloc/calloc for N2
* `NRF` changes:
  * Features
    - Added heartbeat parameter
  * Fixes
    - Returning only REGISTERED NFs from Search result
    - Removing suspended NFs after timeout
* `PCF` changes:
  * Features
    - Add support for traffic steering rules
    - Add support for redirection rules
  * Fixes
    - Handling boolean values in yaml parsing for policies
  * Tech debt
    - Updated PCF models to Release 16.17.0 and moved them to the shared common submodule
* `SMF` changes:
  * Features
    - Support getting SMF configuration with the new SMF configuration API
    - Handled traffic redirection PCF policy
    - Giving users possibility to configure SMF info themselves
    - Removed SBI DNS lookup upon start of SMF
    - De-register to NRF on exit
    - Enabled event exposure in HTTP/2 API server
  * Fixes
    - Fixed ULCL support in SM context update procedure
    - Fixed SEID assignment in N4 session establishment request
    - Fixed Service Request handling
    - Fixed YAML config issues
    - Fixed Handle IE Usage Report in session deletion response
    - Fixed SMF selection (NRF registration) when local subscription info is not used
  * Tech debt
    - Updated SMF-specific NRF models to Release 16.15.0 and moved them to the shared common submodule
    - Updated PCF models to Release 16.17.0 and moved them to the shared common submodule
* `UDM` changes:
  * Fixes
    - Fixed HTTP/2 issue for SDM sm-data API
* `UDR` changes:
  * Features
    - SessionManagementSubscriptionData GET ALL and DELETE apis
    - Session management subscription DATA PUT api new
    - UDR configuration APIs
    - Added support for MongoDB database choice
    - Added option to configure database port
  * Fixes
    - Fixed hardcoded HTTP/2 port
    - Added missing HTTP2 for Authentication Data and Session Management Subscription Data

## v1.5.1 -- May 2023 ##

* Tutorials:
  * All basic-based tutorials are now only in HTTP/2 mode and with NRF
    - All non-NRF basic deployments have been obsoleted
* Update the helm charts and helm chart tutorial
* Testing:
  * Load tester for 5000 PDU sessions
* Common features/fixes for all Network Functions:
  * Code Refactoring for:
    * Logging mechanism (runtime log level selection)
    * Installation / build scripts
    * Continuous Integration scripts
  * Published images on Docker-Hub is using now Ubuntu-20 as base image
    * We will soon obsolete the build system for Ubuntu18.04
* `AMF` changes:
  * Fix Service Request handling (Service Type: Signalling)
  * Fix N2 handover
  * Support usage of SUPI-type IMSI
  * Fix mapping between RAN UE NGAP ID and UE context
  * Fix SBI port for UDM in case of FQDN resolution
  * Fix TMSI handling
  * Fix PDU Session Ressource Release Response message
  * Fix issue for decoding MSIN with an odd number of digits
  * Fix usage of lower-case for DNN value (case insensitive)
  * Fix: NSSF port number was not read from config file
  * Code Refactoring for:
    * NAS layer
    * Registration Complete Message
    * UE context refactor
* `NRF` changes:
  * Tentative fix for a failed assertion of Boost signal
  * HTTP2 fix for json response data formatting
* `PCF` changes:
  * Add HTTP/2 support
* `SMF` changes:
  * Fix N1N2 Content message
  * Remove ranInfo field in n2infocontainer
  * Fix encoding NAS header
  * Resolved QoS Flow info missing in N2 Handover Preparation
  * Fix SUPI format: Use IMSI as SUPI
  * Fix: Send PDU Session Reject when PDU session fails before SMF procedure is started
  * Fix HTTP header
  * Fixing config parameter read
  * Fix for IE Redirect Information
  * Fix: Associate node id based on node id type
  * Use N3 ip address from NF profile if provided
  * Fix: UL TEID for multiple created PDR
  * Fix for encode/decode of create QER IE
  * Support for DL PDR in session establishment
  * Use NWI from config file when no UPF profile is associated
  * Fix HTTP/2 issue with PCF
* `UDM` changes:
  * HTTP2 Fix: Removed duplicate request handler
* `UDR` changes:
  * Fix PLMN ID for SessionManagementSubscriptionData (HTTP2)
  * logging: Add UE ID in the log
  * Retry NF Register if registration failed

## v1.5.0 -- January 2023 ##

* New tutorials:
  - UL CL with policies --> `docs/DEPLOY_SA5G_ULCL.md`
  - Testing with `OMEC-gnbsim` --> `docs/DEPLOY_SA5G_WITH_OMEC_GNBSIM.md`
  - SD-Fabric usage
* Update the helm charts and helm chart tutorial
* Switched tutorials to latest `mysql` version (`8.0`)
* Fixes in slicing tutorial to use latest OAI RAN images
* Common features/fixes for all Network Functions:
  - Proper exit on SIGTERM
  - jinja2-based configuration file
  - Ubuntu22 and cgroup2 support (even on `SPGWU-TINY`)
  - Giving some time for FQDN resolution
  - Release mode does not use libasan anymore
  - Health-checks are natively in the distributed images
* `AMF` changes:
  - Minimal fix for Decoding RegistrationRequest from COTS UE
  - Fix small issue for NGAP lib
  - NGAP IES code refactoring
  - Fix PDU session release
  - Refactor NGAP message callback
  - Fix nake ptr
  - Fix UL NAS transport
  - Fix typo for Rejected NSSAI
  - PDU session release supported
  - Update SST type (int instead of string) in conf file
  - Events exposure: location report with empty supi fixed
  - small fix for event exposure loss of connectivity
  - Minor fix for encoding no SD in PduSessionResourceSetupRequest
  - Fix SST/SD on cots ue
  - Docker images improvements
* `AUSF` changes:
  - Docker images improvements
* `NEF` changes:
  - Docker images improvements
* `NRF` changes:
  - Enhance UPF profile in NRF and fix bug in SBI when body is too long
  - Added Status change notification
  - Docker images improvements
* `NSSF` changes:
  - Docker images improvements
* `PCF` changes:
  - Initial release
  - NRF registration
  - Add Npcf_SMPolicyControl API Create, Update, Delete and Get procedures
  - Add file based policy provisioning
  - Add policy decision feature based on SUPI, DNN, Slice and default policy
* `SMF` changes:
  - Feature improvements:
    * PDU SESS EST + Qos Monitoring events exposure
    * PFCP: removing dependency to folly
    * Add IEs to support UE Rel 16
    * Added and integrated UPF graph instead of PFCP associations list
      * Supported scenarios:
        - I-UPF / A-UPF N9
        - UL CL
    * Implement Npcf_SMPolicyControl API client
    * Changing the configuration file to jinja2-based approach
      * At least one slice (slice #0) shall be completely defined
  - Fixes:
    * Fix openapi cause
    * Fix small issue for Mime parser for normal message
    * Fix Volume Threshold IE to PFCP Create URR IE
    * Fix mcc mnc 00 udr
    * Fix issues to work with Release-16 COTS UE
    * Fix issue when there's no valid reply from UPF for PDU session release
    * Fix Protocol identifier Selected Bearer Control Mode
    * Fix issue for Static UE IP Addr
    * Fix URR ID in IE Create URR (post UPF graph implementation)
    * Fix issue for Full DNN (APN Operator Identifier)
* `SPGWU-TINY` changes:
  - Docker images improvements
  - Ubuntu22 full support
* `UDM` changes:
  - Docker images improvements
* `UDR` changes:
  - Improve MySQL connection handling
  - Fix issue with DNNs including special characters
  - SessionManagementSubscriptionData POST API
  - Fix session management subscription data
  - Docker image improvements
* `UPF-VPP` changes:
  - Ubuntu22.04 support
  - SNSSAI fix
  - Support UL CL UPF deployment
  - Support I-UPF / A-UPF N9 UPF deployment
  - GTP payload length fix
  - Major Configuration update

## v1.4.0 -- July 2022 ##

* All official images produced by CI are pushed to `oaisoftwarealliance` Docker-Hub Team account
* New tutorial:
  - My5gRAN Tester --> `docs/DEPLOY_SA5G_WITH_My5g-RANTester.md`
* Update the helm charts and helm chart tutorial
* Reduce image size for all network functions
* New wiki page to know more about variable which can be configured for each network function
* Fix HTTP/2 support for all network functions `docker-compose/docker-compose-basic-nrf-httpv2.yaml`
* `AMF` Changes:
  - Fix SCTP NG Shutdown issue
  - Fix 100% CPU consumption issue
  - Fix RAN UE ID display
  - Fix issue for TMSI and GUTI value
  - Fix for handling S-NSSAI 
  - Remove OPC value from AMF configuration
  - Support for Ubuntu 20.04 bare-metal installation
* `AUSF` Changes:
  - Remove unused packages
  - HTTP/2 support for SBI interface
  - NRF Registration and heartbeat exchange
* `NRF` Changes:
  - Remove unused packages
  - Add NF profile handling for PCF
  - HTTP/2 support for SBI interface
* `NSSF` Changes:
  - Network slice selection for UE registration 
  - NS-AVAIBALITY API support to CREATE new slice
  - Fix bare-metal setup configuration management
  - HTTP/2 support for SBI interface
* `SMF` Changes:
  - Fix for handling S-NSSAI 
  - Add support for IMS
  - HTTP/2 support for SBI interface
  - Add usage report feature
  - Flexiable MTU
  - Support for Ubuntu 20.04 bare-metal installation
* `UDM` Changes:
  - Fix HTTP/2 support
  - NRF Registration and heartbeat exchange
* `UDR` Changes:
  - Fix sync failure issue
  - Fix issue to support Slice Selection Subscription Data retrieval
  - NRF Registration and heartbeat exchange
* `SPGWU-TINY` Changes:
  - Fix for handling S-NSSAI 
  - Add support for multiple slices via config file
  - Allowed reusing GTPv1-U socket
  - Fix GTPU offset sequence number
  - Fix configurable number of DL threads for data path
* `UPF-VPP` Changes:
  - Standalone support validated for traffic steering and redirection
  - Added instructions for bare-metal installation
  - Support for Ubuntu 20.04 bare-metal/docker installation
* `NEF` It is ongoing so far it is not functional

## v1.3.0 -- January 2022 ##

* Incorporation of new public network functions:
  - NSSF
* New tutorials:
  - Slicing --> `docs/DEPLOY_SA5G_SLICING.md`
  - Static UE IP address to emulate private network --> `docs/DEPLOY_SA5G_BASIC_STATIC_UE_IP.md`
* `AMF` Changes:
  - Periodic Registration Update
  - Support for Event Exposure (Registration State Report)
  - Implicit Deregistration Timer
  - Mobile Reachable Timer
  - Mobility Registration Update
  - NRF Selection (via NSSF)
  - Fix for validation of SMF Info
  - Fix RAN UE NGAP Id
  - Fix SMF Selection SD
  - Fix NSSAI mismatch
  - Fix Service Request
  - Fix HTTP2
  - Fix MCC such as 001
  - Docker optimization
* `AUSF` Changes:
  - HTTP2 Support
  - Docker optimization
* `NRF` Changes:
  - NF profile update
  - Docker optimization
* `NSSF` Changes:
  - Initial Public Release
  - Docker Optimization
* `SMF` Changes:
  - Update NWI from NF profile
  - Update SMF profile
  - Added retry for PFCP association request
  - More flexible DNN/IP ranges when deploying container
  - Fix retrieving the list of NWI
  - Fix entreprise IE decoding
  - Fix issue for UPF selection
  - Fix for IE Measurement Period
  - Docker optimization
* `UDM` Changes:
  - Experimental support for Event Exposure
  - Added HTTP2 support
  - Fix static addr allocation
  - Fix build issue
  - Docker build optimizations
* `UDR` Changes:
  - Added HTTP2 support
  - Fix build issue
  - Fix static addr allocation
  - Docker build optimizations
* `SPGWU-TINY` Changes:
  - Disable association request if NF registration is enabled
* `UPF-VPP` Changes:
  - Upgrade to UPG plugin stable/1.2
  - Build fixes
  - Deployment fixes (wait launch of NRF Client until VPP is getting ready)

## v1.2.1 -- October 2021 ##

* Incorporation of new public network functions:
  - UPF-VPP
* New tutorial with this new function
* `AMF` Changes:
  - Fix build issue
  - Tentative fix for ngKSI already in use
  - Initial implementation for Mobility registration update
* `AUSF` Changes:
  - Fix build issue
* `NRF` Changes:
  - Fix build issue
* `SMF` Changes:
  - Timers handling: T3591/T3952
  - Fix build issue
  - Fix UPF selection
* `UDM` Changes:
  - Fix build issue
* `UDR` Changes:
  - Fix build issue
* `SPGWU-TINY` Changes:
  - Fix build issue
  - Fix GTPU DL encapsulation: 8 extraneous bytes
* `UPF-VPP` Changes:
  - Initial Public Release
  - Full support for Ubuntu18 and RHEL7
  - CI Build support
  - Tutorial validated

## v1.2.0 -- September 2021 ##

* Incorporation of new public network functions:
  - AUSF
  - UDM
  - UDR
* New tutorials with these new functions
* CI improvements
* `AMF` Changes:
  - AUSF connection
  - Support PDU Session Resource Modify procedure
  - Support HTTP2
  - Support AMF Event Exposure Services
  - Fix NIA0, NEA2
  - Fix potential AMF crash with UE/NGAP/NAS context
  - Fix N2 Handover
  - Fix Paging procedures
* `AUSF` Changes:
  - Initial public release
  - NRF registration
    - with FQDN DNS resolution
  - Full support for Ubuntu18 and RHEL8
* `NRF` Changes:
  - Added AUSF, UDR, UDM profiles
  - Updated UPF profile
* `SMF` Changes:
  - Event Exposure implemented
  - UPF profile update
  - Support for URR query
  - Bug fixes
* `UDM` Changes:
  - Initial public release
  - NRF registration
    - with FQDN DNS resolution
  - Full support for Ubuntu18 and RHEL8
* `UDR` Changes:
  - Initial public release
  - NRF registration
    - with FQDN DNS resolution
  - Proper mySQL DB deployment management
  - Full support for Ubuntu18 and RHEL8
* `SPGWU-TINY` Changes:
  - Adding 5G features
    - HTTP2 support

## v1.1.0 -- July 2021 ##

* Improvements on Continuous Integration:
  - DsTester validation on Ubuntu18 docker deployment
  - DsTester validation on RHEL8 / OpenShift deployment
  - Some components (such as AMF/NRF) have bracket-testing at unit level
* A lot of tutorials have been added
* `AMF` Changes:
  - Session Release
  - NRF registration
    - with FQDN DNS resolution
  - Multiple PDU support
  - Bug fixes
  - Full support for Ubuntu18 and RHEL8
* `NRF` Changes:
  - FQDN DNS resolution
  - Bug fixes
  - Full support for Ubuntu18 and RHEL8
* `SMF` Changes:
  - PFCP Release 16 support
  - NRF registration
    - with FQDN DNS resolution
  - Support for multiple UPF instances
  - Dotted DNN support
  - Use (SST, SD) to get the subscription information
  - Bug fixes
  - Full support for Ubuntu18 and RHEL8
* `SPGWU-TINY` Changes:
  - Adding 5G features
    - NRF discovery and FQDN support

## v1.0.0 -- September 2020 ##

* Initial release

