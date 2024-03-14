#!/bin/bash

if [ "$#" -lt 1 ]
then
    echo "error: too few arguments, you provided $#, 1 required"
    echo "usage: run_uta_build_gene.sh <source_uta_v>"
    exit 1
fi
source_uta_v=$1

set -euxo pipefail

# set local variables and create working directories
loading_schema="uta_1_1"
loading_dir="/temp/loading"
dumps_dir="/temp/dumps"
logs_dir="/temp/logs"
for d in "$loading_dir" "$dumps_dir" "$logs_dir";
  do mkdir -p "$d"
done

## Drop loading schema, and recreate
etc/scripts/delete-schema.sh $loading_schema
etc/scripts/create-new-schema.sh "$source_uta_v" "$loading_schema"

### extract meta data
# genes
sbin/ncbi-parse-geneinfo /temp/gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz | \
  gzip -c > "$loading_dir/genes.geneinfo.gz" 2>&1 | tee "$logs_dir/ncbi-parse-geneinfo.log"

# transcript protein associations
sbin/ncbi-parse-gene2refseq /temp/gene/DATA/gene2accession.gz | gzip -c > "$loading_dir/assocacs.gz" 2>&1 | \
  tee "$logs_dir/ncbi-fetch-assoc-acs"

# parse transcript info from GBFF input files
GBFF_files=$(ls /temp/refseq/H_sapiens/mRNA_Prot/human.*.rna.gbff.gz)
sbin/ncbi-parse-gbff "$GBFF_files" | gzip -c > "$loading_dir/gbff.txinfo.gz" 2>&1 | \
  tee "$logs_dir/ncbi-parse-gbff.log"

# parse genomic gff to get exon alignments
GFF_dir="/temp/genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/"
GFF_files=$(find "$GFF_dir" -type f -name "*.gff.gz")
if [ -z "$GFF_files" ]
then
    echo "error: no GFF files found in $GFF_dir"
    exit 1
fi
python sbin/ncbi_parse_genomic_gff.py "$GFF_files" | gzip -c > "$loading_dir/ncbi-gff.exonset.gz" 2>&1 | \
  tee "$logs_dir/ncbi_parse_genomic_gff.log"

### update the uta database
# genes
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-geneinfo "$loading_dir/genes.geneinfo.gz" 2>&1 | \
  tee "$logs_dir/load-geneinfo.log"

# transcript info
#uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-txinfo "$loading_dir/gbff.txinfo.gz" 2>&1 | \
#  tee "$logs_dir/load-txinfo.log"

# exon alignments
uta --conf=etc/global.conf --conf=etc/uta_dev@localhost.conf load-exonset "$loading_dir/ncbi-gff.exonset.gz" 2>&1 | \
  tee "$logs_dir/load-exonset.log"

### psql_dump
pg_dump -U uta_admin -h localhost -d uta -t "$loading_schema.gene" | gzip -c > "$dumps_dir/uta.pgd.gz"
