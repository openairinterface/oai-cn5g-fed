# OpenAirInterface 5G Core Network Deployment

Welcome to the tutorial home page of the OAI 5g Core project. Here you can find lots of tutorials and help manuals. We regularly update these documents depending on the new feature set.

## Quick Start & Tutorials

- [List of COTS UEs tested with OAI](../List-of-Tested-COTSUE.md)
- [Pre-requisites](Prerequisites.md)
- How to get the container images
    - [Pull the container images](Retrieve-Official-Images.md)
    - [Build the container images](Build-Images.md)
- [Configuring the Containers](Configuration.md)
    - [How to use PCF Provisionning API](PCF-Provisioning-API.md)
- 5G Core Network Deployment
    - [Using Docker-Compose, perform a `basic` deployment](Basic_Deployment.md)
    - [Using Docker-Compose, perform a `basic` deployment with `eBPF` implementation of UPF](UPF_EBPF.md)
    - [Using Docker-Compose, perform a `basic-vpp` deployment with `VPP` implementation of UPF](UPF_VPP.md)
    - [Using Docker-Compose, perform a `basic` deployment with `SD-Fabric` implementation of UPF](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf-sdfabric/-/wikis/Deployment-using-Docker)
    - [Using Docker-Compose, perform a `basic` deployment with Static UE IP address allocation](Static_UE_IP.md)
    - [Using Helm Chart, perform a `basic` deployment](Helm_Charts.md)
    - [Using Docker-Compose, doing network slicing](Advance_Slicing.md)
- 5G Core Network Deployment and Testing with Ran Emulators
    - [Using Docker-Compose, perform a `basic` deployment and test with `OAI RF simulator`](https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/ci-scripts/yaml_files/5g_rfsimulator)
    - [Using Docker-Compose, perform a `minimalist` deployment and test with `gnbsim`](Mini_Deployment.md)
    - [Using Docker-Compose, perform a `basic` deployment and test with `UERANSIM`](UERANSIM.md)
    - [Using Docker-Compose, perform a `basic` deployment and test with `My5g-RANTester`](My5g_RANTester.md)
    - [Using Docker-Compose, perform a `basic` deployment and test with `omec-gnbsim`](Omec_gNBSIM.md)
    - [Using Docker-Compose, when testing with Commercial UE, troubleshoot traffic issues](Troubleshoot-COTS-UE-Traffic.md)
    - [Using Docker-Compose, perform a `basic` Traffic Redirection deployment and test with `gnbsim`](Traffic_Redirection.md)
    - [Using Docker-Compose, perform a `basic` Traffic Steering deployment and test with `gnbsim`](Traffic_Steering.md)
    - [Using Docker-Compose, perform a `basic` UL/CL deployment and test with `gnbsim`](ULCL.md)
    - [Using Docker-Compose, test the  5G Network Data Analytics Function](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nwdaf/-/blob/master/docs/TUTORIAL.md)
- Connecting a real RAN to OAI 5G Core Network
    - [Network Considerations](Network-Considerations.md)
- The Developers Corner
    - [How to Deploy Developers Core Network and Basic Debugging](Debug-5G-Core.md)
    - [Advance Deployment of OAI 5G Core](Advance_Deployment.md)
- [Report an Issue or bug for Core Network Functions](Basic_Deployment.md#8-report-an-issue)
