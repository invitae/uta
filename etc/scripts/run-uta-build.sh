#!/bin/bash

# source_uta_v is the UTA version before the update.
# seqrepo_data_release is the SeqRepo version before the update.
# ncbi_dir is where the script looks for NCBI data files.
# working_dir stores log files, intermediate data files, and the final database dump.

set -euxo pipefail

source_uta_v=$1
seqrepo_data_release=$2
ncbi_dir=$3
working_dir=$4

if [ -z "$source_uta_v" ] || [ -z "$seqrepo_data_release" ] || [ -z "$ncbi_dir" ] || [ -z "$working_dir" ]
then
    echo 'Usage: run-uta-build.sh <source_uta_v> <seqrepo_data_release> <ncbi_dir> <working_dir>'
    exit 1
fi

# set local variables and create working directories
loading_uta_v="uta_1_1"
loading_dir="$working_dir/loading"
dumps_dir="$working_dir/dumps"
logs_dir="$working_dir/logs"
for d in "$loading_dir" "$dumps_dir" "$logs_dir";
  do mkdir -p "$d"
done

## Drop loading schema, and recreate
etc/scripts/delete-schema.sh "$loading_uta_v"
etc/scripts/create-new-schema.sh "$source_uta_v" "$loading_uta_v"

# Filter out columns from assocacs file.
sbin/assoc-acs-merge "$loading_dir/assocacs.gz" | gzip -c > "$loading_dir/assoc-ac.gz" 2>&1 | \
    tee "$logs_dir/assoc-acs-merge.log"

# Load genes into gene table.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo "$loading_dir/geneinfo.gz" 2>&1 | \
    tee "$logs_dir/load-geneinfo.log"

# Load accessions into associated_accessions table.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-assoc-ac "$loading_dir/assoc-ac.gz" 2>&1 | \
    tee "$logs_dir/load-assoc-ac.log"

# Load transcript info into transcript and exon_set tables.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-txinfo "$loading_dir/txinfo.gz" 2>&1 | \
    tee "$logs_dir/load-txinfo.log"

# Load exon sets into into exon_set and exon tables.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-exonset "$loading_dir/exonsets.gz" 2>&1 | \
    tee "$logs_dir/load-exonsets.log"

# Create cigar strings for all rows in tx_alt_exon_pairs_v view and update exon_aln table.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf align-exons 2>&1 | \
    tee "$logs_dir/align-exons.log"

# Load seqinfo?

### run diff
sbin/uta-diff "$source_uta_v" "$loading_uta_v"

### psql_dump
pg_dump -U uta_admin -h localhost -d uta -t "$loading_uta_v.gene" | gzip -c > "$dumps_dir/uta.pgd.gz"
