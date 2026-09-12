library(DESeq2)
library(readr)

#-----------------------------
# Read command line arguments
#-----------------------------
args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
    stop("Usage: Rscript deseq2.R counts.txt metadata.txt output_directory")
}

table_file <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

#-----------------------------
# Check input files
#-----------------------------
if (!file.exists(table_file)) {
    stop("Count table not found.")
}

if (!file.exists(metadata_file)) {
    stop("Metadata file not found.")
}

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

#-----------------------------
# Read input files
#-----------------------------
counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE
)

metadata <- read.delim(
    metadata_file,
    row.names = 1,
    check.names = FALSE
)


#-----------------------------
# Check missing values
#-----------------------------
if (any(is.na(counts))) {
    stop("Count table contains missing values (NA).")
}

if (any(is.na(metadata))) {
    stop("Metadata contains missing values (NA).")
}

#-----------------------------
# Check sample names
#-----------------------------
missing_samples <- setdiff(colnames(counts), rownames(metadata))

if (length(missing_samples) > 0) {
    stop(
        paste(
            "Samples missing in metadata:",
            paste(missing_samples, collapse = ", ")
        )
    )
}

metadata <- metadata[colnames(counts), , drop = FALSE]

stopifnot(all(colnames(counts) == rownames(metadata)))

#-----------------------------
# Check Group column
#-----------------------------
if (!"Group" %in% colnames(metadata)) {
    stop("Metadata must contain a column named 'Group'.")
}



#-----------------------------
# Experimental design
#-----------------------------
metadata$Group <- factor(metadata$Group)

# Check number of groups
if (nlevels(metadata$Group) < 2) {
    stop("At least two groups are required for differential expression analysis.")
}

# Optional:
# metadata$Group <- relevel(metadata$Group, ref = "Control")

#-----------------------------
# Create DESeq2 object
#-----------------------------
dds <- DESeqDataSetFromMatrix(
    countData = counts,
    colData = metadata,
    design = ~ Group
)

#-----------------------------
# Filter low-count genes
# Keep genes with at least 10 counts
# in two or more samples
#-----------------------------
dds <- dds[
    rowSums(counts(dds) >= 10) >= 2,
]

#-----------------------------
# Differential expression
#-----------------------------
dds <- DESeq(dds)

# For two groups
res <- lfcShrink(
    dds,
    coef = 2,
    type = "apeglm"
)

# Example for specific comparison:
# res <- results(dds,
#                contrast = c("Group",
#                             "Treatment",
#                             "Control"))

#-----------------------------
# Sort results
#-----------------------------
res <- res[order(res$padj, na.last = TRUE), ]

#-----------------------------
# Save DE results
#-----------------------------
res_df <- as.data.frame(res)
res_df$Gene <- rownames(res_df)

res_df <- res_df[
    ,
    c(
        "Gene",
        "baseMean",
        "log2FoldChange",
        "lfcSE",
        "stat",
        "pvalue",
        "padj"
    )
]

write.csv(
    res_df,
    file.path(output_dir, "DESeq2_results.csv"),
    row.names = FALSE
)


# Save complete DESeq2 results
res_full <- as.data.frame(res)
res_full$Gene <- rownames(res_full)

write.csv(
    res_full,
    file.path(output_dir, "DESeq2_results_full.csv"),
    row.names = FALSE
)

#-----------------------------
# Save normalized counts
#-----------------------------
norm_counts <- counts(
    dds,
    normalized = TRUE
)

write.csv(
    norm_counts,
    file.path(output_dir, "Normalized_counts.csv")
)

#-----------------------------
# Save variance stabilized counts
#-----------------------------
vsd <- vst(dds, blind = FALSE)

write.csv(
    assay(vsd),
    file.path(output_dir, "VST_counts.csv")
)

cat("DESeq2 analysis completed successfully.\n")