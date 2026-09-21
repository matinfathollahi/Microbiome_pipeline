library(ANCOMBC)


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)


if (length(args) != 15) {

    stop(
        paste(
            "Usage:",
            "Rscript ancombc.R",
            "<table>",
            "<taxonomy>",
            "<metadata>",
            "<output_dir>",
            "<sample_column>",
            "<study_column>",
            "<group_column>",
            "<reference_group>",
            "<case_group>",
            "<min_samples_per_group>",
            "<min_studies>",
            "<prevalence>",
            "<alpha>",
            "<p_adjust_method>",
            "<threads>"
        )
    )
}


table_file <- args[1]
taxonomy_file <- args[2]
metadata_file <- args[3]
output_dir <- args[4]

sample_column <- args[5]
study_column <- args[6]
group_column <- args[7]

reference_group <- args[8]
case_group <- args[9]

min_samples_per_group <- as.integer(
    args[10]
)

min_studies <- as.integer(
    args[11]
)

prevalence <- as.numeric(
    args[12]
)

alpha <- as.numeric(
    args[13]
)

p_adjust_method <- args[14]

threads <- as.integer(
    args[15]
)


############################################################
# Validate config
############################################################

if (
    is.na(min_samples_per_group) ||
    min_samples_per_group < 2
) {

    stop(
        "min_samples_per_group must be >= 2."
    )
}


if (
    is.na(min_studies) ||
    min_studies < 2
) {

    stop(
        "min_studies must be >= 2."
    )
}


if (
    is.na(prevalence) ||
    prevalence < 0 ||
    prevalence >= 1
) {

    stop(
        "prevalence must be in [0, 1)."
    )
}


if (
    is.na(alpha) ||
    alpha <= 0 ||
    alpha >= 1
) {

    stop(
        "alpha must be in (0, 1)."
    )
}


valid_adjustments <- c(
    "holm",
    "hochberg",
    "hommel",
    "bonferroni",
    "BH",
    "BY",
    "fdr",
    "none"
)


if (
    !p_adjust_method %in%
    valid_adjustments
) {

    stop(
        "Invalid p_adjust_method: ",
        p_adjust_method
    )
}


if (
    is.na(threads) ||
    threads < 1
) {

    stop(
        "threads must be >= 1."
    )
}


############################################################
# Input files
############################################################

input_files <- c(
    table_file,
    taxonomy_file,
    metadata_file
)


missing_files <- input_files[
    !file.exists(
        input_files
    )
]


if (
    length(missing_files) > 0
) {

    stop(
        "Missing input file(s): ",
        paste(
            missing_files,
            collapse = ", "
        )
    )
}


dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Count table
############################################################

counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE
)


counts <- as.matrix(
    counts
)


storage.mode(
    counts
) <- "numeric"


if (
    any(
        !is.finite(
            counts
        )
    )
) {

    stop(
        "Count table contains non-finite values."
    )
}


if (
    any(
        counts < 0
    )
) {

    stop(
        "Count table contains negative values."
    )
}


if (
    any(
        abs(
            counts -
            round(
                counts
            )
        ) > 1e-8
    )
) {

    stop(
        "ANCOM-BC2 requires count data; non-integer values were detected."

    )
}


counts <- round(
    counts
)


counts <- counts[
    rowSums(
        counts
    ) > 0,
    ,
    drop = FALSE
]


if (
    nrow(counts) == 0
) {

    stop(
        "No non-zero features remain."
    )
}


############################################################
# Metadata
############################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


required_metadata <- c(
    sample_column,
    study_column,
    group_column
)


missing_metadata <- setdiff(
    required_metadata,
    colnames(metadata)
)


if (
    length(missing_metadata) > 0
) {

    stop(
        "Missing metadata columns: ",
        paste(
            missing_metadata,
            collapse = ", "
        )
    )
}


for (
    column in required_metadata
) {

    metadata[[column]] <- (
        trimws(
            as.character(
                metadata[[column]]
            )
        )
    )
}


if (
    any(
        metadata[[sample_column]] == ""
    )
) {

    stop(
        "Blank SampleID values detected."
    )
}


if (
    anyDuplicated(
        metadata[[sample_column]]
    ) > 0
) {

    stop(
        "Duplicated SampleIDs detected."
    )
}


############################################################
# Check sample matching
############################################################

missing_samples <- setdiff(
    colnames(counts),
    metadata[[sample_column]]
)


if (
    length(missing_samples) > 0
) {

    stop(
        "Count-table samples missing from metadata: ",
        paste(
            head(
                missing_samples,
                20
            ),
            collapse = ", "
        )
    )
}


############################################################
# Restrict metadata to samples present in count table
############################################################

metadata_missing_from_counts <- setdiff(
    metadata[[sample_column]],
    colnames(counts)
)


if (
    length(metadata_missing_from_counts) > 0
) {

    warning(
        paste0(
            length(metadata_missing_from_counts),
            "metadata sample(s) are absent from the count table and will be excluded from ANCOM-BC2: ",
            
            paste(
                head(
                    metadata_missing_from_counts,
                    20
                ),
                collapse = ", "
            )
        )
    )
}


metadata <- metadata[
    metadata[[sample_column]]
    %in%
    colnames(counts),
    ,
    drop = FALSE
]


if (
    nrow(metadata) == 0
) {

    stop(
        "No metadata samples are present in the count table."
    )
}


############################################################
# Keep requested contrast only
############################################################

metadata <- metadata[
    metadata[[group_column]]
    %in%
    c(
        reference_group,
        case_group
    ),
    ,
    drop = FALSE
]


if (
    nrow(metadata) == 0
) {

    stop(
        "No samples remain for configured contrast."
    )
}


if (
    !reference_group
    %in%
    metadata[[group_column]]
) {

    stop(
        "Reference group not found: ",
        reference_group
    )
}


if (
    !case_group
    %in%
    metadata[[group_column]]
) {

    stop(
        "Case group not found: ",
        case_group
    )
}


############################################################
# Study eligibility
############################################################

study_names <- sort(
    unique(
        metadata[[study_column]]
    )
)


eligibility_rows <- list()


for (
    study in study_names
) {

    study_metadata <- metadata[
        metadata[[study_column]] == study,
        ,
        drop = FALSE
    ]


    n_reference <- sum(
        study_metadata[[group_column]]
        ==
        reference_group
    )


    n_case <- sum(
        study_metadata[[group_column]]
        ==
        case_group
    )


    eligible <- (
        n_reference
        >=
        min_samples_per_group
        &&
        n_case
        >=
        min_samples_per_group
    )


    eligibility_rows[
        [
            length(
                eligibility_rows
            ) + 1
        ]
    ] <- data.frame(

        Study =
            study,

        ReferenceSamples =
            n_reference,

        CaseSamples =
            n_case,

        Eligible =
            eligible,

        stringsAsFactors =
            FALSE
    )
}


study_eligibility <- do.call(
    rbind,
    eligibility_rows
)


write.table(
    study_eligibility,
    file.path(
        output_dir,
        "study_eligibility.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


eligible_studies <- (
    study_eligibility$Study[
        study_eligibility$Eligible
    ]
)


if (
    length(
        eligible_studies
    )
    <
    min_studies
) {

    stop(
        paste0(
            "Insufficient eligible studies for ANCOM-BC2. ",
            "Found ",
            length(
                eligible_studies
            ),
            ", required ",
            min_studies,
            "."
        )
    )
}


############################################################
# Restrict analysis to eligible studies
############################################################

metadata <- metadata[
    metadata[[study_column]]
    %in%
    eligible_studies,
    ,
    drop = FALSE
]


selected_samples <- metadata[
    [
        sample_column
    ]
]


counts <- counts[
    ,
    selected_samples,
    drop = FALSE
]


rownames(
    metadata
) <- metadata[
    [
        sample_column
    ]
]


metadata <- metadata[
    colnames(
        counts
    ),
    ,
    drop = FALSE
]


############################################################
# Factor reference levels
############################################################

metadata[[group_column]] <- factor(
    metadata[[group_column]],
    levels = c(
        reference_group,
        case_group
    )
)


metadata[[study_column]] <- factor(
    metadata[[study_column]]
)


############################################################
# ANCOM-BC2 model
#
# Group = biological variable of interest
# Study = fixed adjustment factor
############################################################

fix_formula <- paste(
    group_column,
    "+",
    study_column
)


set.seed(
    2026
)


fit <- ancombc2(

    data =
        counts,

    taxa_are_rows =
        TRUE,

    aggregate_data =
        counts,

    meta_data =
        metadata,

    fix_formula =
        fix_formula,

    rand_formula =
        NULL,

    p_adj_method =
        p_adjust_method,

    pseudo_sens =
        TRUE,

    prv_cut =
        prevalence,

    lib_cut =
        0,

    s0_perc =
        0.05,

    group =
        NULL,

    struc_zero =
        FALSE,

    neg_lb =
        FALSE,

    alpha =
        alpha,

    n_cl =
        threads,

    verbose =
        TRUE,

    global =
        FALSE,

    pairwise =
        FALSE,

    dunnet =
        FALSE,

    trend =
        FALSE
)


############################################################
# Extract primary result
############################################################

results <- fit$res


if (
    is.null(results) ||
    nrow(results) == 0
) {

    stop(
        "ANCOM-BC2 returned no primary results."
    )
}


############################################################
# Find Group effect column
############################################################

lfc_columns <- grep(
    paste0(
        "^lfc_",
        group_column
    ),
    colnames(results),
    value = TRUE
)


if (
    length(lfc_columns) != 1
) {

    stop(
        paste0(
            "Could not uniquely identify the ",
            group_column,
            " coefficient. Candidates: ",
            paste(
                lfc_columns,
                collapse = ", "
            )
        )
    )
}


lfc_column <- lfc_columns[1]


coefficient <- sub(
    "^lfc_",
    "",
    lfc_column
)


se_column <- paste0(
    "se_",
    coefficient
)

w_column <- paste0(
    "W_",
    coefficient
)

p_column <- paste0(
    "p_",
    coefficient
)

q_column <- paste0(
    "q_",
    coefficient
)

diff_column <- paste0(
    "diff_",
    coefficient
)

sensitivity_column <- paste0(
    "passed_ss_",
    coefficient
)


required_result_columns <- c(
    "taxon",
    lfc_column,
    se_column,
    w_column,
    p_column,
    q_column,
    diff_column
)


missing_result_columns <- setdiff(
    required_result_columns,
    colnames(results)
)


if (
    length(missing_result_columns) > 0
) {

    stop(
        "Missing ANCOM-BC2 result columns: ",
        paste(
            missing_result_columns,
            collapse = ", "
        )
    )
}


############################################################
# Build clean output
############################################################

if (
    sensitivity_column
    %in%
    colnames(results)
) {

    passed_sensitivity <- results[
        [
            sensitivity_column
        ]
    ]

} else {

    passed_sensitivity <- rep(
        NA,
        nrow(results)
    )
}


clean_results <- data.frame(

    FeatureID =
        as.character(
            results$taxon
        ),

    EffectSize =
        as.numeric(
            results[
                [
                    lfc_column
                ]
            ]
        ),

    SE =
        as.numeric(
            results[
                [
                    se_column
                ]
            ]
        ),

    W =
        as.numeric(
            results[
                [
                    w_column
                ]
            ]
        ),

    Pvalue =
        as.numeric(
            results[
                [
                    p_column
                ]
            ]
        ),

    FDR =
        as.numeric(
            results[
                [
                    q_column
                ]
            ]
        ),

    Differential =
        as.logical(
            results[
                [
                    diff_column
                ]
            ]
        ),

    PassedSensitivity =
        as.logical(
            passed_sensitivity
        ),

    stringsAsFactors =
        FALSE
)


############################################################
# Taxonomy annotation
############################################################

taxonomy <- read.delim(
    taxonomy_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


feature_column_candidates <- c(
    "Feature ID",
    "FeatureID",
    "#OTU ID"
)


feature_column <- feature_column_candidates[
    feature_column_candidates
    %in%
    colnames(taxonomy)
][1]


taxon_column_candidates <- c(
    "Taxon",
    "Taxonomy"
)


taxon_column <- taxon_column_candidates[
    taxon_column_candidates
    %in%
    colnames(taxonomy)
][1]


if (
    length(feature_column) == 1 &&
    !is.na(feature_column) &&
    length(taxon_column) == 1 &&
    !is.na(taxon_column)
) {

    clean_results$Taxon <- taxonomy[
        [
            taxon_column
        ]
    ][
        match(
            clean_results$FeatureID,
            taxonomy[
                [
                    feature_column
                ]
            ]
        )
    ]

} else {

    clean_results$Taxon <- NA_character_
}


############################################################
# Direction
############################################################

clean_results$Direction <- ifelse(

    clean_results$EffectSize > 0,

    paste0(
        case_group,
        "_higher"
    ),

    ifelse(

        clean_results$EffectSize < 0,

        paste0(
            reference_group,
            "_higher"
        ),

        "no_change"
    )
)


############################################################
# Robust significance
############################################################

clean_results$RobustSignificant <- (

    !is.na(
        clean_results$FDR
    )

    &

    clean_results$FDR
    <=
    alpha

    &

    clean_results$Differential

    &

    (
        is.na(
            clean_results$PassedSensitivity
        )
        |
        clean_results$PassedSensitivity
    )
)


clean_results <- clean_results[
    order(
        clean_results$FDR,
        na.last = TRUE
    ),
    ,
    drop = FALSE
]


############################################################
# Write results
############################################################

write.table(
    clean_results,
    file.path(
        output_dir,
        "all_results.tsv"
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


significant_results <- clean_results[
    clean_results$RobustSignificant,
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
# Summary
############################################################

summary_table <- data.frame(

    Parameter = c(
        "Method",
        "Model",
        "ReferenceGroup",
        "CaseGroup",
        "EligibleStudies",
        "Samples",
        "FeaturesTested",
        "SignificantFeatures",
        "PrevalenceCutoff",
        "Alpha",
        "PAdjustment"
    ),

    Value = c(
        "ANCOM-BC2",
        fix_formula,
        reference_group,
        case_group,
        length(
            eligible_studies
        ),
        ncol(
            counts
        ),
        nrow(
            clean_results
        ),
        nrow(
            significant_results
        ),
        prevalence,
        alpha,
        p_adjust_method
    ),

    stringsAsFactors =
        FALSE
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


cat(
    "\nANCOM-BC2 completed successfully.\n"
)

cat(
    "Eligible studies:",
    length(
        eligible_studies
    ),
    "\n"
)

cat(
    "Samples:",
    ncol(
        counts
    ),
    "\n"
)

cat(
    "Features tested:",
    nrow(
        clean_results
    ),
    "\n"
)

cat(
    "Robust significant features:",
    nrow(
        significant_results
    ),
    "\n"
)