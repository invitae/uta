#!/bin/bash

set -e

TOP_LEVEL_DIR=$1

FILE=gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
mkdir -p $TOP_LEVEL_DIR/gene/DATA/GENE_INFO/Mammalia
curl https://ftp.ncbi.nih.gov/$FILE -o $TOP_LEVEL_DIR/$FILE
ls $TOP_LEVEL_DIR/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz
