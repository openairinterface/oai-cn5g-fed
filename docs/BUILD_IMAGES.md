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

They are named as `git sub-modules` in the `component` folder.

Before doing anything, you SHALL retrieve the code for each git sub-module.

Normally the `./scripts/syncComponents.sh` should help synchronize all of them.

Now if you have non-tracked files or modified files within git submodules, this script may not work. 

Use the `--verbose` option to see the execution of each command.

If the synchronization fails, you may need to go into the path of the failing git-submodule(s) and clean the workspace from non-tracked/modified files. And then execute the `./scripts/syncComponents.sh` script again.

The 2 most important commands to know are :

1. `git submodule deinit --force .`
2. `git submodule update --init --recursive`

You can execute them at this federation level or at the nf component level.

## 1.1. You are interested in a stable version. ##

We recommend to synchronize with the master branches on all git sub-modules.

We also recommend that you synchronize this "tutorial" repository with a provided tag. By doing so, the `docker-compose` files will be aligned with feature sets of each cNF.

```bash
# Clone directly on the <tag> release tag
git clone --branch <tag> https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed.git
cd oai-cn5g-fed
# If you forgot to clone directly with tag/branch
git checkout -f <tag>

# Synchronize all git submodules
./scripts/syncComponents.sh
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

## 1.2. You are interested in the latest features. ##

All the latest features are pushed to the `develop` branches of each NF repository.

It means that we/you are able to build and the Continuous Integration test suite makes sure it
does NOT break any existing tested feature.

So for example, at time of writing, N2 Handover support code is included in `v1.1.0` release. But it is not tested yet. So it is not advertised in the `CHANGELOG.md` and the Release Notes.

Anyhow, the tutorials' docker-compose files on the latest commit of the `develop` branch of `oai-cn5g-fed` repository SHALL support any additional un-tested feature.

# 2. Generic Parameters #

If you are re-building CN5G images, be careful that `docker` or `podman` may re-use `cached` blobs to construct the intermediate layers.

We recommend to add the `--no-cache` option in that case.

## 2.1. On a Ubuntu Host ##

We are supporting the following releases:

* Ubuntu `22.04` or `jammy`

You just add the `--build-arg BASE_IMAGE=ubuntu:xxxx` option.

# 3. Build Network Function Images #

## 3.1 On a Ubuntu Host ##

For example amf image can be build like below for base container image `ubuntu:jammy`:

```bash
docker build --target oai-amf --tag oai-amf:latest \
               --file component/oai-amf/docker/Dockerfile.amf.ubuntu \
               --build-arg BASE_IMAGE=ubuntu:jammy \
               component/oai-amf
```

## 3.2 RHEL9/UBI Images ##

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
