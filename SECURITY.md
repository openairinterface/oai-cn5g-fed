<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| develop | :white_check_mark: |

## Reporting a Vulnerability

We strongly encourage you to report security vulnerabilities first to our
contact address,
[oaicicd@openairinterface.org](mailto:oaicicd@openairinterface.org), before
disclosing them in any public forum. This email address is shared by all OAI
CN5G components, so make sure to keep the subject tag given below, so that the
report is routed to this repository.

Reports sent to this address are handled confidentially by members of
the OAI security team and are treated as a top priority.

- **Email subject**: `[SEC-VUL-OAI-CN5G-FED]: "Mention the affected
  functionality here"`.
- **Affected commit**: provide the commit SHA where the vulnerability was
  observed. This should normally be the latest commit or a recent commit at the
  time of the report. If a shared submodule is affected, mention its commit SHA
  as well.
- **Vulnerability description**: please keep it concise and avoid unnecessary
  detail. Present a clear summary of the vulnerability and its impact first,
  followed by the affected files, versions, and other relevant details.
- **Affected functionality and file paths**.
- **Discovery and reproduction information**: how did you discover the problem,
  and how can it be reproduced?
- **AI tool disclosure**: please mention and explain whether you have used any
  AI tool to generate this report or to find the vulnerability. If you used one
  to find the vulnerability, please see the next section. The tool should be
  reported as `TOOL-NAME: LLM-MODEL-VERSION`, for example
  `Claude:claude-5-opus`.
- **Relevant environment details**: CPU, RAM, hard disk, kernel command-line
  parameters, operating system name, and kernel version.
- **Relevant log excerpts**: do not attach any large files, just an extract of
  the logs if needed. We may request the full logs later.
- **Proposed patch, if available**: we encourage you to share a tentative patch
  if you have one.

### Use of AI to find a vulnerability

If an AI tool was used to identify or discover the vulnerability, do not submit
the vulnerability through the email. Instead, report it as a public GitHub issue
in the
[GitHub Issue Tracker](https://github.com/openairinterface/oai-cn5g-fed/issues),
because multiple researchers using the same or different AI tools can find the
same vulnerability.

In this case, please follow the format below to open the issue:

- **Issue title**: `[AI-SEC-VUL-OAI-CN5G-FED]: "Mention the affected
  functionality here"`.
- **Issue label**: apply the
  https://github.com/openairinterface/oai-cn5g-fed/labels/security
  label when opening the issue.
- **Affected commit**: provide the commit SHA where the vulnerability was
  observed. This should normally be the latest commit or a recent commit at the
  time of the report. If a shared submodule is affected, mention its commit SHA
  as well.
- **Vulnerability description**: please keep it concise. Reports generated or
  assisted by AI tools often contain excessive detail or too many sections,
  which makes the important information hard to identify. Present a clear
  summary of the vulnerability and its impact first, followed by the affected
  files, versions, and other relevant details.
- **Affected functionality and file paths**.
- **Reproduction information**: do not mention how to reproduce the problem in
  the issue description. The security team will contact you about it.
- **AI tool disclosure**: please mention and explain whether you have used any
  AI tool to find the vulnerability. It should be reported as
  `TOOL-NAME: LLM-MODEL-VERSION`, for example `Claude:claude-5-opus`.
- **Relevant environment details**: CPU, RAM, hard disk, kernel command-line
  parameters, operating system name, and kernel version.
- **Relevant log excerpts**: do not attach any large files, just an extract of
  the logs if needed. We may request the full logs later.
- **Proposed patch, if available**: AI tools are good at fixing vulnerabilities;
  you can ask your AI tool to provide a patch.

## Scope

The [openairinterface/oai-cn5g-fed](https://github.com/openairinterface/oai-cn5g-fed)
repository is the **federation repository** of the OAI 5G Core. It does not
contain the source code of any network function; it provides the deployment
artifacts and the tooling around them: the docker-compose files and the
configuration templates in [docker-compose/](./docker-compose), the subscriber
database seeds, the [openshift/](./openshift) artifacts, the helper scripts, the
tutorials in [docs/](./docs), and the CI tooling and tests in
[ci-scripts/](./ci-scripts) and [test/](./test).

Issues in the OAI CN5G network functions themselves (AMF, SMF, UPF, AUSF, UDM,
UDR, NRF, PCF, NSSF, NEF, LMF, NWDAF) must be reported against their own
repositories, as must issues in the Duranta OAI codebase
[duranta-project/openairinterface5g](https://github.com/duranta-project/openairinterface5g).
A defect in a network function reached while running a deployment described here
belongs to that network function's repository, not to this one.

The Helm charts are not kept here either, even though their deployment is
documented in [DEPLOY_SA5G_HC.md](./docs/DEPLOY_SA5G_HC.md): they live in
[openairinterface/orchestration](https://github.com/openairinterface/orchestration)
under `charts/` and must be reported against that repository.

Issues in the shared submodule
[oai-cn5g-common-ci](https://github.com/openairinterface/oai-cn5g-common-ci),
checked out at `ci-scripts/common`, can be reported here if they are reachable
through this repository. In that case, please state clearly which component is
affected and give the commit ID of the affected submodule in addition to the
federation commit.

Security reports are in scope when they affect the confidentiality, integrity,
or availability of a 5G Core deployed with the artifacts of this repository, in
a documented or reasonably expected deployment.

In-scope examples include:

- Default or hard-coded credentials, keys, or subscriber secrets shipped in the
  docker-compose files, in the configuration templates under
  [docker-compose/conf/](./docker-compose/conf), or in the database seeds under
  [docker-compose/database/](./docker-compose/database), where a documented
  deployment uses them as-is.
- Container or pod settings in the docker-compose and [openshift/](./openshift)
  artifacts that grant unsafe privileges, mount sensitive host paths, or share
  host namespaces beyond what the deployment needs.
- Deployment artifacts that expose an internal service, an SBI endpoint, or a
  management interface outside the intended network, or that silently disable
  authentication, TLS, or integrity protection.
- Command injection, unsafe use of `sudo`, insecure handling of temporary files,
  or arbitrary file access in the deployer and the helper scripts
  ([docker-compose/core-network.py](./docker-compose/core-network.py),
  [scripts/](./scripts), [ci-scripts/](./ci-scripts)).
- Exposure of subscriber identifiers (SUPI/IMSI/SUCI/GUTI), security keys, or
  credentials through the logs, captures, or artifacts that the deployment and
  the tutorials produce.
- Tutorials or sample configurations that lead a reader into an insecure
  deployment while presenting the result as production-ready.
- CI, build, or release-pipeline issues only when they could compromise official
  OAI release artifacts, published images, or the trusted source distribution.

Out-of-scope examples include:

- Defects in the code of a network function, even when first observed while
  running a deployment from this repository; see the Scope section above.
- Performance issues without a security impact.
- Bugs requiring local admin/root access on the host running the deployment,
  with no privilege boundary crossed.
- Reports against unsupported forks, private deployments, local lab
  misconfiguration, or modified code not present in this repository.
- Vulnerabilities solely caused by third-party projects or dependencies should
  generally be reported upstream. If the vulnerability affects the security of
  the deployment or requires a change in this repository, please report it here
  as well.
- Attacks that require a trusted operator role, such as a deployment
  deliberately misconfigured by its owner, unless a documented trust boundary
  is crossed.
- Denial of service that only depends on flooding a plaintext, unprotected
  transport (for example, running SBI without TLS or SCTP without IPsec) as
  permitted by the deployment, rather than on a defect in these artifacts.
- Features documented as not supported in
  [FEATURE_SET.md](./FEATURE_SET.md), or issues in experimental or
  incomplete functionality, unless they demonstrate a realistic impact on
  supported deployments.
- Issues only affecting contributor CI jobs, temporary development artifacts, or
  untrusted test images, unless they can affect official releases.

## Disclosure

The project aims to acknowledge all contributors for valid reports of security
vulnerabilities. Each vulnerability sent to the security contact address will,
after review and if accepted, be handled through a draft GitHub Security
Advisory, and a CVE ID may be assigned as part of that process. Reporters will
be credited by name or GitHub handle in the advisory. Disclosure will typically
be made at or shortly after the release of the fix.

The security team will decide whether a report meets the requirements for a
GitHub advisory and CVE ID on a case-by-case basis.

Some reports may lead to changes in the OAI CN5G codebase even if they do not
result in an associated advisory. Examples of reports that may fall into this
category include (but are not limited to):

- Reports of vulnerabilities in unstable functionality or incomplete features.
- Reports of vulnerabilities where there is no evidence that a recent OAI CN5G
  release tag has been affected.

In such cases, the project aims to credit reporters with an acknowledgement in
the relevant fix commit via a `Reported-by:` trailer in the commit message.

**NOTE**: The OAI project manages CVEs only via the
[GitHub security advisory database](https://github.com/advisories).
If you have already requested or obtained a CVE identifier from
[CVE.org](https://www.cve.org/ReportRequest/ReportRequestForNonCNAs) or another
CVE Numbering Authority, please provide it to the security team so that the
project can coordinate the affected advisory and ensure that the published
information accurately reflects the final fix and impact.

### Timeline

After receiving the report, the team will validate the vulnerability and will
respond to the reporter within 10 days. The project aims to publish the advisory
with the fix within 90 days of receiving the report, where reasonably
practicable.
