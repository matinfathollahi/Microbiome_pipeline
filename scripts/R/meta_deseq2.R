library(DESeq2)

args <- commandArgs(
    trailingOnly = TRUE
)

if (length(args) != 8) {

    stop(
        paste(
            "Usage:",
            "meta_deseq2.R",
            "counts.tsv metadata.tsv",
            "sample_column group_column",
            "reference_group case_group",
            "study output.tsv"
        )
    )
}

counts_file <- args[1]
metadata_file <- args[2]

sample_column <- args[3]
group_column <- args[4]

reference_group <- args[5]
case_group <- args[6]

study <- args[7]
output_file <- args[8]


############################################################
# Read data
############################################################

counts <- read.delim(
    counts_file,
    row.names = 1,
    check.names = FALSE
)

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


############################################################
# Validate metadata
############################################################

required_columns <- c(
    sample_column,
    group_column
)

missing_columns <- setdiff(
    required_columns,
    colnames(metadata)
)

if (length(missing_columns) > 0) {

    stop(
        paste(
            "Missing metadata columns:",
            paste(
                missing_columns,
                collapse = ", "
            )
        )
    )
}


############################################################
# Keep requested comparison only
############################################################

metadata <- metadata[
    metadata[[group_column]] %in%
        c(
            reference_group,
            case_group
        ),
    ,
    drop = FALSE
]


if (nrow(metadata) == 0) {

    stop(
        paste(
            "No samples found for comparison:",
            case_group,
            "vs",
            reference_group
        )
    )
}


############################################################
# Check both groups
############################################################

present_groups <- unique(
    metadata[[group_column]]
)

required_groups <- c(
    reference_group,
    case_group
)

missing_groups <- setdiff(
    required_groups,
    present_groups
)

if (length(missing_groups) > 0) {

    stop(
        paste(
            "Study",
            study,
            "is missing group(s):",
            paste(
                missing_groups,
                collapse = ", "
            )
        )
    )
}


############################################################
# Match samples
############################################################

metadata_samples <- as.character(
    metadata[[sample_column]]
)

common_samples <- intersect(
    colnames(counts),
    metadata_samples
)

if (length(common_samples) < 4) {

    stop(
        paste(
            "Too few matched samples in study",
            study
        )
    )
}

counts <- counts[
    ,
    common_samples,
    drop = FALSE
]

metadata <- metadata[
    match(
        common_samples,
        metadata[[sample_column]]
    ),
    ,
    drop = FALSE
]

rownames(metadata) <- metadata[[sample_column]]


if (!all(
    colnames(counts)
    == rownames(metadata)
)) {

    stop(
        "Counts and metadata sample order mismatch."
    )
}


############################################################
# Validate counts
############################################################

counts_matrix <- as.matrix(
    counts
)

storage.mode(
    counts_matrix
) <- "numeric"


if (any(
    !is.finite(counts_matrix)
)) {

    stop(
        "Non-finite counts found."
    )
}


if (any(
    counts_matrix < 0
)) {

    stop(
        "Negative counts found."
    )
}


if (any(
    abs(
        counts_matrix
        - round(counts_matrix)
    ) > 1e-8
)) {

    stop(
        "DESeq2 requires integer counts."
    )
}


counts_matrix <- round(
    counts_matrix
)

storage.mode(
    counts_matrix
) <- "integer"


############################################################
# Remove duplicated taxa
############################################################

if (any(
    duplicated(
        rownames(counts_matrix)
    )
)) {

    stop(
        "Duplicated feature IDs found."
    )
}


############################################################
# Study-specific count filtering
############################################################

keep <- rowSums(
    counts_matrix >= 10
) >= 2

counts_matrix <- counts_matrix[
    keep,
    ,
    drop = FALSE
]


if (nrow(counts_matrix) == 0) {

    stop(
        paste(
            "No features remain after filtering in",
            study
        )
    )
}


############################################################
# Remove samples with zero total counts after feature filtering
############################################################

sample_totals <- colSums(
    counts_matrix
)

sample_keep <- sample_totals > 0

zero_samples <- names(
    sample_totals
)[!sample_keep]

if (length(zero_samples) > 0) {

    cat(
        "Zero-total samples removed after feature filtering:",
        length(zero_samples),
        "\n"
    )

    cat(
        paste(
            zero_samples,
            collapse = ", "
        ),
        "\n"
    )
}

counts_matrix <- counts_matrix[
    ,
    sample_keep,
    drop = FALSE
]

if (ncol(counts_matrix) < 4) {
    stop(
        paste(
            "Too few samples with non-zero counts in",
            study,
            "after feature filtering"
        )
    )
}

############################################################
# Group coding
############################################################

metadata[[group_column]] <- factor(
    metadata[[group_column]],
    levels = c(
        reference_group,
        case_group
    )
)


############################################################
# DESeq2
############################################################

design_formula <- reformulate(
    group_column
)

dds <- DESeqDataSetFromMatrix(

    countData = counts_matrix,

    colData = metadata,

    design = design_formula
)

dds <- DESeq(
    dds,
    quiet = TRUE,
    sfType = "poscounts",
    fitType = "mean"
)


############################################################
# Explicit direction:
# case - reference
############################################################

res <- results(

    dds,

    contrast = c(
        group_column,
        case_group,
        reference_group
    )
)


############################################################
# Standardized output
############################################################

out <- data.frame(

    FeatureID = rownames(res),

    EffectSize =
        as.numeric(
            res$log2FoldChange
        ),

    StandardError =
        as.numeric(
            res$lfcSE
        ),

    Pvalue =
        as.numeric(
            res$pvalue
        ),

    FDR =
        as.numeric(
            res$padj
        ),

    Study =
        study,

    Method =
        "DESeq2",

    Comparison =
        paste0(
            case_group,
            "_vs_",
            reference_group
        ),

    stringsAsFactors = FALSE
)


out <- out[
    !is.na(out$EffectSize)
    & !is.na(out$StandardError)
    & is.finite(out$EffectSize)
    & is.finite(out$StandardError)
    & out$StandardError > 0,
    ,
    drop = FALSE
]


if (nrow(out) == 0) {

    stop(
        paste(
            "No valid DESeq2 effects for",
            study
        )
    )
}


out <- out[
    order(
        out$FDR,
        na.last = TRUE
    ),
    ,
    drop = FALSE
]


############################################################
# Save
############################################################

dir.create(
    dirname(output_file),
    recursive = TRUE,
    showWarnings = FALSE
)

write.table(

    out,

    output_file,

    sep = "\t",

    quote = FALSE,

    row.names = FALSE
)

cat(
    "Study:", study, "\n"
)

cat(
    "Comparison:",
    case_group,
    "vs",
    reference_group,
    "\n"
)

cat(
    "Samples:", ncol(counts_matrix), "\n"
)

cat(
    "Features:", nrow(out), "\n"
)