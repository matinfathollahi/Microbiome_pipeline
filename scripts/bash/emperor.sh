#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <pcoa.qza> <metadata.tsv> <output.qzv>"
    exit 1
fi

command -v qiime >/dev/null 2>&1 || {
    echo "ERROR: qiime command not found."
    exit 1
}

PCOA="$1"
METADATA="$2"
OUTPUT="$3"

[ -f "$PCOA" ] || {
    echo "ERROR: PCoA file not found: $PCOA"
    exit 1
}

[ -f "$METADATA" ] || {
    echo "ERROR: Metadata file not found: $METADATA"
    exit 1
}

mkdir -p "$(dirname "$OUTPUT")"

echo "Generating Emperor visualization..."

qiime emperor plot \
    --i-pcoa "$PCOA" \
    --m-metadata-file "$METADATA" \
    --o-visualization "$OUTPUT"

echo "Done."
echo "Output saved to: $OUTPUT"