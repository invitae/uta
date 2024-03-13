#!/bin/bash

set -e

# Input variables
LOCAL_NCBI_DIR=$(pwd)/ncbi
PREVIOUS_UTA_VERSION=uta_20210129b

# 1. Download files for SeqRepo and UTA updates
# Input: N/A
# Output: LOCAL_NCBI_DIR populated with downloaded files
mkdir -p $LOCAL_NCBI_DIR
docker build --file Dockerfile.download --tag ncbi:latest --progress plain .
# docker run -it --mount type=bind,source=$LOCAL_NCBI_DIR,target=/data/ncbi ncbi:latest

# 2. Update SeqRepo
# Input: TBD
# Output: TBD
# docker run seqrepo:latest -- seqrepo load

# 3. Update UTA, which depends on an updated SeqRepo
# Input: LOCAL_NCBI_DIR populated with downloaded files
# Input: PREVIOUS_UTA_VERSION
# Output: Postgres dump of updated database
docker build --file ../Dockerfile --tag uta-update:latest ..
docker build --file ../misc/docker/uta.dockerfile --tag uta:$PREVIOUS_UTA_VERSION --build-arg uta_version=$PREVIOUS_UTA_VERSION ../misc/docker
previous_uta_version=$PREVIOUS_UTA_VERSION docker compose -f docker-compose.uta.yml run --rm uta-update

# Stop dependency containers
docker compose -f docker-compose.uta.yml down
