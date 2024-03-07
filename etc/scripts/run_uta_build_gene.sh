#!/bin/bash

if [ "$#" -lt 1 ]
then
    echo "error: too few arguments, you provided $#, 1 required"
    echo "usage: run_uta_build_gene.sh <source_uta_v>"
    exit 1
fi
source_uta_v=$1

set -euxo pipefail

loading_schema="uta_1_1"
loading_dir="/temp/loading"
dumps_dir="/temp/dumps"
mkdir -p "$loading_dir"
mkdir -p "$dumps_dir"

# Drop loading schema, and recreate
etc/scripts/delete-schema.sh $loading_schema
etc/scripts/create-new-schema.sh "$source_uta_v" "$loading_schema"

## extract meta data
sbin/ncbi-parse-geneinfo /temp/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | \
 gzip -c > "$loading_dir/genes.geneinfo.gz"

## update the uta database
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo "$loading_dir/genes.geneinfo.gz"

## psql_dump
pg_dump -U uta_admin -h localhost -d uta -t "$loading_schema.gene" | gzip -c > "$dumps_dir/uta.pgd.gz"
