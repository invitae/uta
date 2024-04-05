#!/bin/bash

# source_uta_v is the UTA version before the update.
# ncbi_dir is where the script looks for NCBI data files.
# working_dir stores intermediate data files and the final database dump.
# log_dir stores log files.

# Note that the uta loading code uses the seqrepo location defined in the conf files, under [sequences].seqrepo.

set -euxo pipefail

source_uta_v=$1
ncbi_dir=$2
working_dir=$3
log_dir=$4

if [ -z "$source_uta_v" ] || [ -z "$ncbi_dir" ] || [ -z "$working_dir" ] || [ -z "$log_dir" ]
then
    echo 'Usage: run-uta-build.sh <source_uta_v> <ncbi_dir> <working_dir> <log_dir>'
    exit 1
fi

# set local variables and create working directories
loading_uta_v="uta_1_1"
mkdir -p "$log_dir"

## Drop loading schema, and recreate
etc/scripts/delete-schema.sh "$loading_uta_v"
etc/scripts/create-new-schema.sh "$source_uta_v" "$loading_uta_v"

# Filter out columns from assocacs file.
sbin/assoc-acs-merge "$working_dir/assocacs.gz" | gzip -c > "$working_dir/assoc-ac.gz" 2>&1 | \
    tee "$log_dir/assoc-acs-merge.log"

# Load genes into gene table.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo "$working_dir/geneinfo.gz" 2>&1 | \
    tee "$log_dir/load-geneinfo.log"

# Load accessions into associated_accessions table.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-assoc-ac "$working_dir/assoc-ac.gz" 2>&1 | \
    tee "$log_dir/load-assoc-ac.log"

# Load transcript info into transcript and exon_set tables.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-txinfo "$working_dir/txinfo.gz" 2>&1 | \
    tee "$log_dir/load-txinfo.log"

# Load exon sets into into exon_set and exon tables.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-exonset "$working_dir/exonsets.gz" 2>&1 | \
    tee "$log_dir/load-exonsets.log"

# Create cigar strings for all rows in tx_alt_exon_pairs_v view and update exon_aln table.
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf align-exons 2>&1 | \
    tee "$log_dir/align-exons.log"

# Load seqinfo?

### run diff
sbin/uta-diff "$source_uta_v" "$loading_uta_v"

### psql_dump
pg_dump -U uta_admin -h localhost -d uta -t "$loading_uta_v.gene" | gzip -c > "$working_dir/uta.pgd.gz"
