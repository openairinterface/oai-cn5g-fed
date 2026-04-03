# SPDX-License-Identifier: LicenseRef-CSSL-1.0

# Here you can define the image and tags that are used for the tests
# skip whitespace to make sed-ing easier from CI
image_tags = {
    "mysql": "mysql:8.0",
    "oai-nrf": "oaisoftwarealliance/oai-nrf:develop",
    "oai-amf": "oaisoftwarealliance/oai-amf:develop",
    "oai-smf": "oaisoftwarealliance/oai-smf:develop",
    "oai-upf": "oaisoftwarealliance/oai-upf:develop",
    "oai-ausf": "oaisoftwarealliance/oai-ausf:develop",
    "oai-udm": "oaisoftwarealliance/oai-udm:develop",
    "oai-udr": "oaisoftwarealliance/oai-udr:develop",
    "oai-nssf": "oaisoftwarealliance/oai-nssf:develop",
    "oai-pcf": "oaisoftwarealliance/oai-pcf:develop",
    "vpp-upf": "oaisoftwarealliance/oai-upf-vpp:develop",
    "ngap-tester": "ngap-tester:develop",
    "gnbsim": "gnbsim:latest",
    "oai-gnb": "oaisoftwarealliance/oai-gnb:2025.w46",
    "oai-nr-ue": "oaisoftwarealliance/oai-nr-ue:2025.w46",
    "mobsim": "carot0/mobsim:latest"
}
