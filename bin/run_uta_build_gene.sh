#!/bin/bash

set -euxo pipefail

# set version
uta_v=uta_20210129b

## get the file
rsync --no-motd -HRavP ftp.ncbi.nlm.nih.gov::gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz .

## extract meta data
sbin/ncbi-parse-geneinfo DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | gzip -c > genes.geneinfo.gz

## update the uta database
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo genes.sample.gz

## psql_dump
#pg_dump -U uta_admin -h localhost -d uta -t uta_20210129b.gene | gzip -c > uta.pgd.gz
