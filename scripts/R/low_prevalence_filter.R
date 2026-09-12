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

counts <- counts[rowSums(counts > 0) >= minimum_samples, ]

write.table(
    counts,
    output,
    sep = "\t",
    quote = FALSE,
    col.names = NA
)