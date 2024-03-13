#!/bin/bash

if [ "$#" -lt 2 ]
then
    echo "error: too few arguments, you provided $#, 2 required"
    echo "usage: delete-schema.sh <db_host> <source_uta_v>"
    exit 1
fi

set -euxo pipefail

db_host="$1"
source_uta_v="$2"

psql -h "$db_host" -U uta_admin -d uta -c "DROP SCHEMA IF EXISTS $source_uta_v CASCADE"
