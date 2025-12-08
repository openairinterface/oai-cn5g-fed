"""
Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
contributor license agreements.  See the NOTICE file distributed with
this work for additional information regarding copyright ownership.
The OpenAirInterface Software Alliance licenses this file to You under
the OAI Public License, Version 1.1  (the "License"); you may not use this file
except in compliance with the License.
You may obtain a copy of the License at

  http://www.openairinterface.org/?page_id=698

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
------------------------------------------------------------------------------
For more information about the OpenAirInterface (OAI) Software Alliance:
  contact@openairinterface.org
---------------------------------------------------------------------
"""

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
