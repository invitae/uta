#!/bin/bash

set -e

FILE_DIR=$1
FILES=(
    'gene/DATA/GENE_INFO/Mammalia/Homo_sapiens.gene_info.gz'
    'gene/DATA/gene2accession.gz'
    'refseq/H_sapiens/mRNA_Prot/human.1.rna.gbff.gz'
)

for FILE in "${FILES[@]}"
do
    mkdir -p "$(dirname $FILE_DIR/$FILE)"
    curl "https://ftp.ncbi.nih.gov/$FILE" -o "$FILE_DIR/$FILE"
done
