# OpenAirInterface CN5G


## License

This project is distributed under the **OAI Public License V1.1**.  
For more details, please refer to the [OAI Website](https://openairinterface.org/legal/oai-license-model/).


---

## 5G CN Implementation by OAI Community

`OPENAIR-CN-5G`, an implementation of the 3GPP specifications for the 5G Core Network (CN) currently includes the following network functions, each maintained in its own repository:

* **Access and Mobility Management Function (AMF)** – [oai-cn5g-amf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf)
* **Authentication Server Function (AUSF)** – [oai-cn5g-ausf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-ausf)
* **Location Management Function (LMF)** – [oai-cn5g-lmf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-lmf)
* **Network Exposure Function (NEF)** – [oai-cn5g-nef](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nef)
* **Network Repository Function (NRF)** – [oai-cn5g-nrf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nrf)
* **Network Slicing Selection Function (NSSF)** – [oai-cn5g-nssf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nssf)
* **Policy Control Function (PCF)** – [oai-cn5g-pcf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-pcf)
* **Session Management Function (SMF)** – [oai-cn5g-smf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-smf)
* **Unified Data Management (UDM)** – [oai-cn5g-udm](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udm)
* **Unified Data Repository (UDR)** – [oai-cn5g-udr](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udr)
* **User Plane Function (UPF)** with two variants:
    * Simple implementation (with eBPF option) – [oai-cn5g-upf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf)
    * VPP-based implementation – [oai-cn5g-upf-vpp](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf-vpp)
* **Unstructured Data Storage Function (UDSF)** – [oai-cn5g-udsf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-udsf)
* **Network Data Analytics Function (NWDAF)** – [oai-cn5g-nwdaf](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nwdaf)


> Note: Some repositories are currently private but will be released soon.

Any merge request or push to the `develop` branch in a network function repository (e.g., `oai-cn5g-amf`) automatically triggers the CI pipeline via GitLab webhooks.

View the pipeline status here: [OAI 5G Core Network Jenkins](https://jenkins-oai.eurecom.fr/view/5G%20Core%20Network/)


---