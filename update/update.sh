#!/bin/bash

set -e

# Input variables
LOCAL_NCBI_DIR=$(pwd)/ncbi
PREVIOUS_UTA_VERSION=uta_20210129b

# Download files for SeqRepo and UTA updates
mkdir -p $LOCAL_NCBI_DIR
docker build --file Dockerfile.download --tag ncbi:latest --progress plain .
docker run -it --mount type=bind,source=$LOCAL_NCBI_DIR,target=/data/ncbi ncbi:latest

# Update SeqRepo
# docker run seqrepo:latest -- seqrepo load

# Update UTA, which depends on an updated SeqRepo
previous_uta_version=$PREVIOUS_UTA_VERSION docker compose -f docker-compose.uta.yml run --rm uta-update

# Stop dependency containers
docker compose -f docker-compose.uta.yml down
