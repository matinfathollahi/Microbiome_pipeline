library(Maaslin2)


############################################################
# Arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 15) {
    stop(
        paste(
            "Usage:",
            "Rscript maaslin2.R",
            "table.tsv",
            "metadata.tsv",
            "output_dir",
            "sample_column",
            "study_column",
            "group_column",
            "reference_group",
            "case_group",
            "min_samples_per_group",
            "min_studies",
            "prevalence",
            "alpha",
            "normalization",
            "transform",
            "analysis_method"
        )
    )
}


table_file      <- args[1]
metadata_file   <- args[2]
output_dir      <- args[3]

sample_column   <- args[4]
study_column    <- args[5]
group_column    <- args[6]

reference_group <- args[7]
case_group      <- args[8]

min_samples     <- as.integer(args[9])
min_studies     <- as.integer(args[10])

prevalence      <- as.numeric(args[11])
alpha           <- as.numeric(args[12])

normalization   <- args[13]
transform       <- args[14]
analysis_method <- args[15]


############################################################
# Validate arguments
############################################################

if (is.na(min_samples) || min_samples < 1) {
    stop("min_samples_per_group must be >= 1.")
}

if (is.na(min_studies) || min_studies < 1) {
    stop("min_studies must be >= 1.")
}

if (is.na(prevalence) || prevalence < 0 || prevalence > 1) {
    stop("prevalence must be between 0 and 1.")
}

if (is.na(alpha) || alpha <= 0 || alpha >= 1) {
    stop("alpha must be between 0 and 1.")
}


############################################################
# Create output directory
############################################################

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Load feature table
#
# Expected:
# rows    = Features
# columns = Samples
############################################################

counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

counts <- as.matrix(counts)

storage.mode(counts) <- "numeric"


############################################################
# Validate feature table
############################################################

if (anyNA(counts)) {
    stop("Feature table contains NA or non-numeric values.")
}

if (any(counts < 0)) {
    stop("Feature table contains negative values.")
}

if (nrow(counts) == 0 || ncol(counts) == 0) {
    stop("Feature table is empty.")
}


############################################################
# Load metadata
############################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


############################################################
# Validate metadata columns
############################################################

required_columns <- c(
    sample_column,
    study_column,
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
# Validate Sample IDs
############################################################

metadata[[sample_column]] <- as.character(
    metadata[[sample_column]]
)

if (anyDuplicated(metadata[[sample_column]]) > 0) {
    stop("Duplicate sample IDs detected in metadata.")
}


############################################################
# Match samples between feature table and metadata
############################################################

common_samples <- intersect(
    colnames(counts),
    metadata[[sample_column]]
)

if (length(common_samples) == 0) {
    stop(
        "No matching samples between feature table and metadata."
    )
}


############################################################
# Keep common samples
############################################################

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


############################################################
# Confirm sample order
############################################################

if (!identical(
    colnames(counts),
    metadata[[sample_column]]
)) {

    stop(
        "Feature table and metadata sample order do not match."
    )
}


############################################################
# Remove samples with missing Study / Group
############################################################

valid_samples <- (
    !is.na(metadata[[study_column]]) &
    !is.na(metadata[[group_column]]) &
    metadata[[study_column]] != "" &
    metadata[[group_column]] != ""
)

metadata <- metadata[
    valid_samples,
    ,
    drop = FALSE
]

counts <- counts[
    ,
    valid_samples,
    drop = FALSE
]


############################################################
# Keep reference and case groups only
############################################################

keep_group <- metadata[[group_column]] %in% c(
    reference_group,
    case_group
)

metadata <- metadata[
    keep_group,
    ,
    drop = FALSE
]

counts <- counts[
    ,
    keep_group,
    drop = FALSE
]


############################################################
# Study eligibility
############################################################

studies <- sort(
    unique(metadata[[study_column]])
)


eligibility_list <- lapply(
    studies,
    function(study) {

        study_metadata <- metadata[
            metadata[[study_column]] == study,
            ,
            drop = FALSE
        ]

        n_reference <- sum(
            study_metadata[[group_column]] == reference_group,
            na.rm = TRUE
        )

        n_case <- sum(
            study_metadata[[group_column]] == case_group,
            na.rm = TRUE
        )

        eligible <- (
            n_reference >= min_samples &&
            n_case >= min_samples
        )

        data.frame(
            Study = study,
            ReferenceSamples = n_reference,
            CaseSamples = n_case,
            Eligible = eligible,
            stringsAsFactors = FALSE
        )
    }
)


eligibility <- do.call(
    rbind,
    eligibility_list
)


############################################################
# Save Study eligibility
############################################################

write.table(
    eligibility,
    file.path(
        output_dir,
        "study_eligibility.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Select eligible Studies
############################################################

eligible_studies <- eligibility$Study[
    eligibility$Eligible
]


############################################################
# Require enough eligible Studies
############################################################

if (length(eligible_studies) < min_studies) {

    stop(
        paste0(
            "Only ",
            length(eligible_studies),
            " eligible studies were found; at least ",
            min_studies,
            " are required."
        )
    )
}


############################################################
# Keep eligible Studies only
############################################################

keep_study <- metadata[[study_column]] %in%
    eligible_studies

metadata <- metadata[
    keep_study,
    ,
    drop = FALSE
]

counts <- counts[
    ,
    keep_study,
    drop = FALSE
]


############################################################
# Validate remaining samples
############################################################

if (nrow(metadata) == 0) {
    stop(
        "No samples remained after Study eligibility filtering."
    )
}


############################################################
# Set factor levels
############################################################

metadata[[group_column]] <- factor(
    metadata[[group_column]],
    levels = c(
        reference_group,
        case_group
    )
)

metadata[[study_column]] <- droplevels(
    factor(
        metadata[[study_column]]
    )
)


############################################################
# Check Group levels
############################################################

if (
    nlevels(
        droplevels(
            metadata[[group_column]]
        )
    ) < 2
) {

    stop(
        "Both reference and case groups are required."
    )
}


############################################################
# Check Study levels
############################################################

if (
    nlevels(
        metadata[[study_column]]
    ) < min_studies
) {

    stop(
        paste0(
            "At least ",
            min_studies,
            " eligible Studies are required."
        )
    )
}


############################################################
# Prepare feature table for MaAsLin2
#
# MaAsLin2:
# rows    = Samples
# columns = Features
############################################################

input_data <- as.data.frame(
    t(counts),
    check.names = FALSE
)


############################################################
# Prepare metadata
############################################################

rownames(metadata) <- metadata[[sample_column]]

input_metadata <- metadata[
    ,
    c(
        group_column,
        study_column
    ),
    drop = FALSE
]


############################################################
# Final consistency check
############################################################

if (!identical(
    rownames(input_data),
    rownames(input_metadata)
)) {

    stop(
        "Sample order mismatch before MaAsLin2."
    )
}


############################################################
# Run Study-adjusted MaAsLin2
#
# Model:
#
# abundance ~ Group + Study
############################################################

fit <- Maaslin2(
    input_data = input_data,

    input_metadata = input_metadata,

    output = output_dir,

    fixed_effects = c(
        group_column,
        study_column
    ),

    reference = c(
        paste0(
            group_column,
            ",",
            reference_group
        )
    ),

    min_prevalence = prevalence,

    normalization = normalization,

    transform = transform,

    analysis_method = analysis_method,

    correction = "BH",

    max_significance = alpha,

    standardize = FALSE,

    plot_heatmap = FALSE,

    plot_scatter = FALSE
)


############################################################
# Read MaAsLin2 complete results
############################################################

all_results_file <- file.path(
    output_dir,
    "all_results.tsv"
)

if (!file.exists(all_results_file)) {

    stop(
        "MaAsLin2 all_results.tsv was not generated."
    )
}


all_results <- read.delim(
    all_results_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


############################################################
# Validate MaAsLin2 result columns
############################################################

required_result_columns <- c(
    "feature",
    "metadata",
    "value",
    "coef",
    "pval",
    "qval"
)

missing_result_columns <- setdiff(
    required_result_columns,
    colnames(all_results)
)

if (length(missing_result_columns) > 0) {

    stop(
        paste(
            "Missing columns in MaAsLin2 results:",
            paste(
                missing_result_columns,
                collapse = ", "
            )
        )
    )
}


############################################################
# Extract Group effect only
############################################################

group_results <- all_results[
    all_results$metadata == group_column,
    ,
    drop = FALSE
]


############################################################
# Keep case vs reference comparison only
############################################################

group_results <- group_results[
    group_results$value == case_group,
    ,
    drop = FALSE
]


if (nrow(group_results) == 0) {

    stop(
        paste0(
            "No ",
            case_group,
            " vs ",
            reference_group,
            " Group results were found."
        )
    )
}


############################################################
# Create clean supplementary results
############################################################

group_results_clean <- data.frame(

    FeatureID =
        group_results$feature,

    Coefficient =
        group_results$coef,

    Pvalue =
        group_results$pval,

    FDR =
        group_results$qval,

    stringsAsFactors = FALSE
)


############################################################
# Direction
############################################################

group_results_clean$Direction <- ifelse(

    group_results_clean$Coefficient > 0,

    paste0(
        case_group,
        "_higher"
    ),

    ifelse(

        group_results_clean$Coefficient < 0,

        paste0(
            reference_group,
            "_higher"
        ),

        "no_change"
    )
)


############################################################
# Significance
############################################################

group_results_clean$Significant <- (
    !is.na(group_results_clean$FDR) &
    group_results_clean$FDR <= alpha
)


############################################################
# Sort by FDR
############################################################

group_results_clean <- group_results_clean[
    order(
        group_results_clean$FDR,
        na.last = TRUE
    ),
    ,
    drop = FALSE
]


############################################################
# Save Group results
############################################################

write.table(
    group_results_clean,
    file.path(
        output_dir,
        "group_results.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Significant Group results
############################################################

group_significant_results <- group_results_clean[
    group_results_clean$Significant,
    ,
    drop = FALSE
]


write.table(
    group_significant_results,
    file.path(
        output_dir,
        "group_significant_results.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Analysis summary
############################################################

summary_table <- data.frame(

    Metric = c(
        "Analysis",
        "Role",
        "Model",
        "ReferenceGroup",
        "CaseGroup",
        "EligibleStudies",
        "Samples",
        "FeaturesTested",
        "SignificantFeatures",
        "MinSamplesPerGroup",
        "PrevalenceThreshold",
        "Normalization",
        "Transform",
        "AnalysisMethod",
        "Alpha",
        "Correction"
    ),

    Value = c(
        "MaAsLin2",
        "Supplementary sensitivity analysis",
        paste(
            group_column,
            "+",
            study_column
        ),
        reference_group,
        case_group,
        length(eligible_studies),
        nrow(input_data),
        ncol(input_data),
        nrow(group_significant_results),
        min_samples,
        prevalence,
        normalization,
        transform,
        analysis_method,
        alpha,
        "BH"
    ),

    stringsAsFactors = FALSE
)


write.table(
    summary_table,
    file.path(
        output_dir,
        "analysis_summary.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Done
############################################################

cat(
    "\nMaAsLin2 supplementary analysis completed successfully.\n"
)

cat(
    "Model:",
    group_column,
    "+",
    study_column,
    "\n"
)

cat(
    "Reference group:",
    reference_group,
    "\n"
)

cat(
    "Case group:",
    case_group,
    "\n"
)

cat(
    "Eligible studies:",
    length(eligible_studies),
    "\n"
)

cat(
    "Samples:",
    nrow(input_data),
    "\n"
)

cat(
    "Features tested:",
    nrow(group_results_clean),
    "\n"
)

cat(
    "Significant features:",
    nrow(group_significant_results),
    "\n"
)