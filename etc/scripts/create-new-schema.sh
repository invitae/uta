#!/bin/bash

if [ "$#" -lt 3 ]
then
    echo "error: too few arguments, you provided $#, 3 required"
    echo "usage: create-new-schema.sh <db_host> <source_uta_v> <dest_uta_v>"
    exit 1
fi

set -euxo pipefail

db_host="$1"
source_uta_v="$2"
dest_uta_v="$3"
dumps_dir=/temp/dumps
mkdir -p $dumps_dir

# dump current version
pg_dump -U uta_admin -h "$db_host" -d uta -n "$source_uta_v" | \
    gzip -c > $dumps_dir/"$source_uta_v".pgd.gz

# create new schema
gzip -cdq $dumps_dir/"$source_uta_v".pgd.gz | \
    sbin/pg-dump-schema-rename "$source_uta_v" "$dest_uta_v" | \
    psql -U uta_admin -h "$db_host" -d uta -aeE
