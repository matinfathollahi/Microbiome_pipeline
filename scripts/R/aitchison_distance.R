args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
    stop("Usage: Rscript script.R input.txt output.txt")
}

input_file <- args[1]
output_file <- args[2]

if (!file.exists(input_file)) {
    stop("Input file not found.")
}

clr <- read.delim(
    input_file,
    row.names = 1,
    check.names = FALSE
)

clr <- as.matrix(clr)
storage.mode(clr) <- "numeric"

if (any(is.na(clr))) {
    stop("Missing values detected.")
}

clr <- t(clr)

aitchison <- as.matrix(
    dist(clr, method = "euclidean")
)

write.table(
    aitchison,
    output_file,
    sep = "\t",
    quote = FALSE,
    col.names = NA
)