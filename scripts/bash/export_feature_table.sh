#!/usr/bin/env bash

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input.qza> <output_directory>"
    exit 1
fi

INPUT="$1"
OUTDIR="$2"

if ! command -v qiime >/dev/null 2>&1; then
    echo "Error: qiime command not found."
    exit 1
fi

if ! command -v biom >/dev/null 2>&1; then
    echo "Error: biom command not found."
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "Error: Input file '$INPUT' does not exist."
    exit 1
fi

mkdir -p "$OUTDIR"

echo "Exporting QIIME2 feature table..."

qiime tools export \
    --input-path "$INPUT" \
    --output-path "$OUTDIR"

BIOM_FILE="$OUTDIR/feature-table.biom"
RAW_TSV="$OUTDIR/feature-table.raw.tsv"
TSV_FILE="$OUTDIR/feature-table.tsv"

if [[ ! -f "$BIOM_FILE" ]]; then
    echo "Error: feature-table.biom was not created."
    exit 1
fi

echo "Converting BIOM to TSV..."

biom convert \
    -i "$BIOM_FILE" \
    -o "$RAW_TSV" \
    --to-tsv

if [[ ! -f "$RAW_TSV" ]]; then
    echo "Error: temporary TSV was not created."
    exit 1
fi


# ----------------------------------------
# Clean BIOM TSV header
# ----------------------------------------

echo "Cleaning BIOM TSV header..."

awk '
BEGIN {
    FS = OFS = "\t"
}

# Remove BIOM comment line
/^# Constructed from biom file/ {
    next
}

# Normalize first column name
$1 == "#OTU ID" {
    $1 = "FeatureID"
}

{
    print
}
' "$RAW_TSV" > "$TSV_FILE"


# Remove temporary raw TSV
rm -f "$RAW_TSV"


# ----------------------------------------
# Validate cleaned TSV
# ----------------------------------------

if [[ ! -s "$TSV_FILE" ]]; then
    echo "Error: feature-table.tsv was not created or is empty."
    exit 1
fi


HEADER="$(head -n 1 "$TSV_FILE" | cut -f1)"

if [[ "$HEADER" != "FeatureID" ]]; then
    echo "Error: unexpected TSV header."
    echo "Expected first column: FeatureID"
    echo "Found: $HEADER"
    exit 1
fi


echo "Feature table export completed successfully."
echo "TSV: $TSV_FILE"