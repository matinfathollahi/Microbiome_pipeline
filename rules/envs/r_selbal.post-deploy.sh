#!/usr/bin/env bash
set -euo pipefail

SELBAL_COMMIT="962b714b8bb0c12a291870437c537ef884b06528"
SELBAL_FILE="${PWD}/third_party/r/selbal-${SELBAL_COMMIT}.tar.gz"

echo "Looking for local Selbal source:"
echo "${SELBAL_FILE}"

if [[ ! -f "${SELBAL_FILE}" ]]; then
    echo "ERROR: Local Selbal source was not found:"
    echo "${SELBAL_FILE}"
    exit 1
fi

echo "Installing Selbal from local source..."

R CMD INSTALL "${SELBAL_FILE}"

Rscript --vanilla -e '
if (!requireNamespace("selbal", quietly = TRUE)) {
    stop("Selbal installation failed")
}

cat(
    "Selbal successfully installed. Version:",
    as.character(packageVersion("selbal")),
    "\n"
)
'