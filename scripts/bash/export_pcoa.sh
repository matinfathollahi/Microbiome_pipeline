#!/usr/bin/env bash

set -euo pipefail

# بررسی تعداد آرگومان‌ها
if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <input.qza|input.qzv> <output_directory>"
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

# بررسی نصب بودن QIIME 2
if ! command -v qiime >/dev/null 2>&1; then
    echo "Error: 'qiime' command not found."
    echo "Please activate your QIIME 2 environment first."
    exit 1
fi

# بررسی وجود فایل ورودی
if [[ ! -e "$INPUT" ]]; then
    echo "Error: Input file does not exist: $INPUT"
    exit 1
fi

# ایجاد پوشه خروجی
mkdir -p "$OUTPUT"

echo "Exporting '$INPUT' to '$OUTPUT'..."

qiime tools export \
    --input-path "$INPUT" \
    --output-path "$OUTPUT"

echo "Export completed successfully."