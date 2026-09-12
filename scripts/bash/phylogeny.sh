#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 5 ]]; then
    echo "Usage: $0 repseq.qza aligned.qza masked.qza tree.qza rooted-tree.qza"
    exit 1
fi

REPSEQ="$1"
ALIGNED="$2"
MASKED="$3"
TREE="$4"
ROOTED="$5"

[[ -f "$REPSEQ" ]] || {
    echo "ERROR: Representative sequences not found: $REPSEQ" >&2
    exit 1
}

mkdir -p "$(dirname "$ALIGNED")"
mkdir -p "$(dirname "$MASKED")"
mkdir -p "$(dirname "$TREE")"
mkdir -p "$(dirname "$ROOTED")"

qiime phylogeny align-to-tree-mafft-fasttree \
    --i-sequences "$REPSEQ" \
    --o-alignment "$ALIGNED" \
    --o-masked-alignment "$MASKED" \
    --o-tree "$TREE" \
    --o-rooted-tree "$ROOTED"

echo "Phylogenetic tree generated successfully."