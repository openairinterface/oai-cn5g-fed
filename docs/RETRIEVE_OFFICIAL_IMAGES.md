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

The official OAI CN5G container images use Ubuntu 22.04 as the container base image. They are compatible with Ubuntu hosts 22.04 through 26.04, Fedora 39 through 43, and RHEL 8 through 10.

Any Docker or Podman version available for those host releases should be fine. The examples below use Docker; Podman users can replace `docker` with `podman`.

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

  - We will keep pushing to the `latest` tag for the network functions when a milestone is reached. Currently, the `latest` tag corresponds to `v2.2.1` release.
  - We are making pushes on the `develop` tag whenever a contribution has been accepted. These images are **EXPERIMENTAL**.
  - Release tag `vx.x.x` contains the release code

Now pull images according to your requirement,

```bash
#!/bin/bash
docker pull oaisoftwarealliance/oai-amf:v2.2.1
docker pull oaisoftwarealliance/oai-nrf:v2.2.1
docker pull oaisoftwarealliance/oai-upf:v2.2.1
docker pull oaisoftwarealliance/oai-smf:v2.2.1
docker pull oaisoftwarealliance/oai-udr:v2.2.1
docker pull oaisoftwarealliance/oai-udm:v2.2.1
docker pull oaisoftwarealliance/oai-ausf:v2.2.1
docker pull oaisoftwarealliance/oai-upf-vpp:v2.2.1
docker pull oaisoftwarealliance/oai-nssf:v2.2.1
docker pull oaisoftwarealliance/oai-pcf:v2.2.1
docker pull oaisoftwarealliance/oai-lmf:v2.2.1
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
| FED REPO    | N/A         | `v2.2.1` | N/A                 |
| AMF         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| SMF         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| NRF         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| UPF         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| UDR         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| UDM         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| AUSF        | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| UPF-VPP     | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| NSSF        | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| LMF         | `develop`    | `v2.2.1` | Ubuntu 22.04        |
| PCF         | `develop`    | `v2.2.1` | Ubuntu 22.04        |

```bash
# Clone directly on the latest release tag
$ git clone --branch v2.2.1 https://github.com/openairinterface/oai-cn5g-fed.git
$ cd oai-cn5g-fed
# If you forgot to clone directly to the latest release tag
$ git checkout -f v2.2.1

# Synchronize all the network functions
# By default, the script synchronizes on develop branch
$ ./scripts/syncComponents.sh --branch v2.2.1
---------------------------------------------------------
Common branch (unless overridden) : v2.2.1
Components synchronized into      : component/
OAI-CN5G-PCF     component branch : v2.2.1
OAI-CN5G-NRF     component branch : v2.2.1
OAI-CN5G-SMF     component branch : v2.2.1
OAI-CN5G-UPF     component branch : v2.2.1
OAI-CN5G-NSSF    component branch : v2.2.1
OAI-CN5G-LMF     component branch : v2.2.1
OAI-CN5G-AMF     component branch : v2.2.1
OAI-CN5G-NEF     component branch : v2.2.1
OAI-CN5G-UDM     component branch : v2.2.1
OAI-CN5G-UDR     component branch : v2.2.1
OAI-CN5G-AUSF    component branch : v2.2.1
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
