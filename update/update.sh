#!/bin/bash

set -e

# Input variables
LOCAL_NCBI_DIR=$(pwd)/ncbi
SEQREPO_VERSION=latest  # 2021-01-29
PREVIOUS_UTA_VERSION=uta_20210129b

# 1. Download files for SeqRepo and UTA updates
# Input: N/A
# Output: LOCAL_NCBI_DIR populated with downloaded files
mkdir -p $LOCAL_NCBI_DIR
docker build --file Dockerfile.download --tag ncbi:latest --progress plain .
docker run -it --mount type=bind,source=$LOCAL_NCBI_DIR,target=/data/ncbi ncbi:latest

# 2. Prepare SeqRepo
# Input: seqrepo version
# Output: a container that has run once and pulled seqrepo data
# Pulling data takes 30 minutes and 13 GB.
docker pull biocommons/seqrepo:$SEQREPO_VERSION
docker run --name seqrepo biocommons/seqrepo:$SEQREPO_VERSION

# 3. Prepare UTA
# Input: uta version
# Output: docker image
# This would also be done automatically as part of the docker compose run,
# but explicitly pulling here for symmetry with seqrepo
docker pull biocommons/uta:$PREVIOUS_UTA_VERSION

# 4. Update UTA and SeqRepo
# Input: LOCAL_NCBI_DIR populated with downloaded files
# Input: PREVIOUS_UTA_VERSION
# Output: Updated SeqRepo (updated in place)
# Output: Updated UTA as a database dump
docker build --file ../Dockerfile --tag uta-update:latest ..
seqrepo_version=$SEQREPO_VERSION previous_uta_version=$PREVIOUS_UTA_VERSION docker compose -f docker-compose.uta.yml run --rm uta-update
docker compose -f docker-compose.uta.yml down

# 5. Publish UTA and SeqRepo
