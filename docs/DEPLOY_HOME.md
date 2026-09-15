<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<a href="https://openairinterface.org/">
    <img src="./images/oai_final_logo.png" alt="Openairinterface logo" title="Openairinterface" align="right" height="60" />
</a>

[[_TOC_]]

# OpenAirInterface 5G Core Network Deployment

This page is the starting point for OAI 5G Core deployment tutorials. If this is your first time with the project, follow the quick-start path below before moving to feature-specific guides.

## Supported Distributions

The official OAI CN5G container images are built on Ubuntu 24.04. The source code builds on the following Linux distributions:

| Distribution  | Supported versions |
| ------------- | ------------------ |
| Ubuntu        | 24.04              |
| CentOS Stream | 10                 |

Any Docker or Podman version available for those releases should be fine. The tutorials use Docker command names in most examples; when using Podman, replace `docker` with `podman` and use your distribution's Compose-compatible command where needed.

## First Deployment

1. Prepare the host with the [deployment pre-requisites](./DEPLOY_PRE_REQUISITES.md).
2. Run the basic [Docker Compose deployment with Duranta/OAI RAN and UE](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md).

## Choose A Tutorial

| Goal | Start here |
| ---- | ---------- |
| Learn the Docker Compose deployment, static UE IP allocation, and OAI RF simulator test | [Basic deployment](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md) |
| Run a compact end-to-end core plus RAN test | [Mini deployment with gnbsim](./DEPLOY_SA5G_MINI_WITH_GNBSIM.md) |
| Test with UERANSIM | [Deployment with UERANSIM](./DEPLOY_SA5G_WITH_UERANSIM.md) |
| Test with OMEC Gnbsim | [Deployment with OMEC gnbsim](./DEPLOY_SA5G_WITH_OMEC_GNBSIM.md) |
| Use the eBPF UPF | [Deployment with UPF eBPF](./DEPLOY_SA5G_WITH_UPF_EBPF.md) |
| Use the legacy VPP UPF | [Deployment with UPF-VPP](./DEPLOY_SA5G_WITH_VPP_UPF.md) |
| Use MongoDB instead of MySQL | [MongoDB deployment](./DEPLOY_SA5G_BASIC_MONGODB.md) |
| Configure QoS policies | [QoS tutorial](./DEPLOY_SA5G_WITH_QOS.md) |
| Configure Ethernet PDU sessions | [Ethernet PDU sessions](./Ethernet_PDU_Sessions.md) |
| Configure slicing | [Network slicing tutorial](./DEPLOY_SA5G_SLICING.md) |
| Configure traffic redirection | [Traffic redirection tutorial](./DEPLOY_SA5G_REDIRECTION.md) |
| Configure traffic steering | [Traffic steering tutorial](./DEPLOY_SA5G_STEERING.md) |
| Configure UL CL | [UL CL tutorial](./DEPLOY_SA5G_ULCL.md) |
| Deploy with Helm charts | [OpenAirInterface orchestration repository](https://github.com/openairinterface/orchestration/tree/main) |

## Reference Guides

- [Configuration reference](./CONFIGURATION.md)
- [PCF provisioning API](./PCF_PROVISIONING_API.md)
- [Network considerations for real RAN connections](./NETWORK_CONSIDERATIONS.md)
- [List of tested COTS UEs](./LIST_OF_TESTED_COTSUE.md)
- [Retrieve official images](./RETRIEVE_OFFICIAL_IMAGES.md)
- [Build images](./BUILD_IMAGES.md)

## Developer Guides

- [Debug 5G Core network functions](./DEBUG_5G_CORE.md)

## Support

- [Report an issue or bug for Core Network Functions](./DEPLOY_SA5G_BASIC_DEPLOYMENT.md#8-report-an-issue)
