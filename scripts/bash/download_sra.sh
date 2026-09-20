#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <ACCESSION> <OUTPUT_DIR>"
    exit 1
fi

command -v prefetch >/dev/null 2>&1 || {
    echo "ERROR: prefetch not found."
    exit 1
}

ACCESSION="$1"
OUTDIR="$2"

mkdir -p "$OUTDIR"

echo "Downloading ${ACCESSION}..."

prefetch \
    "$ACCESSION" \
    --output-directory "$OUTDIR" \


SRA_FILE="${OUTDIR}/${ACCESSION}/${ACCESSION}.sra"

if [ ! -s "$SRA_FILE" ]; then
    echo "ERROR: Download failed for ${ACCESSION}"
    exit 1
fi

echo "Download completed."
echo "File: $SRA_FILE"