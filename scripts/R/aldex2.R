library(ALDEx2)


############################################################
# Arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 14) {
    stop(
        paste(
            "Usage:",
            "Rscript aldex2.R",
            "counts.tsv",
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
            "mc_samples",
            "alpha",
            "fdr_method"
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
mc_samples      <- as.integer(args[12])

alpha           <- as.numeric(args[13])
fdr_method      <- args[14]


############################################################
# Output directory
############################################################

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Load count table
############################################################

counts_df <- read.delim(
    table_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

if (!"FeatureID" %in% colnames(counts_df)) {
    stop(
        "Feature table must contain a column named 'FeatureID'."
    )
}

feature_ids <- counts_df$FeatureID

counts_df$FeatureID <- NULL

counts <- as.matrix(counts_df)

rownames(counts) <- feature_ids

storage.mode(counts) <- "numeric"


############################################################
# Validate count matrix
############################################################

if (anyNA(counts)) {
    stop("Count table contains NA values.")
}

if (any(counts < 0)) {
    stop("Count table contains negative values.")
}

if (any(abs(counts - round(counts)) > 1e-8)) {
    stop(
        "ALDEx2 requires raw count data. Non-integer values were detected."
    )
}

counts <- round(counts)


############################################################
# Load metadata
############################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


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
            paste(missing_columns, collapse = ", ")
        )
    )
}


############################################################
# Validate Sample IDs
############################################################

if (anyDuplicated(metadata[[sample_column]]) > 0) {
    stop("Duplicate SampleID values detected in metadata.")
}


metadata[[sample_column]] <- as.character(
    metadata[[sample_column]]
)


############################################################
# Match samples between count table and metadata
############################################################

common_samples <- intersect(
    colnames(counts),
    metadata[[sample_column]]
)


if (length(common_samples) == 0) {
    stop(
        "No matching sample IDs between feature table and metadata."
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


if (!identical(
    colnames(counts),
    metadata[[sample_column]]
)) {
    stop(
        "Failed to correctly align count table and metadata."
    )
}


############################################################
# Keep only reference and case groups
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
            study_metadata[[group_column]] == reference_group
        )

        n_case <- sum(
            study_metadata[[group_column]] == case_group
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


eligible_studies <- eligibility$Study[
    eligibility$Eligible
]


############################################################
# Require enough eligible studies
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
# Keep eligible studies only
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
# Prevalence filtering
############################################################

feature_prevalence <- rowMeans(
    counts > 0
)


keep_features <- feature_prevalence >= prevalence


counts <- counts[
    keep_features,
    ,
    drop = FALSE
]


if (nrow(counts) == 0) {
    stop(
        "No features remained after prevalence filtering."
    )
}


############################################################
# Remove zero-count features
############################################################

counts <- counts[
    rowSums(counts) > 0,
    ,
    drop = FALSE
]


############################################################
# Set factor reference levels
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
# Build Study-adjusted model
#
# Main model:
#
#     abundance ~ Group + Study
#
############################################################

model_formula <- as.formula(
    paste(
        "~",
        group_column,
        "+",
        study_column
    )
)


model_matrix <- model.matrix(
    model_formula,
    data = metadata
)


############################################################
# Check model matrix
############################################################

if (qr(model_matrix)$rank < ncol(model_matrix)) {

    stop(
        paste(
            "ALDEx2 model matrix is rank deficient.",
            "Check Group/Study confounding."
        )
    )
}


############################################################
# Identify Disease-vs-Control coefficient
############################################################

expected_group_coefficient <- paste0(
    group_column,
    case_group
)


if (
    !expected_group_coefficient %in%
    colnames(model_matrix)
) {

    stop(
        paste(
            "Could not identify Group coefficient:",
            expected_group_coefficient
        )
    )
}


############################################################
# ALDEx2 CLR Monte Carlo sampling
############################################################

set.seed(2026)


clr_object <- aldex.clr(
    counts,
    model_matrix,
    mc.samples = mc_samples,
    denom = "all",
    verbose = FALSE
)


############################################################
# Study-adjusted ALDEx2 GLM
############################################################

glm_results <- aldex.glm(
    clr_object,
    verbose = FALSE,
    fdr.method = fdr_method
)


############################################################
# Save complete GLM output
############################################################

all_results <- data.frame(
    FeatureID = rownames(glm_results),
    glm_results,
    check.names = FALSE,
    row.names = NULL
)


write.table(
    all_results,
    file.path(
        output_dir,
        "all_glm_results.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Extract Group Disease-vs-Control coefficient only
#
# Example:
#
#   GroupDisease:Est
#   GroupDisease:SE
#   GroupDisease:t.val
#   GroupDisease:pval
#   GroupDisease:pval.padj
#
############################################################

estimate_column <- paste0(
    expected_group_coefficient,
    ":Est"
)

se_column <- paste0(
    expected_group_coefficient,
    ":SE"
)

tvalue_column <- paste0(
    expected_group_coefficient,
    ":t.val"
)

pvalue_column <- paste0(
    expected_group_coefficient,
    ":pval"
)

fdr_column <- paste0(
    expected_group_coefficient,
    ":pval.padj"
)


############################################################
# Validate Group coefficient columns
############################################################

required_result_columns <- c(
    estimate_column,
    se_column,
    tvalue_column,
    pvalue_column,
    fdr_column
)


missing_result_columns <- setdiff(
    required_result_columns,
    colnames(glm_results)
)


if (length(missing_result_columns) > 0) {

    cat(
        "\nAvailable ALDEx2 GLM columns:\n"
    )

    print(
        colnames(glm_results)
    )

    stop(
        paste(
            "Expected Group coefficient columns were not found:",
            paste(
                missing_result_columns,
                collapse = ", "
            )
        )
    )
}


############################################################
# Create clean Group-only results
############################################################

group_results <- data.frame(

    FeatureID = rownames(glm_results),

    Coefficient =
        glm_results[[estimate_column]],

    StandardError =
        glm_results[[se_column]],

    Tvalue =
        glm_results[[tvalue_column]],

    Pvalue =
        glm_results[[pvalue_column]],

    FDR =
        glm_results[[fdr_column]],

    stringsAsFactors = FALSE
)

############################################################
# Direction of association
############################################################

group_results$Direction <- ifelse(

    group_results$Coefficient > 0,

    paste0(
        case_group,
        "_higher"
    ),

    ifelse(

        group_results$Coefficient < 0,

        paste0(
            reference_group,
            "_higher"
        ),

        "no_change"
    )
)


############################################################
# Significance flag
############################################################

group_results$Significant <- (
    !is.na(group_results$FDR) &
    group_results$FDR <= alpha
)



############################################################
# Sort Group results by FDR
############################################################

group_results <- group_results[
    order(
        group_results$FDR,
        na.last = TRUE
    ),
    ,
    drop = FALSE
]

############################################################
# Save Group results
############################################################

write.table(
    group_results,
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

significant_results <- group_results[
    group_results$Significant,
    ,
    drop = FALSE
]


significant_results <- significant_results[
    order(significant_results$FDR),
    ,
    drop = FALSE
]


write.table(
    significant_results,
    file.path(
        output_dir,
        "significant_results.tsv"
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
        "PrevalenceThreshold",
        "MonteCarloSamples",
        "Alpha",
        "FDRMethod"
    ),

    Value = c(
        "ALDEx2",
        "Supplementary sensitivity analysis",
        paste(
            group_column,
            "+",
            study_column
        ),
        reference_group,
        case_group,
        length(eligible_studies),
        ncol(counts),
        nrow(counts),
        nrow(significant_results),
        prevalence,
        mc_samples,
        alpha,
        fdr_method
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

cat("\nALDEx2 supplementary analysis completed successfully.\n")

cat(
    "Model:",
    group_column,
    "+",
    study_column,
    "\n"
)

cat(
    "Eligible studies:",
    length(eligible_studies),
    "\n"
)

cat(
    "Features tested:",
    nrow(group_results),
    "\n"
)

cat(
    "Significant features:",
    nrow(significant_results),
    "\n"
)