<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">OpenAirInterface 5G Core Network Deployment : Pulling Container Images</font></b>
    </td>
  </tr>
</table>

# Retrieve Official Images

The official OAI CN5G container images are built on Ubuntu 24.04. The source code builds on Ubuntu 24.04 and CentOS Stream 10.

Any Docker or Podman version available for those releases should be fine. The examples below use Docker; Podman users can replace `docker` with `podman`.

If you want to use a specific branch or commit instead of an official image tag, refer to [Build your own images](./BUILD_IMAGES.md).

# Pulling Images From Docker Hub #

The images are hosted under the oai account `oaisoftwarealliance`.

Once again you may need to log on [docker-hub](https://hub.docker.com/) if your organization has the reached pulling limit as `anonymous`.

```bash
$ docker login
Login with your Docker ID to push and pull images from Docker Hub. If you don't have a Docker ID, head over to https://hub.docker.com to create one.
Username:
Password:
```

The OAI CI/CD team has automated more frequent pushes to Docker-Hub on `oaisoftwarealliance` account. Two important things to be noted:

  - We will keep pushing to the `latest` tag for the network functions when a milestone is reached. Currently, the `latest` tag corresponds to `v3.0.0` release.
  - We are making pushes on the `develop` tag whenever a contribution has been accepted. These images are **EXPERIMENTAL**.
  - Release tag `vx.x.x` contains the release code

Now pull images according to your requirement,

```bash
#!/bin/bash
docker pull oaisoftwarealliance/oai-amf:v3.0.0
docker pull oaisoftwarealliance/oai-nrf:v3.0.0
docker pull oaisoftwarealliance/oai-upf:v3.0.0
docker pull oaisoftwarealliance/oai-smf:v3.0.0
docker pull oaisoftwarealliance/oai-udr:v3.0.0
docker pull oaisoftwarealliance/oai-udm:v3.0.0
docker pull oaisoftwarealliance/oai-ausf:v3.0.0
docker pull oaisoftwarealliance/oai-upf-vpp:v3.0.0
docker pull oaisoftwarealliance/oai-nssf:v3.0.0
docker pull oaisoftwarealliance/oai-pcf:v3.0.0
docker pull oaisoftwarealliance/oai-lmf:v3.0.0
# Utility image to generate traffic
docker pull oaisoftwarealliance/trf-gen-cn5g:latest
```

Finally you may logoff --> your token is stored in plain text..

```bash
$ docker logout
```

We will push new versions when new features are validated.

# Synchronizing The Tutorials #

**CAUTION: PLEASE READ THIS SECTION VERY CAREFULLY!**

This repository only has tutorials and Continuous Integration scripts.

| CNF Name    | Branch Name | Tag      | Official image base |
| ----------- | ----------- | -------- | ------------------- |
| FED REPO    | N/A         | `v3.0.0` | N/A                 |
| AMF         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| SMF         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| NRF         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| UPF         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| UDR         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| UDM         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| AUSF        | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| UPF-VPP     | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| NSSF        | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| LMF         | `develop`    | `v3.0.0` | Ubuntu 24.04        |
| PCF         | `develop`    | `v3.0.0` | Ubuntu 24.04        |

```bash
# Clone directly on the latest release tag
$ git clone --branch v3.0.0 https://github.com/openairinterface/oai-cn5g-fed.git
$ cd oai-cn5g-fed
# If you forgot to clone directly to the latest release tag
$ git checkout -f v3.0.0

# Synchronize all the network functions
# By default, the script synchronizes on develop branch
$ ./scripts/syncComponents.sh --branch v3.0.0
---------------------------------------------------------
Common branch (unless overridden) : v3.0.0
Components synchronized into      : component/
OAI-CN5G-PCF     component branch : v3.0.0
OAI-CN5G-NRF     component branch : v3.0.0
OAI-CN5G-SMF     component branch : v3.0.0
OAI-CN5G-UPF     component branch : v3.0.0
OAI-CN5G-NSSF    component branch : v3.0.0
OAI-CN5G-LMF     component branch : v3.0.0
OAI-CN5G-AMF     component branch : v3.0.0
OAI-CN5G-NEF     component branch : v3.0.0
OAI-CN5G-UDM     component branch : v3.0.0
OAI-CN5G-UDR     component branch : v3.0.0
OAI-CN5G-AUSF    component branch : v3.0.0
---------------------------------------------------------
```

## If you are using the `develop` images ##

If you want to pull the `develop` tags of the published images:

```bash
#!/bin/bash
docker pull oaisoftwarealliance/oai-amf:develop
docker pull oaisoftwarealliance/oai-nrf:develop
docker pull oaisoftwarealliance/oai-upf:develop
docker pull oaisoftwarealliance/oai-smf:develop
docker pull oaisoftwarealliance/oai-udr:develop
docker pull oaisoftwarealliance/oai-udm:develop
docker pull oaisoftwarealliance/oai-ausf:develop
docker pull oaisoftwarealliance/oai-upf-vpp:develop
docker pull oaisoftwarealliance/oai-nssf:develop
docker pull oaisoftwarealliance/oai-pcf:develop
docker pull oaisoftwarealliance/oai-nef:develop
docker pull oaisoftwarealliance/oai-lmf:develop
# Utility image to generate traffic
docker pull oaisoftwarealliance/trf-gen-cn5g:latest
```

```bash
# Clone directly on the latest release tag
$ git clone --branch develop https://github.com/openairinterface/oai-cn5g-fed.git
$ cd oai-cn5g-fed
# If you forgot to clone directly to the latest release tag
$ git checkout -f develop
$ git rebase origin/develop
```

You are ready to [Configure the Containers](./CONFIGURATION.md).

You can also go [back](./DEPLOY_HOME.md) to the list of tutorials.
