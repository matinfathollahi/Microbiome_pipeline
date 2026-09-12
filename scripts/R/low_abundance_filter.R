args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 3)
    stop("Usage: Rscript filter_counts.R input output min_count")

input <- args[1]
output <- args[2]
min_count <- as.numeric(args[3])

if (!file.exists(input))
    stop("Input file not found.")

counts <- read.delim(
    input,
    row.names = 1,
    check.names = FALSE
)

counts <- as.matrix(counts)
mode(counts) <- "numeric"

counts <- counts[rowSums(counts) >= min_count, ]

write.table(
    counts,
    file = output,
    sep = "\t",
    quote = FALSE,
    col.names = NA
)