#!/usr/bin/env Rscript

library(pheatmap)

##############################
## Read command line arguments
##############################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 4) {
    stop(
        "Usage: Rscript Heatmap.R <feature_table> <significant_file> <metadata_file> <output_dir>"
    )
}

feature_table   <- args[1]
significant_file <- args[2]
metadata_file   <- args[3]
output_dir      <- args[4]

##############################
## Check input files
##############################

if (!file.exists(feature_table))
    stop("Feature table not found.")

if (!file.exists(significant_file))
    stop("Significant taxa file not found.")

if (!file.exists(metadata_file))
    stop("Metadata file not found.")

##############################
## Create output directory
##############################

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

##############################
## Read data
##############################

feature <- read.delim(
    feature_table,
    row.names = 1,
    check.names = FALSE
)

sig <- read.delim(
    significant_file,
    check.names = FALSE
)

metadata <- read.delim(
    metadata_file,
    row.names = 1,
    check.names = FALSE
)

##############################
## Check required columns
##############################

if (!"Taxon" %in% colnames(sig)) {
    stop("The significant taxa file must contain a column named 'Taxon'.")
}

if (!"Group" %in% colnames(metadata)) {
    stop("The metadata file must contain a column named 'Group'.")
}



##############################
## Handle no significant taxa
##############################

if (nrow(sig) == 0) {

    output_pdf <- file.path(
        output_dir,
        "Heatmap.pdf"
    )

    pdf(
        output_pdf,
        width = 10,
        height = 8
    )

    plot.new()

    text(
        0.5,
        0.58,
        "LEfSe Heatmap",
        cex = 1.6,
        font = 2
    )

    text(
        0.5,
        0.48,
        "No significant taxa were detected.",
        cex = 1.2
    )

    text(
        0.5,
        0.40,
        "LEfSe analysis completed successfully.",
        cex = 1
    )

    dev.off()

    writeLines(
        c(
            "LEfSe analysis completed successfully.",
            "No significant taxa were detected.",
            "Therefore, no biological heatmap could be generated."
        ),
        file.path(
            output_dir,
            "NO_SIGNIFICANT_TAXA.txt"
        )
    )

    message(
        "No significant taxa detected. ",
        "A placeholder Heatmap.pdf was created."
    )

    quit(
        save = "no",
        status = 0
    )
}

##############################
## Keep significant taxa
##############################

if ("FeatureID" %in% colnames(sig)) {

    selected_features <- sig$FeatureID

} else {

    selected_features <- sig$Taxon
}

feature_sig <- feature[
    rownames(feature) %in% selected_features,
    ,
    drop = FALSE
]

cat("Number of NA values:", sum(is.na(feature_sig)), "\n")


if (nrow(feature_sig) == 0) {
    stop(
        "Significant taxa were reported by LEfSe, ",
        "but none matched FeatureID values in the feature table."
    )
}



##############################
## Match samples
##############################

common_samples <- intersect(
    colnames(feature_sig),
    rownames(metadata)
)

if (length(common_samples) == 0) {
    stop("No common sample IDs were found between feature table and metadata.")
}

## فقط نمونه‌های مشترک
metadata <- metadata[
    common_samples,
    ,
    drop = FALSE
]

## مرتب کردن بر اساس گروه
metadata <- metadata[
    order(metadata$Group),
    ,
    drop = FALSE
]

## مرتب کردن ستون‌های feature مطابق metadata
feature_sig <- feature_sig[
    ,
    rownames(metadata),
    drop = FALSE
]

## تبدیل به ماتریس عددی
feature_sig <- as.matrix(feature_sig)
storage.mode(feature_sig) <- "numeric"

## جایگزینی NA در صورت وجود
if (sum(is.na(feature_sig)) > 0) {
    cat("Replacing", sum(is.na(feature_sig)), "NA values with 0\n")
    feature_sig[is.na(feature_sig)] <- 0
}


cluster_rows <- nrow(feature_sig) > 1

##############################
## Draw heatmap
##############################

pheatmap(
    feature_sig,
    annotation_col = metadata,
    scale = "row",
    clustering_rows = cluster_rows,
    clustering_cols = FALSE,
    show_rownames = TRUE,
    show_colnames = FALSE,
    fontsize_row = 8,
    border_color = NA,
    filename = file.path(output_dir, "Heatmap.pdf"),
    width = 10,
    height = 8
)

cat("Heatmap saved to:\n")
cat(file.path(output_dir, "Heatmap.pdf"), "\n")