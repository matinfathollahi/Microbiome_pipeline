#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <R1.fastq> <R2.fastq> <threads>"
    exit 1
fi

FASTQ1="$1"
FASTQ2="$2"
THREADS="$3"

command -v pigz >/dev/null 2>&1 || {
    echo "ERROR: pigz is not installed."
    exit 1
}

[[ "$THREADS" =~ ^[1-9][0-9]*$ ]] || {
    echo "ERROR: THREADS must be a positive integer."
    exit 1
}

for FILE in "$FASTQ1" "$FASTQ2"; do

    [ -f "$FILE" ] || {
        echo "ERROR: File not found: $FILE"
        exit 1
    }

    [ -s "$FILE" ] || {
        echo "ERROR: File is empty: $FILE"
        exit 1
    }

    [[ "$FILE" != *.gz ]] || {
        echo "ERROR: File is already compressed: $FILE"
        exit 1
    }

    OUTPUT="${FILE}.gz"
    TMP="${OUTPUT}.tmp"

    echo "Compressing $(basename "$FILE")..."

    rm -f "$TMP"

    pigz \
        -c \
        -p "$THREADS" \
        "$FILE" \
        > "$TMP"

    [ -s "$TMP" ] || {
        echo "ERROR: Compression produced an empty file: $TMP"
        rm -f "$TMP"
        exit 1
    }

    pigz -t "$TMP" || {
        echo "ERROR: Gzip integrity check failed: $TMP"
        rm -f "$TMP"
        exit 1
    }

    mv -f "$TMP" "$OUTPUT"

    echo "Created: $OUTPUT"

done

echo "Compression completed successfully."