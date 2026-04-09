<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing to OpenAir-CN-5G

We want to make contributing to this project as easy and transparent as possible.

Please refer to the steps described on our website: [How to contribute to OAI](https://www.openairinterface.org/?page_id=112)

1. If you are contributing source code which is under CSSL License or will be in CSSL license then,
sign and return a Contributor License Agreement to OAI team. Files under other licenses require signed commits.
2. Create an account on [Eurecom GiLab Server](https://gitlab.eurecom.fr/users/sign_in) if you do not have any.
   - If your email domain (`@domain.com`) is not whitelisted, please contact us (mailto:oaicicdteam@openairinterface.org).
   - Eurecom GitLab does NOT accept public email domains.
3. Provide the `username` of this account to the OAI team (mailto:oaicicdteam@openairinterface.org) so you have developer rights on this repository.
4. You can fork onto another hosting system. But we will **NOT** accept a pull request from a forked repository.
      - This decision was made for the license reasons.
      - The Continuous Integration will reject your pull request.
      - All pull requests SHALL have **`develop`** branch as target branch.
5. Mandatory signing of all the commits using the email address used for CLA.

## Commit Guidelines

### Signing Commits

To sign commits:

You can also get the verified label on your commits via using [SSH KEYS or GPG KEYS](https://docs.gitlab.com/user/project/repository/signed_commits/)

```
# edit .git/config in the git repository you are working
# add the user section
[user]
    name = YOUR NAME
    email = YOUR EMAIL ADDRESS
# if you use signingkey then use below
[user]
    name = YOUR NAME
    email = YOUR EMAIL ADDRESS
    signingkey = LOCATION OF SSH KEYS or GPG KEY
[gpg]
	format = ssh
[commit]
	gpgsign = true
```

You can use `git commit -s` to sign your commits with your email address. 

> **NOTE:** If your commits are not signed the CI framework will not accept the MR.

### Writing Commit Messages

To help maintainers and reviewers understand your changes, please follow these guidelines when writing commit messages:

- Use short, descriptive title
- Separate subject from body with a blank line
- Use the body to explain what and why
- Prefix your commit with a type, for example:

```bash
feat: Adds a new feature
fix: Fixes a bug
refactor: Rewrites or restructures code without adding a feature or fixing a bug
chore: Miscellaneous changes, e.g., updating dependencies
perf: Commits aimed at improving performance
ci: Changes related to Continuous Integration
docs: Updates documentation (README, tutorials)
style: Code formatting changes (whitespace, indentation, etc.)
test: Adds or fixes tests
```

In case you make an error in a recent commit you can run the following command:

```bash
git commit --amend # allows you to modify and add changes to the most recent commit
git push origin feature-branch --force-with-lease
```

### Rewriting Commits

Your commit history should remain clean and meaningful. Avoid commits that only “clean up” or fix issues in previous commits, such as messages like `Fix typo`.
Instead, combine those changes into a single commit using interactive rebase or fixup commits.

- Use `git rebase -i` to interactively edit older commit messages or squash related commits.
- Use `git commit --fixup=<commit-hash>` to mark a commit for automatic squashing into a previous commit.
- Please make sure that the commit message clearly summarizes all changes included.

**Example using Interactive Rebase:**

```bash
git rebase -i HEAD~3   # interactively rebase the last 3 commits
# mark commits to squash with "s" or "squash" and edit the final commit message
# mark commits to edit commit message with "e" or "edit"
# save and follow the prompts to update messages
git push origin feature-branch --force-with-lease # force with lease let's you only overwrite what you also have locally in origin/feature-branch
```

**Example using fixup commits:**

```bash
# Create a fixup commit to automatically squash into an earlier commit
git commit --fixup=<commit-hash>

# Start an interactive rebase with autosquash
git rebase -i --autosquash <commit-hash>^

# Git opens a commit list:
## pick - keep the commit as-is
## fixup - automatically squash into the previous commit
## If you save and close the file with no other changes, the rebase will proceed

# If conflicts occur during the rebase, resolve them and run
git rebase --continue

# Push to remote branch
git push origin feature-branch --force-with-lease
```

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
    -  To make code review easier and faster, please keep the pull requests short and focused.
3.  Our Continuous Integration (CI) process will be triggered automatically on your proposed modified code and check the validity.
    -  Check build
    -  Check some formatting rules
    -  Run a bunch of tests
4.  If at least one of these steps fails, you will have to push corrections onto your source branch.
    -  The step 3. will be again automatically triggered on this new commit.
    -  Please wait that your run is finished before committing and pushing new modifications on your source branch.
    -  That will allow fairness on the CI usage to other contributors.
5.  When this automated process passes, one of our CI administrators will review your changes or assign a senior contributor to do a peer-review.
    -  The reviewer should carefully check the code, commit messages, and CI results.
    -  All discussion threads must be resolved before approval.
6.  Once the peer reviewer accepts your modification, one of our CI administrators will accept and merge your pull request
    -  The CI will run again on the new `develop` branch commit.
    -  The source branch WILL be deleted by one of our CI administrators.

## Reporting Bugs

Please report software bugs or security issues in the [Gitlab Issue Tracker](https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-fed/-/issues).
Use the label ~Bug for bugs, ~Security for security issues, and ~Feature for feature requests.
If you are unsure whether it is a bug, start with the [mailing lists](https://gitlab.eurecom.fr/oai/openairinterface5g/-/wikis/MailingList).
If needed, the OAI team will open an issue on your behalf.

When creating an issue, please include:

- A clear description of the problem
- Expected behavior — what you thought should happen
- Observed behavior — what actually happened
- Steps to reproduce — include commands, configuration, or environment details as needed
- Use bullet points and code blocks for logs or commands to make the issue easier to understand.
