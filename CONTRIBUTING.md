<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing to OpenAir-CN-5G

We want to make contributing to this project as easy and transparent as possible.

Please refer to the steps described on our website: [How to contribute to OAI](https://www.openairinterface.org/?page_id=112)

1. Sign and return a Contributor License Agreement to OAI team.
2. Create an account on [Eurecom GiLab Server](https://gitlab.eurecom.fr/users/sign_in) if you do not have any.
   - If your email domain (`@domain.com`) is not whitelisted, please contact us (mailto:oaicicdteam@openairinterface.org).
   - Eurecom GitLab does NOT accept public email domains.
3. Provide the `username` of this account to the OAI team (mailto:oaicicdteam@openairinterface.org) so you have developer rights on this repository.
4. You can fork onto another hosting system. But we will **NOT** accept a pull request from a forked repository.
      - This decision was made for the license reasons.
      - The Continuous Integration will reject your pull request.
      - All pull requests SHALL have **`develop`** branch as target branch.

## Synchronizing all NFs

We are using nested GIT submodules for network functions in this repository, you can use `scripts/syncComponents.sh`
script to fetch all the network functions.

## Coding Styles

We are using `clang-format` as formatting tool on the C/C++ code.

On a Ubuntu-22 server:

```bash
sudo apt-get update
sudo apt-get install clang-format-12
sudo update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-12 20
clang-format --version
Ubuntu clang-format version 12.0.1-19ubuntu3
```

How to test (as CI):

```
# run the below command in the parent folder
ci-scripts/common/bash/checkCodingFormattingRules.sh
```

How to format (fix issues reported by above script):

```bash
cd myClonedWorkspace/src
clang-format -i theFilesYouWantToFormat
```

## License

By contributing to OpenAirInterface, you agree that your contributions will be licensed under the [LICENSE](LICENSE) file in the root directory of this source tree.

## Continuous Integration process

1.  You push your modified code with the new branch onto our [official GitLab repository](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed).
    -  Please make the name of the branch explicit and short.
2.  You create a pull request from the [dedicated web page](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed/-/merge_requests).
    -  The `target` (`base` in the web-page) branch **SHALL be `develop`**.
    -  The `source` (`compare` in the web-page) branch is your branch.
3.  Our Continuous Integration (CI) process will be triggered automatically on your proposed modified code and check the validity.
    -  Check build
    -  Check some formatting rules
    -  Run a bunch of tests
4.  If at least one of these steps fails, you will have to push corrections onto your source branch.
    -  The step 3. will be again automatically triggered on this new commit.
    -  Please wait that your run is finished before committing and pushing new modifications on your source branch.
    -  That will allow fairness on the CI usage to other contributors.
4.  When this automated process passes, one of our CI administrators will review your changes or assign a senior contributor to do a peer-review.
5.  Once the peer reviewer accepts your modification, one of our CI administrators will accept and merge your pull request
    -  The CI will run again on the new `develop` branch commit.
    -  The source branch WILL be deleted by one of our CI administrators.
