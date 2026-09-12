#!/usr/bin/env Rscript


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)


if (length(args) != 7) {

    stop(
        paste(
            "Usage: Rscript mmuphin_correction.R",
            "<feature_table>",
            "<metadata>",
            "<batch_variable>",
            "<group_variable>",
            "<adjusted_output>",
            "<diagnostic_pdf>",
            "<summary_output>"
        )
    )
}


table_file <- args[1]

metadata_file <- args[2]

batch_variable <- args[3]

group_variable <- args[4]

output_file <- args[5]

diagnostic_file <- args[6]

summary_file <- args[7]


############################################################
# Package
############################################################

if (
    !requireNamespace(
        "MMUPHin",
        quietly = TRUE
    )
) {

    stop(
        "Package 'MMUPHin' is not installed."
    )
}


############################################################
# Input files
############################################################

if (!file.exists(table_file)) {

    stop(
        "Feature table not found: ",
        table_file
    )
}


if (!file.exists(metadata_file)) {

    stop(
        "Metadata file not found: ",
        metadata_file
    )
}


############################################################
# Read abundance/count table
#
# Features x Samples
############################################################

feature_table <- read.delim(

    table_file,

    row.names = 1,

    check.names = FALSE,

    stringsAsFactors = FALSE
)


feature_table <- as.matrix(
    feature_table
)


storage.mode(
    feature_table
) <- "double"


############################################################
# Validate feature table
############################################################

if (
    nrow(feature_table) == 0 ||
    ncol(feature_table) == 0
) {

    stop(
        "Feature table is empty."
    )
}


if (
    any(
        !is.finite(
            feature_table
        )
    )
) {

    stop(
        "Feature table contains NA/Inf values."
    )
}


if (
    any(
        feature_table < 0
    )
) {

    stop(
        "Feature table contains negative values."
    )
}


if (
    anyDuplicated(
        rownames(
            feature_table
        )
    )
) {

    stop(
        "Duplicate Feature IDs detected."
    )
}


if (
    anyDuplicated(
        colnames(
            feature_table
        )
    )
) {

    stop(
        "Duplicate sample IDs detected "
        "in feature table."
    )
}


############################################################
# All-zero features/samples
############################################################

if (
    any(
        rowSums(
            feature_table
        ) == 0
    )
) {

    stop(
        "All-zero feature(s) detected."
    )
}


if (
    any(
        colSums(
            feature_table
        ) == 0
    )
) {

    bad_samples <- colnames(
        feature_table
    )[
        colSums(
            feature_table
        ) == 0
    ]

    stop(
        "All-zero sample(s): ",
        paste(
            bad_samples,
            collapse = ", "
        )
    )
}


############################################################
# Read metadata
############################################################

metadata <- read.delim(

    metadata_file,

    check.names = FALSE,

    stringsAsFactors = FALSE
)


required_columns <- c(

    "SampleID",

    batch_variable,

    group_variable
)


missing_columns <- setdiff(

    required_columns,

    colnames(
        metadata
    )
)


if (
    length(
        missing_columns
    ) > 0
) {

    stop(
        "Missing metadata columns: ",
        paste(
            missing_columns,
            collapse = ", "
        )
    )
}


############################################################
# Clean metadata
############################################################

metadata$SampleID <- trimws(
    as.character(
        metadata$SampleID
    )
)


metadata[[batch_variable]] <- trimws(
    as.character(
        metadata[[batch_variable]]
    )
)


metadata[[group_variable]] <- trimws(
    as.character(
        metadata[[group_variable]]
    )
)


############################################################
# Duplicate SampleID
############################################################

if (
    anyDuplicated(
        metadata$SampleID
    )
) {

    stop(
        "Duplicate SampleID values "
        "detected in metadata."
    )
}


############################################################
# Match metadata to feature table
############################################################

idx <- match(

    colnames(
        feature_table
    ),

    metadata$SampleID
)


if (
    any(
        is.na(
            idx
        )
    )
) {

    missing_samples <- colnames(
        feature_table
    )[
        is.na(
            idx
        )
    ]

    stop(
        "Feature-table samples missing from metadata: ",
        paste(
            missing_samples,
            collapse = ", "
        )
    )
}


metadata <- metadata[
    idx,
    ,
    drop = FALSE
]


############################################################
# Check ordering
############################################################

if (
    !identical(
        colnames(
            feature_table
        ),
        metadata$SampleID
    )
) {

    stop(
        "Feature table / metadata sample order mismatch."
    )
}


############################################################
# Missing/blank variables
############################################################

if (
    any(
        is.na(
            metadata[[batch_variable]]
        )
    ) ||
    any(
        metadata[[batch_variable]] == ""
    )
) {

    stop(
        "Batch variable contains missing/blank values."
    )
}


if (
    any(
        is.na(
            metadata[[group_variable]]
        )
    ) ||
    any(
        metadata[[group_variable]] == ""
    )
) {

    stop(
        "Biological variable contains "
        "missing/blank values."
    )
}


############################################################
# Convert to factors
############################################################

metadata[[batch_variable]] <- factor(
    metadata[[batch_variable]]
)


metadata[[group_variable]] <- factor(
    metadata[[group_variable]]
)


if (
    nlevels(
        metadata[[batch_variable]]
    ) < 2
) {

    stop(
        "MMUPHin requires at least two batches/studies."
    )
}


if (
    nlevels(
        metadata[[group_variable]]
    ) < 2
) {

    stop(
        "Biological variable requires "
        "at least two levels."
    )
}


if (
    batch_variable ==
    group_variable
) {

    stop(
        "Batch and biological variables "
        "cannot be identical."
    )
}


############################################################
# MMUPHin requires metadata row names
# to match abundance column names.
############################################################

rownames(
    metadata
) <- metadata$SampleID


if (
    !identical(
        colnames(
            feature_table
        ),
        rownames(
            metadata
        )
    )
) {

    stop(
        "MMUPHin sample names are not aligned."
    )
}


############################################################
# Explicit confounding / rank check
############################################################

design_formula <- as.formula(
    paste(
        "~",
        batch_variable,
        "+",
        group_variable
    )
)


design_matrix <- model.matrix(
    design_formula,
    data = metadata
)


if (
    qr(
        design_matrix
    )$rank <
    ncol(
        design_matrix
    )
) {

    stop(
        paste0(
            "Batch/study variable and biological ",
            "variable are perfectly confounded. ",
            "MMUPHin cannot separate their effects."
        )
    )
}


############################################################
# Output directories
############################################################

dir.create(
    dirname(
        output_file
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


dir.create(
    dirname(
        diagnostic_file
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


dir.create(
    dirname(
        summary_file
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Sample totals BEFORE correction
############################################################

totals_before <- colSums(
    feature_table
)


############################################################
# MMUPHin
############################################################

fit <- tryCatch(

    MMUPHin::adjust_batch(

        feature_abd =
            feature_table,

        batch =
            batch_variable,

        covariates =
            group_variable,

        data =
            metadata,

        control = list(

            zero_inflation =
                TRUE,

            diagnostic_plot =
                diagnostic_file,

            verbose =
                TRUE
        )
    ),

    error = function(e) {

        stop(
            "MMUPHin adjust_batch failed: ",
            conditionMessage(
                e
            )
        )
    }
)


############################################################
# Extract corrected abundance
############################################################

adjusted <- fit$feature_abd_adj


if (
    is.null(
        adjusted
    )
) {

    stop(
        "MMUPHin did not return feature_abd_adj."
    )
}


adjusted <- as.matrix(
    adjusted
)


storage.mode(
    adjusted
) <- "double"


############################################################
# Validate adjusted table
############################################################

if (
    !identical(
        dim(
            adjusted
        ),
        dim(
            feature_table
        )
    )
) {

    stop(
        "Adjusted abundance table dimensions changed."
    )
}


if (
    !identical(
        rownames(
            adjusted
        ),
        rownames(
            feature_table
        )
    )
) {

    stop(
        "Feature order changed after MMUPHin."
    )
}


if (
    !identical(
        colnames(
            adjusted
        ),
        colnames(
            feature_table
        )
    )
) {

    stop(
        "Sample order changed after MMUPHin."
    )
}


if (
    any(
        !is.finite(
            adjusted
        )
    )
) {

    stop(
        "Adjusted table contains NA/Inf values."
    )
}


if (
    any(
        adjusted < 0
    )
) {

    stop(
        "MMUPHin produced negative abundance values."
    )
}


if (
    any(
        rowSums(
            adjusted
        ) == 0
    )
) {

    stop(
        "MMUPHin produced an all-zero feature."
    )
}


if (
    any(
        colSums(
            adjusted
        ) == 0
    )
) {

    stop(
        "MMUPHin produced an all-zero sample."
    )
}


############################################################
# Save adjusted abundance
############################################################

write.table(

    adjusted,

    output_file,

    sep = "\t",

    quote = FALSE,

    col.names = NA
)


############################################################
# Check per-sample totals
############################################################

totals_after <- colSums(
    adjusted
)


relative_total_difference <- abs(

    totals_after -
    totals_before

) / pmax(

    abs(
        totals_before
    ),

    .Machine$double.eps
)


############################################################
# Summary
############################################################

summary_table <- data.frame(

    Method =
        "MMUPHin",

    Batch_Variable =
        batch_variable,

    Biological_Variable =
        group_variable,

    N_Features =
        nrow(
            adjusted
        ),

    N_Samples =
        ncol(
            adjusted
        ),

    N_Batches =
        nlevels(
            metadata[
                [batch_variable]
            ]
        ),

    N_Biological_Groups =
        nlevels(
            metadata[
                [group_variable]
            ]
        ),

    Zeros_Before =
        sum(
            feature_table == 0
        ),

    Zeros_After =
        sum(
            adjusted == 0
        ),

    Max_Relative_Sample_Total_Difference =
        max(
            relative_total_difference
        ),

    stringsAsFactors = FALSE
)


write.table(

    summary_table,

    summary_file,

    sep = "\t",

    quote = FALSE,

    row.names = FALSE
)


cat(
    "MMUPHin batch correction completed successfully.\n"
)

cat(
    "Batch variable:",
    batch_variable,
    "\n"
)

cat(
    "Biological variable:",
    group_variable,
    "\n"
)

cat(
    "Output:",
    output_file,
    "\n"
)