#!/bin/bash
#/*
# * Licensed to the OpenAirInterface (OAI) Software Alliance under one or more
# * contributor license agreements.  See the NOTICE file distributed with
# * this work for additional information regarding copyright ownership.
# * The OpenAirInterface Software Alliance licenses this file to You under
# * the OAI Public License, Version 1.1  (the "License"); you may not use this file
# * except in compliance with the License.
# * You may obtain a copy of the License at
# *
# *      http://www.openairinterface.org/?page_id=698
# *
# * Unless required by applicable law or agreed to in writing, software
# * distributed under the License is distributed on an "AS IS" BASIS,
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# * See the License for the specific language governing permissions and
# * limitations under the License.
# *-------------------------------------------------------------------------------
# * For more information about the OpenAirInterface (OAI) Software Alliance:
# *      contact@openairinterface.org
# */

declare -A COMPONENTS=(
  [nrf]="oai-nrf"
  [amf]="oai-amf"
  [smf]="oai-smf"
  [upf]="oai-upf"
  [ausf]="oai-ausf"
  [udm]="oai-udm"
  [udr]="oai-udr"
  [upf-vpp]="oai-upf-vpp"
  [nssf]="oai-nssf"
  [nef]="oai-nef"
  [pcf]="oai-pcf"
  [lmf]="oai-lmf"
)

# Detect current branch from the main repo
DEFAULT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'master')"
COMMON_BRANCH=""
declare -A BRANCHES
verbose=0
doDefault=1

# --------------------------------------------------------------------------
# Helper Functions
# --------------------------------------------------------------------------

usage() {
  cat <<EOF
OpenAir-CN Components Synchronization Script
--------------------------------------------
Synchronizes all OAI CN5G components to specified branches.

Usage:
  $0 [OPTIONS]

Options:
  --branch <branch>               Set a common branch for all components.
  --<component>-branch <branch>   Override branch for a specific component.
                                  Available: ${!COMPONENTS[@]}
  --verbose                       Enable detailed output.
  -h, --help                      Show this help message.

Examples:
  $0 --branch develop
  $0 --branch develop --smf-branch feature/smf-improvement
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
    --branch)
      COMMON_BRANCH="$2"
      doDefault=0
      shift 2
      ;;
    --*-branch)
      comp="${key#--}"; comp="${comp%-branch}"
      if [[ -n "${COMPONENTS[$comp]:-}" ]]; then
        BRANCHES["$comp"]="$2"
        doDefault=0
        shift 2
      else
        error "Unknown component '$comp'. Valid components: ${!COMPONENTS[@]}"
      fi
      ;;
    *)
      error "Unknown option: $key"
      ;;
  esac
done

# --------------------------------------------------------------------------
# Apply default/common branches
# --------------------------------------------------------------------------

for comp in "${!COMPONENTS[@]}"; do
  if [[ -n "$COMMON_BRANCH" ]]; then
    BRANCHES["$comp"]="${BRANCHES[$comp]:-$COMMON_BRANCH}"
  else
    BRANCHES["$comp"]="${BRANCHES[$comp]:-$DEFAULT_BRANCH}"
  fi
done

# --------------------------------------------------------------------------
# Print Summary
# --------------------------------------------------------------------------

echo "---------------------------------------------------------"
echo "Detected branch of fed repository : ${DEFAULT_BRANCH}"
[[ -n "$COMMON_BRANCH" ]] && echo "Using common branch for all NFs    : ${COMMON_BRANCH}"
for comp in "${!COMPONENTS[@]}"; do
  printf "OAI-%-8s component branch : %s\n" "$(echo "$comp" | tr '[:lower:]' '[:upper:]')" "${BRANCHES[$comp]}"
done
echo "---------------------------------------------------------"

# --------------------------------------------------------------------------
# Git Submodule Initialization
# --------------------------------------------------------------------------

log "Cleaning existing submodules..."
run_git "git submodule deinit --force ."
run_git "git submodule update --init --recursive"

# --------------------------------------------------------------------------
# Synchronize Each Component
# --------------------------------------------------------------------------

if [[ $doDefault -eq 1 ]]; then
  log "No branches specified — cleaning only."
  run_git "git submodule foreach 'git clean -x -d -ff'"
  exit 0
fi

for comp in "${!COMPONENTS[@]}"; do
  comp_dir="component/${COMPONENTS[$comp]}"
  branch="${BRANCHES[$comp]}"

  git ls-remote --exit-code origin "refs/heads/${branch}" > /dev/null 2>&1
  ret_code=$?
  # Check if branch exists remotely
  if [[ $ret_code != 0 ]]; then
    error "Branch '${branch}' does not exist on remote 'origin' for component '${comp}'."
  fi

  pushd "$comp_dir" >/dev/null

  log "Fetching branches for ${comp}..."
  run_git "git fetch --prune"

  log "Checking out '${branch}' for ${comp}..."
  run_git "git branch -D '${branch}' || true"
  run_git "git checkout -B '${branch}' 'origin/${branch}'"
  run_git "git submodule update --init --recursive"
  run_git "git clean -x -d -ff"

  popd >/dev/null
done

log "All components successfully synchronized to existing branches."
