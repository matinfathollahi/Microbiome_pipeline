#!/usr/bin/env bash
set -euo pipefail

Rscript --no-environ -e '
Sys.setenv(R_REMOTES_NO_ERRORS_FROM_WARNINGS="false")

if (!requireNamespace("selbal", quietly = TRUE)) {
    remotes::install_github(
        repo = "UVic-omics/selbal",
        ref = "962b714b8bb0c12a291870437c537ef884b06528",
        upgrade = "never"
    )
}

if (!requireNamespace("selbal", quietly = TRUE)) {
    stop("selbal installation failed")
}
'