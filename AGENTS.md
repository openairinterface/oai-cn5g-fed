<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Repository Guidelines for Agents

These guidelines are the default conventions for working in this repository.
Explicit user instructions always take precedence and override them.

This file only adds what an agent needs on top of [CONTRIBUTING.md](./CONTRIBUTING.md),
which holds the licensing and contribution requirements. Read it first.

This repository is a federation: it carries the tutorials, the deployment files and
the tests, while the network function (NF) sources live in separate repositories that
`scripts/syncComponents.sh` clones into `component/`.

## Key directories

| Path | Contents |
| --- | --- |
| `ci-scripts/` | Jenkins pipelines and the scripts they run. `ci-scripts/common/` is a git submodule |
| `docker-compose/` | docker compose files, NF configuration files, healthcheck scripts |
| `docs/` | tutorials |
| `openshift/` | build configs for the CentOS-based images |
| `scripts/` | `syncComponents.sh`, which clones and synchronizes the NFs into `component/` |
| `test/` | Robot Framework test suite |

## Commit guidelines

Follow the [commit guidelines](./CONTRIBUTING.md#commit-guidelines). In particular:

- Agents MUST NOT add a `Signed-off-by` or a `Co-authored-by` tag. Only humans can
  legally certify the Developer Certificate of Origin (DCO).
- Agents MUST add an `Assisted-by` tag, so that the evolving role of AI in the
  development process stays visible:

      Assisted-by: AGENT_NAME:MODEL_VERSION

  where `AGENT_NAME` is the AI tool or framework and `MODEL_VERSION` the exact model
  version used, for example:

      Assisted-by: Claude:claude-opus-5

- Do not write long, overwhelming commit messages.
- Keep each commit focused on one logical change.
- Keep the subject concise, preferably no more than 72 characters.

Every commit must be signed with the SSH or GPG key of the human submitter, otherwise
the pull request is not merged. The key and its configuration belong to the developer,
so agents must not change them, and must never work around a failing signature with
`--no-gpg-sign`: report the failure instead. Check a commit with
`git log --show-signature`. See [signing commits](./CONTRIBUTING.md#signing-commits).

## Documentation practices

Write so that a developer new to this codebase can follow you; do not assume the
reader is an expert in the area you are writing about. Be clear, concise and specific.

All tutorials reside in the [docs](./docs/) folder.

## Code formatting

Changes to source files must follow the [coding style](./CONTRIBUTING.md#coding-style).
Run `ci-scripts/common/bash/format-code.sh` to match the CI formatting checks.

## Synchronize all NFs

Use `scripts/syncComponents.sh` to synchronize the network functions into `component/`.
It also updates the submodules inside each of them. See
[synchronizing all NFs](./CONTRIBUTING.md#synchronizing-all-nfs).

The `ci-scripts/common` submodule of this repository is separate: `syncComponents.sh`
does not touch it. Initialize it with `git submodule update --init --recursive`.

## Rebase the branches with the latest develop

Feature branches must be rebased on the latest `origin/develop` and must not contain
any merge commit. See
[rebase a branch with develop](./CONTRIBUTING.md#rebase-a-branch-with-develop).

## Builds

If a change affects the behaviour of a network function, build its image first. The
build runs from the synchronized `component/` tree, for example for the AMF:

```bash
docker build --target oai-amf --tag oai-amf:test \
             --file component/oai-cn5g-amf/docker/Dockerfile.amf.ubuntu \
             component/oai-cn5g-amf
```

The CentOS Stream 10 image of the same NF is built the same way, from
`docker/Dockerfile.amf.centos`:

```bash
docker build --target oai-amf --tag oai-amf:centos-test \
             --file component/oai-cn5g-amf/docker/Dockerfile.amf.centos \
             component/oai-cn5g-amf
```

More details are in [BUILD_IMAGES.md](./docs/BUILD_IMAGES.md). The same CentOS
Dockerfiles are also driven by the OpenShift build configs in
[openshift](./openshift/README.md), which is how the images are built for a cluster.

## Tests

Once the images are built, agents can run the tests that cover the change. The robot
suites and the tutorials each take their image tags from a different place, so point
the one you are running at the image you just built.

### Robot tests

Run them for changes in `amf`, `ausf`, `nrf`, `pcf`, `smf`, `udm`, `udr`, `upf` or in
the `test/` folder of this repository. The tags live in
[test/image_tags.py](./test/image_tags.py); edit that file to test your own build, and
keep the entries whitespace-free, because the CI rewrites them with `sed`. See the
[test suite guide](./test/README.md).

### Tutorials

A tutorial is executed the same way the CI does it, by extracting and running the
commands in its markdown file:

```bash
ci-scripts/checkTutorial.py --tutorial DEPLOY_SA5G_WITH_QOS.md
```

The tutorial deploys the tags written in the `image:` lines of the docker compose file
it uses. Edit those lines to test your own build,
and restore the file afterwards, the way the CI does once a stage is over.

This really deploys the core on the machine: it runs every command of the tutorial
from the `docker-compose/` folder, in order, including the ones that start containers,
create docker networks, capture packets with `sudo tshark` and tear everything down
again. Do not start one on a machine that is already running a deployment, and check
first that nothing else is using it.

Only the commands the script can extract are executed: a line prefixed with `$: `
inside a code block whose opening fence is three backticks, a space, and the word
`shell`. A block opened with any other fence -- `console`, or `shell` with no space --
is documentation only and is never run, so a tutorial can pass while the command you
added was silently skipped.

Run a tutorial when the change touches one of the network functions it deploys, or
any of the files it uses. The table lists which network function pulls in which
tutorial in the CI, and can be used the same way for a local run.

| Tutorial | CI stage | Run it for changes in |
| --- | --- | --- |
| [DEPLOY_SA5G_MINI_WITH_GNBSIM.md](./docs/DEPLOY_SA5G_MINI_WITH_GNBSIM.md) | Check Minimalist Deployment Tutorial | `amf`, `smf`, `upf` |
| [DEPLOY_SA5G_BASIC_DEPLOYMENT.md](./docs/DEPLOY_SA5G_BASIC_DEPLOYMENT.md) | Check Basic Deployment Tutorial | `nrf`, `amf`, `smf`, `upf`, `ausf`, `udm`, `udr` |
| [DEPLOY_SA5G_ULCL.md](./docs/DEPLOY_SA5G_ULCL.md) | Check UL-CL Policies Tutorial | `amf`, `smf`, `pcf` |
| [DEPLOY_SA5G_BASIC_MONGODB.md](./docs/DEPLOY_SA5G_BASIC_MONGODB.md) | Check MongoDB deployment Tutorial | `udr` |
| [DEPLOY_SA5G_WITH_QOS.md](./docs/DEPLOY_SA5G_WITH_QOS.md) | Check QoS Tutorial | any network function except `nssf`; it is the smoke test of a core change |
| [Ethernet_PDU_Sessions.md](./docs/Ethernet_PDU_Sessions.md) | Check Ethernet PDU Sessions Tutorial | `smf`, `upf` |
| [DEPLOY_SA5G_WITH_UPF_EBPF.md](./docs/DEPLOY_SA5G_WITH_UPF_EBPF.md) | Check Basic w/ eBPF Deployment Tutorial | `upf`, eBPF datapath |

Also agents can run a tutorial when the change is in the files it uses, even if no network
function is touched: its docker compose file in `docker-compose/`, the NF
configuration it loads, or the markdown file itself.

Agents should always try to add unit tests for new features and bug fixes.

## Actions that need explicit instructions

Agents must never push or update a remote or upstream branch, create a pull request,
or post a comment on one, without being explicitly asked to.
