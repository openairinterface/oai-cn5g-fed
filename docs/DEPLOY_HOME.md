<a href="https://openairinterface.org/">
    <img src="./images/oai_final_logo.png" alt="Openairinterface logo" title="Openairinterface" align="right" height="60" />
</a>

# OpenAirInterface 5G Core Network Deployment

Welcome to the tutorial home page of the OAI 5g Core project. Here you can find lots of tutorials and help manuals. We regularly update these documents depending on the new feature set.

## Table of contents

- [List of COTS UEs tested with OAI](./LIST_OF_TESTED_COTSUE.md)
- [Pre-requisites](./DEPLOY_PRE_REQUISITES.md)
- How to get the container images
    - [Pull the container images](./RETRIEVE_OFFICIAL_IMAGES.md)
    - [Build the container images](./BUILD_IMAGES.md)
- [Configuring the Containers](./CONFIGURATION.md)
    - [How to use PCF Provisioning API](./PCF_PROVISIONING_API.md)
- 5G Core Network Deployment
    - [Using Docker-Compose, perform a `basic` deployment](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md)
    - [Using Docker-Compose, perform a `basic` deployment with `eBPF` implementation of UPF](./DEPLOY_SA5G_WITH_UPF_EBPF.md)
    - [Using Docker-Compose, perform a `basic-vpp` deployment with `VPP` implementation of UPF](./DEPLOY_SA5G_WITH_VPP_UPF.md)
    - [Using Docker-Compose, perform a `basic` deployment with `SD-Fabric` implementation of UPF](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-upf-sdfabric/-/wikis/Deployment-using-Docker)
    - [Using Docker-Compose, perform a `basic` deployment with Static UE IP address allocation](./DEPLOY_SA5G_BASIC_STATIC_UE_IP.md)
    - [Using Helm Chart](https://gitlab.eurecom.fr/oai/orchestration/charts/-/tree/develop)
    - [Using Docker-Compose, doing network slicing](./DEPLOY_SA5G_SLICING.md)
- 5G Core Network Deployment and Testing with Ran Emulators
    - [Using Docker-Compose, perform a `basic` deployment and test with `OAI RF simulator`](https://gitlab.eurecom.fr/oai/openairinterface5g/-/tree/develop/ci-scripts/yaml_files/5g_rfsimulator)
    - [Using Docker-Compose, perform a `minimalist` deployment and test with `gnbsim`](./DEPLOY_SA5G_MINI_WITH_GNBSIM.md)
    - [Using Docker-Compose, perform a `basic` deployment and test with `UERANSIM`](./DEPLOY_SA5G_WITH_UERANSIM.md)
    - [Using Docker-Compose, perform a `basic` deployment and test with `My5g-RANTester`](./DEPLOY_SA5G_WITH_My5g-RANTester.md)
    - [Using Docker-Compose, perform a `basic` deployment and test with `omec-gnbsim`](./DEPLOY_SA5G_WITH_OMEC_GNBSIM.md)
    - [Using Docker-Compose, when testing with Commercial UE, troubleshoot traffic issues](./TROUBLESHOOT_COTS_UE_TRAFFIC.md)
    - [Using Docker-Compose, perform a `basic` Traffic Redirection deployment and test with `gnbsim`](./DEPLOY_SA5G_REDIRECTION.md)
    - [Using Docker-Compose, perform a `basic` Traffic Steering deployment and test with `gnbsim`](./DEPLOY_SA5G_STEERING.md)
    - [Using Docker-Compose, perform a `basic` UL/CL deployment and test with `gnbsim`](./DEPLOY_SA5G_ULCL.md)
    - [Using Docker-Compose, test the  5G Network Data Analytics Function](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-nwdaf/-/blob/master/docs/TUTORIAL.md)
- Connecting a real RAN to OAI 5G Core Network
    - [Network Considerations](./NETWORK_CONSIDERATIONS.md)
- The Developers Corner
    - [How to Deploy Developers Core Network and Basic Debugging](./DEBUG_5G_CORE.md)
    - [Advance Deployment of OAI 5G Core](./ADVANCE_DEPLOYMENT.md)
    - [Using Virtual Machine, deploy and test with a Commercial UE](./DEPLOY_SA5G_VM_COTSUE.md)
- [Report an Issue or bug for Core Network Functions](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md#8-report-an-issue)
