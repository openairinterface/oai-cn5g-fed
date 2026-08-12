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
      <b><font size = "5">OpenAirInterface 5G Core Network Deployment : Building Container Images</font></b>
    </td>
  </tr>
</table>

# 1.  Retrieve the correct network function branches #

This repository only has tutorials and Continuous Integration scripts.

Each 5G Network Function source code is managed in its own repository.

They are cloned into the `component` folder.

Before doing anything, you SHALL retrieve the code for each network function.

Normally the [scripts/syncComponents.sh](../scripts/syncComponents.sh) should help synchronize all of them. A component that is not present yet is cloned on the spot.

The components are reset to a pristine state, so non-tracked or modified files within the component clones are discarded. The script stops and names the concerned components before modifying anything: commit or stash your work, or pass `--force` to discard it.

Run `./scripts/syncComponents.sh --help` to list all options, and use `--verbose` to see the execution of each command.
If the synchronization fails, the concerned component is named in the error message and is left untouched.

For each component, the script runs in order :

1. `git clone` -- only when the component is not there yet
2. `git fetch --prune --tags`
3. `git checkout --force --detach` -- on the requested branch or tag
4. `git submodule update --init --recursive` -- the component's own nested submodules
5. `git clean -x -d -ff`

You can execute them by hand at the nf component level.

## 1.1. You are interested in a stable version. ##

We recommend to synchronize with the develop branches on all network functions.

We also recommend that you synchronize this "tutorial" repository with a provided tag. By doing so, the `docker-compose` files will be aligned with feature sets of each cNF.

```bash
# Clone directly on the <tag> release tag
git clone --branch <tag> https://github.com/openairinterface/oai-cn5g-fed.git
cd oai-cn5g-fed
# If you forgot to clone directly with tag/branch
git checkout -f <tag>

# Synchronize all the network functions
./scripts/syncComponents.sh
[INFO] No common branch specified — using the default branch 'develop'.
---------------------------------------------------------
Detected branch of fed repository : HEAD
Common branch (unless overridden) : develop
Components synchronized into      : component/
OAI-CN5G-PCF     component branch : develop
OAI-CN5G-NRF     component branch : develop
OAI-CN5G-SMF     component branch : develop
OAI-CN5G-UPF     component branch : develop
OAI-CN5G-NSSF    component branch : develop
OAI-CN5G-LMF     component branch : develop
OAI-CN5G-AMF     component branch : develop
OAI-CN5G-NEF     component branch : develop
OAI-CN5G-UDM     component branch : develop
OAI-CN5G-UDR     component branch : develop
OAI-CN5G-AUSF    component branch : develop
---------------------------------------------------------
```

## 1.2. You are interested in the latest features. ##

All the latest features are pushed to the `develop` branches of each NF repository.

It means that we/you are able to build and the Continuous Integration test suite makes sure it
does NOT break any existing tested feature.

The tutorials' docker-compose files on the latest commit of the `develop` branch of `oai-cn5g-fed` repository SHALL support any additional un-tested feature.

# 2. Generic Parameters #

The official OAI CN5G container images use Ubuntu 22.04 as the container base image. They are compatible with Ubuntu hosts 22.04 through 26.04, Fedora 39 through 43, and RHEL 8 through 10.

Any Docker or Podman version available for those host releases should be fine. The examples below use Docker; Podman users can replace `docker` with `podman`.

If you are re-building CN5G images, be careful that `docker` or `podman` may re-use `cached` blobs to construct the intermediate layers.

We recommend to add the `--no-cache` option in that case.

## 2.1. Ubuntu-Based Images ##

The default Ubuntu image base is:

* Ubuntu `22.04` or `jammy`

You just add the `--build-arg BASE_IMAGE=ubuntu:xxxx` option.

# 3. Build Network Function Images #

## 3.1 Build Ubuntu-Based Images ##

For example amf image can be build like below for base container image `ubuntu:jammy`:

```bash
docker build --target oai-amf --tag oai-amf:latest \
               --file component/oai-cn5g-amf/docker/Dockerfile.amf.ubuntu \
               --build-arg BASE_IMAGE=ubuntu:jammy \
               component/oai-cn5g-amf
```

## 3.2 RHEL/UBI Images ##

Checkout this [tutorial](../openshift/README.md)

# 4. Build Traffic-Generator Image #

This is just a utility image.

```bash
$ docker build --target trf-gen-cn5g --tag trf-gen-cn5g:latest \
               --file ci-scripts/Dockerfile.traffic.generator.ubuntu \
               .
```

You are ready to [Configure the Containers](./CONFIGURATION.md) or to deploy the images using [helm-charts](./DEPLOY_SA5G_HC.md)

You can also go [back](./DEPLOY_HOME.md) to the list of tutorials.
