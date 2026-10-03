#!/usr/bin/env bash
# Build the roaming images that are not published on Docker Hub, and pull the
# ones that are, without changing developer checkouts.
set -euo pipefail
export GIT_TERMINAL_PROMPT=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${ROAMING_BUILD_DIR:-$ROOT_DIR/.roaming-build}"
NF_GIT_BASE="${NF_GIT_BASE:-https://github.com/openairinterface}"
IMAGE_TAG="${IMAGE_TAG:-roaming-lbo}"
case "$IMAGE_TAG" in
    roaming-lbo)
        # NFs with roaming changes, plus the SEPP, which has no Docker Hub image
        default_build_nfs="nrf udr udm amf smf sepp"
        default_pull_nfs="ausf upf"
        default_hr_branch="lbo-roaming-support" ;;
    roaming-hr)
        default_build_nfs="nrf udr udm amf smf upf sepp"
        default_pull_nfs="ausf"
        default_hr_branch="hr-roaming-support" ;;
    *)
        default_build_nfs="nrf udr udm amf smf sepp"
        default_pull_nfs="ausf upf"
        default_hr_branch="lbo-roaming-support" ;;
esac
BUILD_NFS="${BUILD_NFS:-$default_build_nfs}"
PULL_NFS="${PULL_NFS:-$default_pull_nfs}"
DOCKERHUB_REPO="${DOCKERHUB_REPO:-oaisoftwarealliance}"
DOCKERHUB_TAG="${DOCKERHUB_TAG:-develop}"
NF_BRANCH="${NF_BRANCH:-lbo-roaming-support}"
SEPP_REPOSITORY="${SEPP_REPOSITORY:-$NF_GIT_BASE/oai-cn5g-sepp.git}"
SEPP_BRANCH="${SEPP_BRANCH:-entrypoint-runtime-config}"
UERANSIM_REPOSITORY="${UERANSIM_REPOSITORY:-https://github.com/rohanrkharade/UERANSIM.git}"
UERANSIM_BRANCH="${UERANSIM_BRANCH:-}"
# The NF build scripts require Ubuntu 24.04; BASE_IMAGE_<NF> overrides one NF.
BASE_IMAGE="${BASE_IMAGE:-ubuntu:noble}"
# Build the NFs from existing local checkouts <LOCAL_SOURCE_ROOT>/oai-cn5g-<nf>
# instead of cloning, e.g. for unpublished work. UERANSIM is still cloned.
LOCAL_SOURCE_ROOT="${LOCAL_SOURCE_ROOT:-}"
TARGETPLATFORM="${TARGETPLATFORM:-linux/amd64}"
BUILD_CPUSET="${BUILD_CPUSET:-}"
mode="${1:-build}"
case "$mode" in
    build|--check|--plan) ;;
    -h|--help)
        cat <<'HELP'
Usage: ./build_roaming_images.sh [--plan|--check]
Default: pull the develop NF images from Docker Hub, validate remote refs, build
the roaming NFs and the SEPP, then build UERANSIM.
--plan: print source/branch/image choices without network access or mutation.
--check: check every remote branch without cloning, pulling, building, or deploying.
IMAGE_TAG=roaming-lbo (default): build NRF, UDR, UDM, AMF, SMF (lbo-roaming-support)
  and SEPP; pull AUSF, UPF.
IMAGE_TAG=roaming-hr: build NRF, UDR, UDM (lbo-roaming-support), AMF, SMF, UPF
  (hr-roaming-support) and SEPP; pull AUSF.
Overrides: BUILD_NFS, PULL_NFS, DOCKERHUB_REPO, DOCKERHUB_TAG (default develop),
NF_GIT_BASE, NF_BRANCH, <NF>_BRANCH (e.g. SMF_BRANCH), SEPP_REPOSITORY,
SEPP_BRANCH (default entrypoint-runtime-config), UERANSIM_REPOSITORY, UERANSIM_BRANCH,
ROAMING_BUILD_DIR, BASE_IMAGE, BASE_IMAGE_<NF>, TARGETPLATFORM,
BUILD_CPUSET (optional CPU set, e.g. 0-3, for a dedicated BuildKit builder that limits
parallel compilation),
LOCAL_SOURCE_ROOT (build local checkouts <root>/oai-cn5g-<nf> as they are).
An unset UERANSIM_BRANCH selects that repository's default branch.
Existing workspace checkouts and Docker volumes are never modified.
HELP
        exit 0 ;;
    *) echo "Unknown option: $mode" >&2; exit 2 ;;
esac
[[ $# -le 1 ]] || { echo 'Only one mode argument is supported' >&2; exit 2; }
read -r -a nfs <<< "$BUILD_NFS"
read -r -a pulls <<< "$PULL_NFS"
components=("${nfs[@]}" ueransim)
declare -A urls branches revisions tags
for nf in "${nfs[@]}"; do
    urls[$nf]="$NF_GIT_BASE/oai-cn5g-$nf.git"
    case $nf in
        amf|smf|upf) default_branch="$default_hr_branch" ;;
        *) default_branch="$NF_BRANCH" ;;
    esac
    branch_var="${nf^^}_BRANCH"
    branches[$nf]="${!branch_var:-$default_branch}"
    tags[$nf]="oai-$nf:$IMAGE_TAG"
done
urls[sepp]="$SEPP_REPOSITORY"; branches[sepp]="$SEPP_BRANCH"
urls[ueransim]="$UERANSIM_REPOSITORY"; branches[ueransim]="$UERANSIM_BRANCH"
tags[ueransim]='ueransim:roaming-lbo'
if [[ -n $LOCAL_SOURCE_ROOT ]]; then
    for nf in "${nfs[@]}"; do urls[$nf]="$LOCAL_SOURCE_ROOT/oai-cn5g-$nf"; branches[$nf]='(local checkout)'; done
fi
for nf in "${pulls[@]}"; do
    printf '%-9s %-65s pull   image=%s\n' "$nf" "Docker Hub" "$DOCKERHUB_REPO/oai-$nf:$DOCKERHUB_TAG"
done
for component in "${components[@]}"; do
    printf '%-9s %-65s branch=%-18s image=%s\n' "$component" "${urls[$component]}" "${branches[$component]:-(remote default)}" "${tags[$component]}"
done
[[ $mode != --plan ]] || exit 0
command -v git >/dev/null
failed=0
for component in "${components[@]}"; do
    if [[ -n $LOCAL_SOURCE_ROOT && $component != ueransim ]]; then
        [[ -d ${urls[$component]} ]] || { echo "ERROR: missing local checkout ${urls[$component]}" >&2; failed=1; continue; }
        revisions[$component]=$(git -C "${urls[$component]}" rev-parse HEAD)
        printf 'Local %s: %s (%s) @ %s%s\n' "$component" "${urls[$component]}" \
            "$(git -C "${urls[$component]}" rev-parse --abbrev-ref HEAD)" "${revisions[$component]}" \
            "$([[ -n $(git -C "${urls[$component]}" status --porcelain --untracked-files=no) ]] && echo ' (with uncommitted changes)')"
        continue
    fi
    branch="${branches[$component]}"
    if [[ -z $branch ]]; then
        if ! listing=$(git ls-remote --symref "${urls[$component]}" HEAD); then
            echo "ERROR: cannot access ${urls[$component]}" >&2; failed=1; continue
        fi
        branch=$(awk '$1=="ref:" && $3=="HEAD" {sub("refs/heads/", "", $2); print $2}' <<< "$listing")
        revision=$(awk '$2=="HEAD" && $1!="ref:" {print $1}' <<< "$listing")
    else
        if ! listing=$(git ls-remote "${urls[$component]}" "refs/heads/$branch"); then
            echo "ERROR: cannot access ${urls[$component]}" >&2; failed=1; continue
        fi
        revision=$(awk 'NR==1 {print $1}' <<< "$listing")
    fi
    if [[ -z $branch || ! $revision =~ ^[0-9a-f]{40}$ ]]; then
        echo "ERROR: $component branch '${branch:-remote default}' is unavailable; no fallback branch will be built." >&2
        failed=1; continue
    fi
    branches[$component]="$branch"; revisions[$component]="$revision"
    printf 'Verified %s: %s @ %s\n' "$component" "$branch" "$revision"
done
[[ $failed == 0 ]] || { echo 'Source validation failed. Publish/provide the requested branches and retry. No images were built.' >&2; exit 1; }
[[ $mode != --check ]] || exit 0
command -v docker >/dev/null
docker info >/dev/null
# BuildKit skips the Dockerfile stages the target does not need (e.g. the SMF
# unit-test stage); the legacy builder builds them all.
docker buildx version >/dev/null 2>&1 || { echo 'docker buildx (BuildKit) is required: install the docker-buildx plugin.' >&2; exit 1; }
build_cmd=(buildx build --load)
if [[ -n $BUILD_CPUSET ]]; then
    # BuildKit has no per-build CPU limit: use a builder container pinned to these CPUs.
    builder="oai-roaming-cpus-${BUILD_CPUSET//[^0-9]/_}"
    docker buildx inspect "$builder" >/dev/null 2>&1 ||
        docker buildx create --name "$builder" --driver docker-container --driver-opt "cpuset-cpus=$BUILD_CPUSET"
    build_cmd+=(--builder "$builder")
fi
run_dir="$BUILD_DIR/runs/$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$BUILD_DIR/sources" "$run_dir"
printf 'component\trepository\tbranch\tcommit\timage\timage_id\n' > "$run_dir/manifest.tsv"
for nf in "${pulls[@]}"; do
    image="$DOCKERHUB_REPO/oai-$nf:$DOCKERHUB_TAG"
    docker pull "$image"
    revision=$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$image" 2>/dev/null || true)
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$nf" "docker.io/$DOCKERHUB_REPO" "$DOCKERHUB_TAG" "${revision:-unknown}" "$image" \
        "$(docker image inspect --format '{{.Id}}' "$image")" >> "$run_dir/manifest.tsv"
done
for component in "${components[@]}"; do
    # UERANSIM is deliberately last: a failed NF build stops the script first.
    # Reuse an image already built from this exact revision, e.g. the LBO NRF
    # and UDR for the HR scenario.
    if [[ $component == ueransim ]]; then repo_name=UERANSIM; else repo_name="oai-cn5g-$component"; fi
    image_name="${tags[$component]%%:*}"
    existing=$(docker images --format '{{.Repository}}:{{.Tag}}' --filter "reference=$image_name" \
        --filter "label=org.opencontainers.image.revision=${revisions[$component]}" | head -n 1)
    if [[ -n $existing && -z $(git -C "${urls[$component]}" status --porcelain --untracked-files=no 2>/dev/null) ]]; then
        echo "Reusing $existing for ${tags[$component]} at ${revisions[$component]}"
        docker tag "$existing" "${tags[$component]}"
        image_id=$(docker image inspect --format '{{.Id}}' "${tags[$component]}")
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$component" "${urls[$component]}" "${branches[$component]}" "${revisions[$component]}" "${tags[$component]}" "$image_id" >> "$run_dir/manifest.tsv"
        continue
    fi
    source_dir="$BUILD_DIR/sources/$repo_name"
    local_source=0
    [[ -n $LOCAL_SOURCE_ROOT && $component != ueransim ]] && local_source=1
    if [[ $local_source == 1 ]]; then
        source_dir="${urls[$component]}"
    elif [[ -e $source_dir ]]; then
        [[ $(git -C "$source_dir" remote get-url origin) == "${urls[$component]}" ]] || { echo "Origin mismatch: $source_dir" >&2; exit 1; }
        [[ -z $(git -C "$source_dir" status --porcelain --untracked-files=all) ]] || { echo "Refusing to replace modified build sources: $source_dir" >&2; exit 1; }
    else
        git init "$source_dir"
        git -C "$source_dir" remote add origin "${urls[$component]}"
    fi
    if [[ $local_source == 0 ]]; then
        git -C "$source_dir" fetch --depth 1 origin "${revisions[$component]}"
        git -C "$source_dir" checkout --detach "${revisions[$component]}"
        git -C "$source_dir" submodule sync --recursive
        git -C "$source_dir" submodule update --init --recursive
    fi
    base_var="BASE_IMAGE_${component^^}"
    args=(--build-arg "TARGETPLATFORM=$TARGETPLATFORM" --build-arg "BASE_IMAGE=${!base_var:-$BASE_IMAGE}"
          --label "org.opencontainers.image.source=${urls[$component]}"
          --label "org.opencontainers.image.revision=${revisions[$component]}"
          --tag "${tags[$component]}")
    if [[ $component == ueransim ]]; then
        dockerfile="$source_dir/Dockerfile"
        [[ -f $source_dir/tools/nr-ue-ping ]] || { echo 'UERANSIM revision must include tools/nr-ue-ping for the automatic traffic test.' >&2; exit 1; }
    else
        dockerfile="$source_dir/docker/Dockerfile.$component.ubuntu"
        args+=(--target "oai-$component")
    fi
    [[ -f $dockerfile ]] || { echo "Missing Dockerfile: $dockerfile" >&2; exit 1; }
    echo "Building $component from ${branches[$component]} @ ${revisions[$component]}"
    docker "${build_cmd[@]}" "${args[@]}" -f "$dockerfile" "$source_dir" 2>&1 | tee "$run_dir/$component-build.log"
    image_id=$(docker image inspect --format '{{.Id}}' "${tags[$component]}")
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$component" "${urls[$component]}" "${branches[$component]}" "${revisions[$component]}" "${tags[$component]}" "$image_id" >> "$run_dir/manifest.tsv"
done
docker run --rm --entrypoint /bin/bash "${tags[ueransim]}" -c 'command -v nr-ue && command -v nr-gnb && command -v nr-cli && command -v nr-ue-ping && command -v ping && command -v timeout'
echo "All images are ready. Manifest: $run_dir/manifest.tsv"
if [[ $IMAGE_TAG == roaming-hr ]]; then
    echo "Deploy: cd '$SCRIPT_DIR' && docker-compose -f docker-compose-basic-nrf-hr-roaming.yaml up -d"
else
    echo "Deploy: cd '$SCRIPT_DIR' && docker-compose -f docker-compose-basic-nrf-lbo-roaming.yaml up -d"
fi
