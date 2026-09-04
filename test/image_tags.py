# SPDX-License-Identifier: LicenseRef-CSSL-1.0

# Here you can define the image and tags that are used for the tests
# skip whitespace to make sed-ing easier from CI
image_tags = {
    "mysql": "mysql:9.6",
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
    "gnbsim": "gnbsim:latest",
    "omec-gnbsim": "oaisoftwarealliance/omec-gnbsim:v2.3-fixes",
    "packetrusher": "oaisoftwarealliance/packet-rusher:fix-5gstmsi-amf",
    "oai-gnb": "oaisoftwarealliance/oai-gnb:develop",
    "oai-nr-ue": "oaisoftwarealliance/oai-nr-ue:develop",
    "mobsim": "carot0/mobsim:latest"
}
