#!/bin/bash
# SPDX-License-Identifier: MIT

declare -A COMPONENTS=(
  [nrf]="oai-cn5g-nrf"
  [amf]="oai-cn5g-amf"
  [smf]="oai-cn5g-smf"
  [upf]="oai-cn5g-upf"
  [ausf]="oai-cn5g-ausf"
  [udm]="oai-cn5g-udm"
  [udr]="oai-cn5g-udr"
  [nssf]="oai-cn5g-nssf"
  [nef]="oai-cn5g-nef"
  [pcf]="oai-cn5g-pcf"
  [lmf]="oai-cn5g-lmf"
)

# Branch used for every component when none is requested
DEFAULT_BRANCH="develop"
COMMON_BRANCH=""
declare -A BRANCHES
verbose=0
force=0

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

usage() {
  cat <<EOF
OAI CN5G Network Functions Synchronization Script
-------------------------------------------------
Synchronizes the OAI CN5G components to the requested branches.
A component without a branch of its own follows the common branch, which
defaults to '${DEFAULT_BRANCH}', so a bare run puts every component on '${DEFAULT_BRANCH}'.
The components are reset to a pristine state, so local changes and untracked
files inside them are discarded: the script stops if it finds any, unless --force.

Usage:
  $0 [OPTIONS]

Options:
  --branch <branch|tag>           Set a common branch or tag for all components.
                                  Default is '${DEFAULT_BRANCH}'.
  --<component>-branch <branch>   Set the branch or tag of a single component.
                                  Overrides the common branch for it alone.
                                  Available: $(printf '%s\n' "${!COMPONENTS[@]}" | sort | xargs)
  --force                         Discard local changes/untracked files in the components.
  --verbose                       Enable detailed output.
  -h, --help                      Show this help message.

Examples:
  $0                                                    # all on ${DEFAULT_BRANCH}
  $0 --branch v2.1.0                                    # all on tag v2.1.0
  $0 --smf-branch feature/smf-improvement               # SMF there, rest on ${DEFAULT_BRANCH}
  $0 --branch v2.1.0 --smf-branch develop               # SMF on develop, rest on tag v2.1.0
EOF
}

log()   { echo "[INFO] $*"; }
warn()  { echo "[WARN] $*" >&2; }
error() { echo "[ERROR] $*" >&2; exit 1; }

run_git() {
  if [[ $verbose -eq 1 ]]; then
    eval "$*"
  else
    eval "$*" > /dev/null 2>&1
  fi
}

# --------------------------------------------------------------------------
# Parse Arguments
# --------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  key="$1"
  case "$key" in
    -h|--help) usage; exit 0 ;;
    --verbose) verbose=1; shift ;;
    --force) force=1; shift ;;
    --branch)
      [[ -n "${2:-}" ]] || error "Option '$key' requires a branch name."
      COMMON_BRANCH="$2"
      shift 2
      ;;
    --*-branch)
      comp="${key#--}"; comp="${comp%-branch}"
      if [[ -n "${COMPONENTS[$comp]:-}" ]]; then
        [[ -n "${2:-}" ]] || error "Option '$key' requires a branch name."
        BRANCHES["$comp"]="$2"
        shift 2
      else
        error "Unknown component '$comp'. Valid components: $(printf '%s\n' "${!COMPONENTS[@]}" | sort | xargs)"
      fi
      ;;
    *)
      error "Unknown option: $key"
      ;;
  esac
done

# All the git commands below expect the federation repository root
TOP_DIR="$(git rev-parse --show-toplevel)" || error "Not inside a git repository."
cd "$TOP_DIR" || error "Could not enter the repository root '${TOP_DIR}'."

# --------------------------------------------------------------------------
# Apply default/common branches
# --------------------------------------------------------------------------

if [[ -z "$COMMON_BRANCH" ]]; then
  COMMON_BRANCH="$DEFAULT_BRANCH"
  log "No common branch specified — using the default branch '${DEFAULT_BRANCH}'."
fi

# Components without a branch of their own follow the common branch
for comp in "${!COMPONENTS[@]}"; do
  BRANCHES["$comp"]="${BRANCHES[$comp]:-$COMMON_BRANCH}"
done

# --------------------------------------------------------------------------
# Print Summary
# --------------------------------------------------------------------------

echo "---------------------------------------------------------"
echo "Detected branch of fed repository : $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
echo "Common branch (unless overridden) : ${COMMON_BRANCH}"
echo "Components synchronized into      : component/"
for comp in "${!COMPONENTS[@]}"; do
  printf "OAI-CN5G-%-7s component branch : %s\n" "$(echo "$comp" | tr '[:lower:]' '[:upper:]')" "${BRANCHES[$comp]}"
done
echo "---------------------------------------------------------"

# --------------------------------------------------------------------------
# Check the requested branches/tags before modifying anything
# --------------------------------------------------------------------------

missing=()
for comp in "${!COMPONENTS[@]}"; do
  branch="${BRANCHES[$comp]}"
  if ! git ls-remote --exit-code https://github.com/openairinterface/oai-cn5g-"${comp}".git "refs/heads/${branch}" "refs/tags/${branch}" > /dev/null 2>&1; then
    warn "Branch or tag '${branch}' does not exist on remote for component '${comp}'."
    missing+=("$comp")
  fi
done
[[ ${#missing[@]} -eq 0 ]] || error "Nothing was modified. Unknown branch or tag for: ${missing[*]}"

# --------------------------------------------------------------------------
# Check the components for uncommitted work before modifying anything
# --------------------------------------------------------------------------

# The clean-up below discards everything that is not committed in the components
local_changes=()
for comp in "${!COMPONENTS[@]}"; do
  comp_dir="component/${COMPONENTS[$comp]}"
  [[ -d "${comp_dir}/.git" ]] || continue
  [[ -z "$(git -C "$comp_dir" status --porcelain)" ]] || local_changes+=("$comp_dir")
done
if [[ ${#local_changes[@]} -gt 0 ]]; then
  [[ $force -eq 1 ]] || error "Local changes or untracked files in: ${local_changes[*]} — commit or stash them, or pass --force to discard them."
  warn "Discarding local changes and untracked files in: ${local_changes[*]}"
fi

# --------------------------------------------------------------------------
# Synchronize Each Component
# --------------------------------------------------------------------------

# A component that fails is reported at the end, the others are still synchronized
failed=()
synced=()

for comp in "${!COMPONENTS[@]}"; do
  branch="${BRANCHES[$comp]}"
  comp_dir="component/${COMPONENTS[$comp]}"

  # The components are plain clones, so a missing one is cloned on the spot
  if [[ ! -d "${comp_dir}/.git" ]]; then
    log "Cloning ${comp}..."
    # Re-run with --verbose to see why a git command failed
    run_git "git clone 'https://github.com/openairinterface/oai-cn5g-${comp}.git' '${comp_dir}'" \
      || { warn "Could not clone ${comp}."; failed+=("$comp"); continue; }
  fi

  pushd "$comp_dir" >/dev/null \
    || { warn "Could not enter ${comp_dir}."; failed+=("$comp"); continue; }

  log "Fetching branches for ${comp}..."
  run_git "git fetch --prune --tags" \
    || { warn "Could not fetch ${comp}."; failed+=("$comp"); popd >/dev/null; continue; }

  log "Checking out '${branch}' for ${comp}..."
  # A tag has no remote-tracking branch, so it is checked out detached
  # --force discards modified tracked files, which the deinit used to take care of
  if git rev-parse --verify --quiet "origin/${branch}" > /dev/null 2>&1; then
    checkout_cmd="git checkout --force --detach 'origin/${branch}'"
  else
    checkout_cmd="git checkout --force --detach 'refs/tags/${branch}'"
  fi
  run_git "$checkout_cmd" \
    || { warn "Could not check out '${branch}' for ${comp}."; failed+=("$comp"); popd >/dev/null; continue; }
  run_git "git submodule update --init --recursive" \
    || { warn "Could not update the submodules of ${comp}."; failed+=("$comp"); popd >/dev/null; continue; }
  run_git "git clean -x -d -ff" \
    || { warn "Could not clean ${comp}."; failed+=("$comp"); popd >/dev/null; continue; }

  synced+=("$comp")
  popd >/dev/null
done

# The successes are reported first, so a partial run does not look like a total failure
[[ ${#synced[@]} -eq 0 ]] || log "Successfully synchronized: ${synced[*]}"
[[ ${#failed[@]} -eq 0 ]] || error "Failed to synchronize: ${failed[*]}"
