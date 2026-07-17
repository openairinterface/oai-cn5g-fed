<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<h1 align="center">
    <a href="https://openairinterface.org/"><img src="https://openairinterface.org/wp-content/uploads/2015/06/cropped-oai_final_logo.png" alt="OAI" width="550"></a>
</h1>

<p align="center">
    <a href="https://openairinterface.org/oai-cssl/"><img src="https://img.shields.io/badge/license-OAI--CSSL--v1.0-blue" alt="License"></a>
    <a href="https://github.com/openairinterface/oai-cn5g-upf-vpp/-/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="License "></a>
    <a href="https://github.com/openairinterface/oai-cn5g-fed/tags">
      <img alt="Latest Git tag" src="https://img.shields.io/github/v/tag/openairinterface/oai-cn5g-fed?sort=semver">
    </a>
    <a href="https://releases.ubuntu.com/20.04/"><img src="https://img.shields.io/badge/OS-Ubuntu20-Green" alt="Supported OS"></a>
    <a href="https://releases.ubuntu.com/22.04/"><img src="https://img.shields.io/badge/OS-Ubuntu22-Green" alt="Supported OS"></a>
    <a href="https://www.redhat.com/en/enterprise-linux-9"><img src="https://img.shields.io/badge/OS-RHEL9-Green" alt="Supported OS"></a>
</p>

<p align="center">
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-amf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-amf?label=amf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-ausf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-ausf?label=ausf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-lmf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-lmf?label=lmf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-nef"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-nef?label=nef%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-nrf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-nrf?label=nrf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-nssf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-nssf?label=nssf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-pcf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-pcf?label=pcf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-smf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-smf?label=smf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-udm"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-udm?label=udm%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-udr"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-udr?label=udr%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-upf"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-upf?label=upf%20docker%20pulls"></a>
  <a href="https://hub.docker.com/r/oaisoftwarealliance/oai-upf-vpp"><img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/oaisoftwarealliance/oai-upf-vpp?label=upf-vpp%20docker%20pulls"></a>
</p>

<h2 align="center">
 OPENAIR-CN-5G: An implementation of the 5G Core network by the OpenAirInterface community.
</h2>

`OPENAIR-CN-5G` is an implementation of the 3GPP specifications for the 5G Core Network.
At the moment, it contains the following network elements:

* Access and Mobility Management Function (**[AMF](https://github.com/openairinterface/oai-cn5g-amf)**)
* Authentication Server Management Function (**[AUSF](https://github.com/openairinterface/oai-cn5g-ausf)**)
* Location Management Function (**[LMF](https://github.com/openairinterface/oai-cn5g-lmf)**)
* Network Exposure Function (**[NEF](https://github.com/openairinterface/oai-cn5g-nef)**)
* Network Repository Function (**[NRF](https://github.com/openairinterface/oai-cn5g-nrf)**)
* Network Slicing Selection Function (**[NSSF](https://github.com/openairinterface/oai-cn5g-nssf)**)
* Network Data Analytics Function (**[NWDAF](https://github.com/openairinterface/oai-cn5g-nwdaf)**)
* Policy Control Function (**[PCF](https://github.com/openairinterface/oai-cn5g-pcf)**)
* Session Management Function (**[SMF](https://github.com/openairinterface/oai-cn5g-smf)**)
* Unified Data Management (**[UDM](https://github.com/openairinterface/oai-cn5g-udm)**)
* Unified Data Repository (**[UDR](https://github.com/openairinterface/oai-cn5g-udr)**)
* User Plane Function (**UPF**) with 2 variants:
  * Simple Implementation (with a eBPF option) (**[UPF](https://github.com/openairinterface/oai-cn5g-upf)**)
  * Legacy VPP-Based Implementation (no longer maintained) (**[UPF-VPP](https://github.com/openairinterface/oai-cn5g-upf-vpp)**)
* Unstructured Data Storage Function (**UDSF**)

Each has its own repository. Some of these repositories are still private, soon to be released.

This repository is a **Federation of the OpenAir CN 5G repositories**.

It provides the shared Continuous Integration (CI) infrastructure used across the OpenAir Core Network 5G repositories
and hosts common documentation and tutorials. See the [documentation](docs/DEPLOY_HOME.md) to get started.

The build status of OAI Core Network Functions is available on the
[OAI Jenkins dashboard](https://jenkins-oai.eurecom.fr/view/5G%20Core%20Network%20GitHub/).

## Feature Set

Feature set of all the network functions is [here](./FEATURE_SET.md)

## License info

The source code is distributed under `Collaborative Standards Software License v1.0 (CSSL v1.0)`.
For more details, visit the [OAI Website](https://openairinterface.org/oai-cssl/).

The full text of `Collaborative Standards Software License v1.0` is also included in the [LICENSE](LICENSE)
file at the root of this repository.

Certain files in the repository are using MIT License and documentation is distributed under
Creative Commons Attribution 4.0 International license.

For third-party softwares, please refer to the [NOTICE](NOTICE) file.

Note that the `UPF-VPP` implementation is distributed under `Apache V2.0 License`.

See [Apache Website for more details](http://www.apache.org/licenses/LICENSE-2.0).

## Collaborative Development

This source code is hosted and maintained on GitHub, enabling collaborative development and contribution:

* Repository: [https://github.com/openairinterface/oai-cn5g-fed](https://github.com/openairinterface/oai-cn5g-fed)

Contribution guidelines and development workflows are described in the [CONTRIBUTING](CONTRIBUTING.md) file.

For information about supported features and capabilities, see the [Feature Set](docs/FEATURE_SET.md).

## Contribution Requests

Anyone is welcome to contribute to any part of the codebase and any network component.

Contributions can include bug fixes, suggestions, design and architecture improvements, as well as feedback on coding and implementation.

## Release Notes

They are available on the [CHANGELOG](CHANGELOG.md) file.

