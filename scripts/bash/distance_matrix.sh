#!/usr/bin/env bash

set -euo pipefail

########################################
# Check arguments
########################################
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <feature-table.qza> <rooted-tree.qza> <output_dir>"
    exit 1
fi

TABLE="$1"
TREE="$2"
OUTDIR="$3"

########################################
# Check dependencies
########################################
command -v qiime >/dev/null 2>&1 || {
    echo "Error: QIIME2 is not available in PATH."
    exit 1
}

########################################
# Check input files
########################################
[ -f "$TABLE" ] || {
    echo "Error: Feature table not found:"
    echo "  $TABLE"
    exit 1
}

[ -f "$TREE" ] || {
    echo "Error: Rooted tree not found:"
    echo "  $TREE"
    exit 1
}

########################################
# Create output directory
########################################
mkdir -p "$OUTDIR"

echo "========================================"
echo "Calculating beta diversity metrics..."
echo "========================================"

########################################
# Bray-Curtis
########################################
echo "Bray-Curtis..."

qiime diversity beta \
    --i-table "$TABLE" \
    --p-metric braycurtis \
    --o-distance-matrix "$OUTDIR/bray_distance.qza"

########################################
# Jaccard
########################################
echo "Jaccard..."

qiime diversity beta \
    --i-table "$TABLE" \
    --p-metric jaccard \
    --o-distance-matrix "$OUTDIR/jaccard_distance.qza"

########################################
# Weighted UniFrac
########################################
echo "Weighted UniFrac..."

qiime diversity beta-phylogenetic \
    --i-table "$TABLE" \
    --i-phylogeny "$TREE" \
    --p-metric weighted_unifrac \
    --o-distance-matrix "$OUTDIR/weighted_unifrac_distance.qza"

########################################
# Unweighted UniFrac
########################################
echo "Unweighted UniFrac..."

qiime diversity beta-phylogenetic \
    --i-table "$TABLE" \
    --i-phylogeny "$TREE" \
    --p-metric unweighted_unifrac \
    --o-distance-matrix "$OUTDIR/unweighted_unifrac_distance.qza"

echo
echo "Exporting distance matrices..."

########################################
# Export all distance matrices
########################################
for metric in \
    bray \
    jaccard \
    weighted_unifrac \
    unweighted_unifrac
do

    echo "Exporting ${metric}..."

    qiime tools export \
        --input-path "$OUTDIR/${metric}_distance.qza" \
        --output-path "$OUTDIR/$metric"

    TSV="$OUTDIR/$metric/distance-matrix.tsv"

    if [ ! -f "$TSV" ]; then
        echo "Error: Export failed for ${metric}"
        exit 1
    fi

    mv "$TSV" \
       "$OUTDIR/${metric}_distance.tsv"

    rm -rf "$OUTDIR/$metric"

done

echo
echo "========================================"
echo "Beta diversity analysis completed."
echo
echo "Generated files:"
echo "  bray_distance.qza"
echo "  bray_distance.tsv"
echo
echo "  jaccard_distance.qza"
echo "  jaccard_distance.tsv"
echo
echo "  weighted_unifrac_distance.qza"
echo "  weighted_unifrac_distance.tsv"
echo
echo "  unweighted_unifrac_distance.qza"
echo "  unweighted_unifrac_distance.tsv"
echo "========================================"