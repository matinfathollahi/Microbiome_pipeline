args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 3) {
    stop("Usage: Rscript filter.R input.tsv output.tsv prevalence")
}

input <- args[1]
output <- args[2]
prevalence <- as.numeric(args[3])

if (is.na(prevalence) || prevalence < 0 || prevalence > 1) {
    stop("prevalence must be between 0 and 1")
}

counts <- read.delim(
    input,
    row.names = 1,
    check.names = FALSE
)

minimum_samples <- ceiling(prevalence * ncol(counts))

############################################################
# Filter low-prevalence features
############################################################

features_before <- nrow(counts)

counts <- counts[
    rowSums(counts > 0) >= minimum_samples,
    ,
    drop = FALSE
]

features_after <- nrow(counts)

############################################################
# Remove all-zero samples
############################################################

sample_totals <- colSums(counts)

zero_samples <- names(sample_totals)[sample_totals == 0]

if (length(zero_samples) > 0) {
    counts <- counts[
        ,
        !(colnames(counts) %in% zero_samples),
        drop = FALSE
    ]
}

############################################################
# Summary
############################################################

cat("Low-prevalence filtering summary\n")
cat("Features before:", features_before, "\n")
cat("Features after :", features_after, "\n")
cat("Samples before :", length(sample_totals), "\n")
cat("All-zero samples removed:", length(zero_samples), "\n")

if (length(zero_samples) > 0) {
    cat("Removed samples:\n")
    cat(paste(zero_samples, collapse = ", "), "\n")
}

cat("Samples after  :", ncol(counts), "\n")

write.table(
    counts,
    output,
    sep = "\t",
    quote = FALSE,
    col.names = NA
)