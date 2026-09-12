#!/usr/bin/env Rscript

library(compositions)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 2)
    stop("Usage: script.R input.tsv output.tsv")

input_file  <- args[1]
output_file <- args[2]

if (!file.exists(input_file))
    stop("Input file not found.")

counts <- read.delim(
    input_file,
    row.names = 1,
    check.names = FALSE
)

counts <- data.matrix(t(counts))

counts[counts == 0] <- 1

if (any(counts <= 0))
    stop("Counts must be positive.")

clr_table <- t(as.matrix(clr(acomp(counts))))

write.table(
    clr_table,
    output_file,
    sep = "\t",
    quote = FALSE,
    col.names = NA
)