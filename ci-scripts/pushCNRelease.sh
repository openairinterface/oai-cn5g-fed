#!/bin/bash
# SPDX-License-Identifier: MIT

# SCRIPT USAGE: ./pushCNRelease.sh amf v2.1.10 openairinterface

# 1. RELEASE TAG
VERSION=$2 # This tag will be pushed to DockerHub

# 2. DOCKER HUB ACCOUNT AND REGISTRY URL
DH_Account="oaisoftwarealliance"
REGISTRY_URL='gracehopper3-oai.sboai.cs.eurecom.fr'

# 3. GET THE LATEST COMMIT_SHA OF develop BRANCH FOR THE CORE NETWORK FUNCTION FROM GITHUB
NF=$1
GH_ORG=$3
BASE_API_URL="https://api.github.com/repos"
BRANCH="develop"
REPO="oai-cn5g-$NF"

## 3.1 Construct API URL for the develop branch
API_URL="$BASE_API_URL/$GH_ORG/$REPO/branches/$BRANCH"

## 3.2 Fetch latest commit SHA using GitHub API (private repos require GH_TOKEN)
LATEST_COMMIT=$(curl -s -H "Authorization: Bearer $GH_TOKEN" "$API_URL" | jq -r '.commit.sha')

## 3.3 Get short 8-character commit SHA
SHORT_COMMIT=${LATEST_COMMIT:0:8} # Example: c054106e

echo "Latest short commit SHA: $SHORT_COMMIT of the Repository: $REPO and the Branch: $BRANCH"

# 4. TAG AND PUSH THE IMAGE TO DOCKER HUB
# Authenticate with DockerHub and the private Docker registry before pushing the image

REGISTRY_REPO="oai-$NF"

docker rmi "$REGISTRY_URL"/"$REGISTRY_REPO":"$BRANCH"-"$SHORT_COMMIT" || true
docker buildx imagetools create -t "$DH_Account"/"$REGISTRY_REPO":"$VERSION" "$REGISTRY_URL"/"$REGISTRY_REPO":"$BRANCH"-"$SHORT_COMMIT"

# Log out from DockerHub and the private Docker registry
