#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <table.qza> <tree.qza> <metadata.tsv> <output_dir> <sampling_depth>"
    exit 1
fi

TABLE=$1
TREE=$2
METADATA=$3
OUTDIR=$4
DEPTH=$5

command -v qiime >/dev/null 2>&1 || {
    echo "Error: qiime not found."
    exit 1
}

[[ -f "$TABLE" ]] || { echo "Error: $TABLE not found."; exit 1; }
[[ -f "$TREE" ]] || { echo "Error: $TREE not found."; exit 1; }
[[ -f "$METADATA" ]] || { echo "Error: $METADATA not found."; exit 1; }

[[ "$DEPTH" =~ ^[0-9]+$ ]] || {
    echo "Error: sampling depth must be an integer."
    exit 1
}

mkdir -p "$OUTDIR"

qiime diversity core-metrics-phylogenetic \
    --i-table "$TABLE" \
    --i-phylogeny "$TREE" \
    --m-metadata-file "$METADATA" \
    --p-sampling-depth "$DEPTH" \
    --output-dir "$OUTDIR"