<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contribution Guidelines and Coding Style for Developers

We want to make contributing to this project as easy and transparent as possible.

Please refer to the steps described on our website: [How to contribute to OAI](https://www.openairinterface.org/?page_id=112)

1. If you are contributing source code which is under CSSL License or will be in CSSL license then,
sign and return a Contributor License Agreement to OAI team. Files under other licenses require signed commits.
   - Individual contributors should sign the [ICLA](https://openairinterface.org/wp-content/uploads/2026/03/ICLA-OAI-RAN-5GCN-SPGW-CU-FlexRIC.pdf).
   - Contributions made on behalf of an organization require the [CCLA](https://openairinterface.org/wp-content/uploads/2026/03/CCLA-OAI-RAN-5GCN-SPGW-CU-FLEXRIC.pdf).
2. Create an account on [GitHub](https://github.com/) if you do not have any.
3. Pull requests from forked repositories are currently not accepted.
4. All pull requests must target the **`develop`** branch.
5. Mandatory signing of all the commits using the email address used for CLA.

## Commit Guidelines

Every pull request must pass two checks before it can be merged:

1. **[Developer Certificate of Origin (DCO)](https://en.wikipedia.org/wiki/Developer_Certificate_of_Origin)**:
   Each commit must include a `Signed-off-by:` trailer in the commit message.
   Use `git commit -s` (or `--signoff`).

2. **[Verified commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)**:
   Each commit must be cryptographically signed using SSH or GPG keys to confirm
   its origin.

### Signing Commits

GitHub supports commit signing using either SSH keys or GPG keys.
For more information, see the
[GitHub documentation](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

Before configuring commit signing:

- Generate an SSH key pair or GPG key pair.
- Add your public key to your GitHub account.
- Verify your GitHub email address (required for “Verified” commits to work).
- If using SSH signing, ensure the key is registered in GitHub for:
    - Authentication (SSH and GPG keys)
    - Signing commits (Signing Keys)

> **NOTE:**
> Adding an SSH key for repo access does not automatically enable commit signing.
> The key must also be added under GitHub's Signing Keys settings.


To ensure commits show as Verified on GitHub:

- Your `git config user.email` must match a GitHub email
- That email must be verified in your GitHub account

For more information, see the
[GitHub Docs](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/verifying-your-email-address)

Configure your repository's `.git/config`:

```ini
# Edit the git configuration

[user]
    name = YOUR NAME
    email = YOUR VERIFIED EMAIL ADDRESS

    # REQUIRED for commit signing
    # Use ONE signing method (SSH or GPG)

    signingkey = YOUR_SIGNING_KEY

    # Examples:
    # SSH signing:
    # signingkey = ~/.ssh/id_ed25519.pub

    # GPG signing:
    # signingkey = YOUR_GPG_KEY_ID

[gpg]
    # REQUIRED: defines signing method (SSH or GPG)

    format = YOUR_SIGNING_FORMAT

    # Examples:
    # SSH signing:
    # format = ssh

    # GPG signing:
    # format = openpgp

[commit]
    gpgsign = true
```

> The private key is used automatically by SSH/Git when signing commits (SSH only).

#### Verifying Signed Commits

You can verify that commits are properly signed locally using:

```bash
git log --show-signature
```

GitHub should also display a Verified badge next to signed commits once the
signing key has been correctly configured in your account.

##### SSH Signature Verification (`allowed_signers`)

For SSH commit signing, local Git verification may require an `allowed_signers`
file. This is only used for local verification in Git and is not required
by GitHub.

If you see errors such as:

```text
No principal matched
Can't check signature
error: gpg.ssh.allowedSignersFile needs to be configured
```
you may need to configure it.

Create the file and add your signing identity:

```bash
mkdir -p ~/.config/git
touch ~/.config/git/allowed_signers
echo "user@example.com ssh-ed25519 AAAACexamplekeystringhere" > ~/.config/git/allowed_signers
```

Enable it in local repository Git config:

```bash
git config gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
```

> **NOTE:**
> This is only for local Git signature verification and does not affect GitHub,
> or remote repository behavior.

> **NOTE:** If your commits are not signed, the PR will not be merged.

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
#### Use of git commit trailers

You have to sign all your commits. Thus, every commit must have a git commit trailer that reads

```
Signed-off-by: Full Name <email-for-cla>
```

There are additional commit trailers that you can or should use:

- `Assisted-by: <Name>:<model>`: if you have been assisted by an AI/LLM, you
  must disclose this by indicating both the LLM name and model. Note that LLMs
  do not author, as _the submission is under your name_ (i.e., NEVER add an LLM
  through `Co-authored:by:`). The [Linux kernel documentation on AI
  assistents](https://docs.kernel.org/process/coding-assistants.html)
  might be helpful.
- `Reviewed-by: Full Name <email>` for a person that reviewed a code. We attach
  this trailer to the merge commit for people that reviewed a pull request.
- `Co-authored-by: Full Name <email>` for a person that significantly
  contributed to a commit and has co-authorship.
- `Fixes: <commit> ("<title>")` if a given commit fixes bug in an earlier,
  referenced commit. For ease-of-use, please include the commit title, and only
  the commit SHA, not a link.
- `Closes: #Issue` if a specific commit closes a bug. If the pull request
  description includes this, we add this to the merge commit.
- `Reported-by: Full Name <email>` if a person reported a bug or other useful
  information that led to this commit.
- `Tested-By: Full Name <email>` if a person tested a given patch.

Please also check the documentation via `man git-interpret-trailers`

#### AI Assistants

These guidelines are mostly based on [linux kernel guidelines](https://docs.kernel.org/process/coding-assistants.html)

This document provides guidance for AI tools and developers using AI assistance
when contributing to the respository.

AI tools helping with the development should follow the standard
openairinterface developement procedure.

- All code must be compatible with CSSL v1.0
- Use appropriate SPDX license identifiers

AI agents MUST NOT add `Signed-off-by` nor `Co-authored-by` tags.  Only humans
can legally certify the Developer Certificate of Origin (DCO).  The human
submitter is responsible for:

- Reviewing all AI-generated code
- Ensuring compliance with licensing requirements
- Adding their own Signed-off-by tag to certify the DCO
- Taking full responsibility for the contribution

When AI tools contribute to openairinterface,
proper commit message helps track the evolving role of AI in the development process.
Contributions should include an `Assisted-by` tag in the following format:

    Assisted-by: AGENT_NAME:MODEL_VERSION

- `AGENT_NAME` is the name of the AI tool or framework
- `MODEL_VERSION` is the specific model version used

```
Example:

    Assisted-by: Claude:claude-3-opus
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

We are using nested Git submodules for network functions in this repository, you can also use `scripts/syncComponents.sh`
script to fetch all the network functions.

```bash
git submodule deinit --force .
git submodule update --init --recursive
git submodule status
```

If the update fails, check for local changes or untracked files inside the affected submodule:

```bash
git status
```

Clean the submodule workspace if needed:

```bash
git reset --hard
git clean -fd
```

Then retry:

```bash
git submodule update --init --recursive
```

Use the `--verbose` option to display detailed execution information:

```bash
git submodule update --init --recursive --verbose
```

Avoid committing unintended submodule changes. If a submodule was updated accidentally, restore it from the parent repository:

```bash
git restore path/to/submodule
```

## Coding Style

We use `clang-format` to enforce the C/C++ coding style. The CI uses **`clang-format-12`**,
so please use the same version locally.

```bash
sudo apt-get update
sudo apt-get install clang-format-12
sudo update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-12 20
```

### Ubuntu 24.04

Use the following command to download the ClangFormat binary from the GitHub repository's releases page:

```bash
sudo wget -qO /usr/local/bin/clang-format https://github.com/cpp-linter/clang-tools-static-binaries/releases/latest/download/clang-format-12_linux-amd64
# set execute permission for the file
sudo chmod a+x /usr/local/bin/clang-format
```

Verify the installed version:

```bash
clang-format --version
```

Run the same formatting check as the CI:

```bash
ci-scripts/common/bash/checkCodingFormattingRules.sh
```

To automatically format your files:

```bash
clang-format -i <file1> <file2> ...
```

## License

By contributing to OpenAirInterface, you agree that your contributions will be licensed
under the [LICENSE](LICENSE) file in the root directory of this source tree.

1. [CSSL v1.0 license](LICENSES/preferred/CSSL-v1.0.txt): Source code and test scripts
2. [CC-BY-4.0](LICENSES/preferred/CC-BY-4.0.txt): All the documentations
3. [MIT](LICENSES/preferred/MIT.txt): Orchestration (helm-charts, docker compose)

Certain files are using different licenses; you can read about them in
[NOTICE](NOTICE).

## Main Workflow

1. Push your modified code to a new branch in the [GitHub repository](https://github.com/openairinterface/oai-cn5g-fed).
   * Please use a short and descriptive branch name.

2. Create a pull request on [GitHub](https://github.com/openairinterface/oai-cn5g-fed/pulls).
   * The `target` (`base` in the GitHub interface) branch **must be `develop`**.
   * The `source` (`compare` in the GitHub interface) branch is your development branch.
   * Break large changes into smaller, logical commits and keep pull requests focused.
     Smaller pull requests are easier to review, test, and merge.

3. The Continuous Integration (CI) process will be triggered and will validate your changes.

4. If any CI check fails, push the required fixes to your source branch.
   * Before pushing new commits, group related fixes together and test them locally when possible.
   * Avoid pushing multiple intermediate commits for the same CI failure.
   * CI will automatically run again on the new commit.
   * Please wait for the current CI run to complete before pushing additional changes.
   * This helps ensure fair CI resource usage for all contributors.

5. Once all CI checks pass, a CI administrator will review your changes or assign them to a senior contributor for peer review.
   * The reviewer will check the code, commit messages, and CI results.
   * All review discussions must be resolved before approval.

6. After approval, a CI administrator will merge the pull request.
   * CI will run again on the updated `develop` branch.
   * The source branch will be deleted after the merge.

## Reporting Bugs

Please report software bugs or security issues through the [GitHub Issue Tracker](https://github.com/openairinterface/oai-cn5g-fed/issues).

Use the appropriate labels when creating an issue. If you are unsure whether your report is a bug, start a discussion through the [mailing lists](https://github.com/duranta-project/openairinterface5g/wiki/MailingList).

If required, the OAI team will create an issue on your behalf.

When reporting an issue, please include:

* A clear description of the problem
* Expected behavior — what you expected to happen
* Observed behavior — what actually happened
* Steps to reproduce the issue, including commands, configuration files, or environment details when applicable
* Logs or command outputs using bullet points and code blocks to make the information easier to review
