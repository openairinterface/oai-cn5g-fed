# OpenAirInterface 5G Core Network Deployment : Building Container Images

## 1.  Retrieve the correct network function branches

**CAUTION: PLEASE READ THIS SECTION VERY CAREFULLY!**

This repository only has tutorials and Continuous Integration scripts.

Each 5G Network Function source code is managed in its own repository.

They are named as `git sub-modules` in the `component` folder.

Before doing anything, you SHALL retrieve the code for each git sub-module.

**CAUTION: Starting from v1.5.1, we did a refactoring effort on source files, build scripts and CI scripts. So now there are a lot of nested git submodules.**

Normally the `./scripts/syncComponents.sh` should help synchronize all of them.

Now if you have non-tracked files or modified files within git submodules, this script may not work. 

Use the `--verbose` option to see the execution of each command.

If the synchronization fails, you may need to go into the path of the failing git-submodule(s) and clean the workspace from non-tracked/modified files. And then execute the `./scripts/syncComponents.sh` script again.

The 2 most important commands to know are :

1. `git submodule deinit --force .`
2. `git submodule update --init --recursive`

You can execute them at this federation level or at the nf component level.

### 1.1. You are interested in a stable version.

We recommend to synchronize with the master branches on all git sub-modules.

We also recommend that you synchronize this "tutorial" repository with a provided tag. By doing so, the `docker-compose` files will be aligned with feature sets of each cNF.

**At the time of writing (2024/08/30), the release tag was `v2.1.0`.**


| CNF Name    | Branch Name | Tag      | Ubuntu 22.04 | RHEL9 (UBI9)    |
| ----------- | ----------- | -------- | ------------ | ----------------|
| FED REPO    | N/A         | `v2.1.0` |              |                 |
| AMF         | `master`    | `v2.1.0` | X            | X               |
| SMF         | `master`    | `v2.1.0` | X            | X               |
| NRF         | `master`    | `v2.1.0` | X            | X               |
| UPF         | `master`    | `v2.1.0` | X            | X               |
| UDR         | `master`    | `v2.1.0` | X            | X               |
| UDM         | `master`    | `v2.1.0` | X            | X               |
| AUSF        | `master`    | `v2.1.0` | X            | X               |
| UPF-VPP     | `master`    | `v2.1.0` | X            | X               |
| NSSF        | `master`    | `v2.1.0` | X            | X               |
| PCF         | `master`    | `v2.1.0` | X            | X               |
| LMF         | `master`    | `v2.1.0` | X            | X               |


```bash
# Clone directly on the v2.1.0 release tag
$ git clone --branch v2.1.0 https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git
$ cd oai-cn5g-fed
# If you forgot to clone directly to the v2.1.0 release tag
$ git checkout -f v2.1.0

# Synchronize all git submodules
$ ./scripts/syncComponents.sh
---------------------------------------------------------
OAI-NRF     component branch : master
OAI-AMF     component branch : master
OAI-SMF     component branch : master
OAI-UPF     component branch : master
OAI-AUSF    component branch : master
OAI-UDM     component branch : master
OAI-UDR     component branch : master
OAI-UPF-VPP component branch : master
OAI-NSSF    component branch : master
OAI-NEF     component branch : master
OAI-PCF     component branch : master
OAI-LMF     component branch : master
---------------------------------------------------------
git submodule deinit --all --force
git submodule init
git submodule update --init --recursive
```

### 1.2. You are interested in the latest features.

All the latest features are pushed to the `develop` branches of each NF repository.

It means that we/you are able to build and the Continuous Integration test suite makes sure it
does NOT break any existing tested feature.

So for example, at time of writing, N2 Handover support code is included in `v1.1.0` release.
But it is not tested yet. So it is not advertised in the `CHANGELOG.md` and the Release Notes.

Anyhow, the tutorials' docker-compose files on the latest commit of the `develop` branch of
`oai-cn5g-fed` repository SHALL support any additional un-tested feature.

```bash
# Clone
$ git clone  https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git
$ cd oai-cn5g-fed
# On an existing repository, resync to the last `develop` commit
$ git fetch --prune
$ git checkout develop
$ git rebase origin/develop

# Synchronize all git submodules
$ ./scripts/syncComponents.sh --nrf-branch develop --amf-branch develop \
                              --smf-branch develop --upf-branch develop \
                              --ausf-branch develop --udm-branch develop \
                              --udr-branch develop --upf-vpp-branch develop \
                              --nssf-branch develop --nef-branch develop \
                              --pcf-branch develop --lmf-branch develop
---------------------------------------------------------
OAI-NRF     component branch : develop
OAI-AMF     component branch : develop
OAI-SMF     component branch : develop
OAI-UPF     component branch : develop
OAI-AUSF    component branch : develop
OAI-UDM     component branch : develop
OAI-UDR     component branch : develop
OAI-UPF-VPP component branch : develop
OAI-NSSF    component branch : develop
OAI-NEF     component branch : develop
OAI-PCF     component branch : develop
OAI-LMF     component branch : develop
---------------------------------------------------------
git submodule deinit --all --force
git submodule init
git submodule update --init --recursive
```

## 2. Generic Parameters

If you are re-building CN5G images, be careful that `docker` or `podman` may re-use `cached` blobs
to construct the intermediate layers.

We recommend to add the `--no-cache` option in that case.

### 2.1. On a Ubuntu Host

We are supporting the following releases:

* Ubuntu `20.04` or `focal`
* Ubuntu `22.04` or `jammy`

When building, you can specify which base image to work on (by default it will be `ubuntu:focal`).

You just add the `--build-arg BASE_IMAGE=ubuntu:xxxx` option.

**CAUTION: Since `v1.5.1` we are no longer supporting Ubuntu `18.04` or `bionic`.**

## 3. Build AMF Image

### 3.1 On a Ubuntu Host

For example, I am building using `ubuntu:focal` as base image:

```bash
$ docker build --target oai-amf --tag oai-amf:v1.5.1 \
               --file component/oai-amf/docker/Dockerfile.amf.ubuntu \
               --build-arg BASE_IMAGE=ubuntu:focal \
               component/oai-amf
$ docker image prune --force
$ docker image ls
oai-amf                 v1.5.1             f478bafd7a06        1 minute ago          179MB
...
```

### 3.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-amf --tag oai-amf:v1.5.1 \
               --file component/oai-amf/docker/Dockerfile.amf.rhel8 \
               component/oai-amf
...
```

The above command is with podman, in case you use docker, it can be changed with its docker equivalent.


## 4. Build SMF Image

### 4.1 On a Ubuntu Host

For example, I am building using `ubuntu:22.04` as base image:

```bash
$ docker build --target oai-smf --tag oai-smf:v1.5.1 \
               --file component/oai-smf/docker/Dockerfile.smf.ubuntu \
               --build-arg BASE_IMAGE=ubuntu:22.04 \
               component/oai-smf
$ docker image prune --force
$ docker image ls
oai-smf                 v1.5.1             f478bafd7a06        1 minute ago          193MB
...
```

### 4.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-smf --tag oai-smf:v1.5.1 \
               --file component/oai-smf/docker/Dockerfile.smf.rhel8 \
               component/oai-smf
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 5. Build NRF Image

### 5.1 On a Ubuntu Host

For example, I am building using `ubuntu:jammy` as base image:

```bash
$ docker build --target oai-nrf --tag oai-nrf:v1.5.1 \
               --file component/oai-nrf/docker/Dockerfile.nrf.ubuntu \
               --build-arg BASE_IMAGE=ubuntu:jammy \
               component/oai-nrf
$ docker image prune --force
$ docker image ls
oai-nrf                 v1.5.1             04334b29e103        1 minute ago          247MB
...
```

### 5.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-nrf --tag oai-nrf:v1.5.1 \
               --file component/oai-nrf/docker/Dockerfile.nrf.rhel8 \
               component/oai-nrf
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 6. Build UPF Image

### 6.1 On a Ubuntu Host

For example, I am building using `ubuntu:20.04` as base image:

```bash
$ docker build --target oai-upf --tag oai-upf:develop \
               --file component/oai-upf/docker/Dockerfile.upf.ubuntu \
               --build-arg BASE_IMAGE=ubuntu:20.04 \
               component/oai-upf
$ docker image prune --force
$ docker image ls
oai-upf                 develop            dec6311cef3b        1 minute ago          155MB
...
```

### 6.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-upf --tag oai-upf:develop \
               --file component/oai-upf/docker/Dockerfile.upf.rhel8 \
               component/oai-upf
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 7. Build AUSF Image

### 7.1 On a Ubuntu Host

```bash
$ docker build --target oai-ausf --tag oai-ausf:v1.5.1 \
               --file component/oai-ausf/docker/Dockerfile.ausf.ubuntu \
               component/oai-ausf
$ docker image prune --force
$ docker image ls
oai-ausf          v1.5.1              77a96de94c23        1 minute ago        231MB
...
```

### 7.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-ausf --tag oai-ausf:v1.5.1 \
               --file component/oai-ausf/docker/Dockerfile.ausf.rhel8 \
               component/oai-ausf
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 8. Build UDM Image

### 8.1 On a Ubuntu Host

```bash
$ docker build --target oai-udm --tag oai-udm:v1.5.1 \
               --file component/oai-udm/docker/Dockerfile.udm.ubuntu \
               component/oai-udm
$ docker image prune --force
$ docker image ls
oai-udm                 v1.5.1             10a4334e31be        1 minute ago          229MB
...
```

### 8.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-udm --tag oai-udm:v1.5.1 \
               --file component/oai-udm/docker/Dockerfile.udm.rhel8 \
               component/oai-udm
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 9. Build UDR Image

### 9.1 On a Ubuntu Host

```bash
$ docker build --target oai-udr --tag oai-udr:v1.5.1 \
               --file component/oai-udr/docker/Dockerfile.udr.ubuntu \
               component/oai-udr
$ docker image prune --force
$ docker image ls
oai-udr                 v1.5.1             581e07d59ec3        1 minute ago          234MB
...
```

### 9.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-udr --tag oai-udr:v1.5.1 \
               --file component/oai-udr/docker/Dockerfile.udr.rhel8 \
               component/oai-udr
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.


## 10. Build UPF-VPP Image

### 10.1 On a Ubuntu Host

```bash
$ docker build --target oai-upf-vpp --tag oai-upf-vpp:v1.5.1 \
               --file component/oai-upf-vpp/docker/Dockerfile.upf-vpp.ubuntu \
               component/oai-upf-vpp
$ docker image prune --force
$ docker image ls
oai-upf-vpp             v1.5.1             581e07d59ec3        1 minute ago          937MB
...
```

### 10.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-upf-vpp --tag oai-upf-vpp:v1.5.1 \
               --file component/oai-upf-vpp/docker/Dockerfile.upf-vpp.rhel7 \
               component/oai-upf-vpp
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 11. Build NSSF Image

### 11.1 On a Ubuntu Host

```bash
$ docker build --target oai-nssf --tag oai-nssf:v1.5.1 \
               --file component/oai-nssf/docker/Dockerfile.nssf.ubuntu \
               component/oai-nssf
$ docker image prune --force
$ docker image ls
oai-nssf          v1.5.1              77a96de94c23        1 minute ago        231MB
...
```

### 11.2 On a RHEL8 Host

RHEL base images generally need a subscription to access the package repository.
For that the base image needs ca and entitlement .pem files.

Copy the ca and entitlement .pem files in your present working directory `pwd` before building the image, you can do it like this:

```bash
$: mkdir -p ./etc-pki-entitlement ./rhsm-conf ./rhsm-ca
$: cp /etc/pki/entitlement/*pem ./etc-pki-entitlement
$: cp /etc/rhsm/ca/*pem ./rhsm-ca
$ sudo podman build --target oai-nssf --tag oai-nssf:v1.5.1 \
               --file component/oai-nssf/docker/Dockerfile.nssf.rhel8 \
               component/oai-nssf
...
```

The above command is with podman, in case you use docker it can be changed with its docker equivalent.

## 12. Build Traffic-Generator Image

This is just a utility image.

```bash
$ docker build --target trf-gen-cn5g --tag trf-gen-cn5g:latest \
               --file ci-scripts/Dockerfile.traffic.generator.ubuntu \
               .
```

You are ready to [Configure the Containers](./CONFIGURATION.md) or to deploy the images using [helm-charts](./DEPLOY_SA5G_HC.md)

You can also go [back](./DEPLOY_HOME.md) to the list of tutorials.
