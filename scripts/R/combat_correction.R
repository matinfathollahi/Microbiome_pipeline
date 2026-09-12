#!/usr/bin/env Rscript

library(sva)

############################################################
# Read command-line arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 5) {
    stop(
        "Usage: Rscript combat.R <expression_table> <metadata> <batch_variable> <group_variable> <output_file>"
    )
}

table_file     <- args[1]
metadata_file  <- args[2]
batch_variable <- args[3]
group_variable <- args[4]
output_file    <- args[5]

############################################################
# Read input files
############################################################

expr <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE
)

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

############################################################
# Check required columns
############################################################

if (!("SampleID" %in% colnames(metadata))) {
    stop("Column 'SampleID' not found in metadata.")
}

if (!(batch_variable %in% colnames(metadata))) {
    stop(sprintf("Batch variable '%s' not found in metadata.", batch_variable))
}

if (!(group_variable %in% colnames(metadata))) {
    stop(sprintf("Group variable '%s' not found in metadata.", group_variable))
}

############################################################
# Match metadata to expression matrix
############################################################

idx <- match(colnames(expr), metadata$SampleID)

if (any(is.na(idx))) {
    missing_samples <- colnames(expr)[is.na(idx)]
    stop(
        paste(
            "The following samples are missing from metadata:",
            paste(missing_samples, collapse = ", ")
        )
    )
}

metadata <- metadata[idx, ]

stopifnot(identical(colnames(expr), metadata$SampleID))

############################################################
# Convert expression matrix to numeric
############################################################

expr <- data.matrix(expr)

############################################################
# Batch variable
############################################################

batch <- factor(metadata[[batch_variable]])

if (any(is.na(batch))) {
    stop("Batch variable contains missing values.")
}

if (length(levels(batch)) < 2) {
    stop("ComBat requires at least two batches.")
}

batch_sizes <- table(batch)

if (any(batch_sizes < 2)) {
    warning(
        paste(
            "Some batches contain fewer than two samples:",
            paste(names(batch_sizes)[batch_sizes < 2], collapse = ", ")
        )
    )
}

############################################################
# Design matrix
############################################################

mod <- model.matrix(
    as.formula(
        paste("~", group_variable)
    ),
    data = metadata
)

############################################################
# Run ComBat
############################################################

combat_table <- ComBat(
    dat = expr,
    batch = batch,
    mod = mod,
    par.prior = TRUE,
    prior.plots = FALSE
)

############################################################
# Write output
############################################################

write.table(
    combat_table,
    file = output_file,
    sep = "\t",
    quote = FALSE,
    col.names = NA
)

cat("ComBat completed successfully.\n")
cat("Output written to:", output_file, "\n")