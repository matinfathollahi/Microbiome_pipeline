#!/usr/bin/env Rscript

library(vegan)
library(dplyr)


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)

if (length(args) != 14) {

    stop(
        paste(
            "Usage: Rscript permanova_study_aware.R",
            "<distance.tsv>",
            "<metadata.tsv>",
            "<metric>",
            "<result.tsv>",
            "<group_effect.tsv>",
            "<eligibility.tsv>",
            "<study_column>",
            "<group_column>",
            "<reference_group>",
            "<case_group>",
            "<min_samples_per_group>",
            "<min_studies>",
            "<permutations>",
            "<seed>"
        )
    )
}


distance_file <- args[1]

metadata_file <- args[2]

metric_name <- args[3]

result_file <- args[4]

group_effect_file <- args[5]

eligibility_file <- args[6]

study_column <- args[7]

group_column <- args[8]

reference_group <- args[9]

case_group <- args[10]

min_samples_per_group <- as.integer(
    args[11]
)

min_studies <- as.integer(
    args[12]
)

permutations <- as.integer(
    args[13]
)

seed <- as.integer(
    args[14]
)


############################################################
# Validate arguments
############################################################

if (!file.exists(distance_file)) {

    stop(
        "Distance matrix not found: ",
        distance_file
    )
}


if (!file.exists(metadata_file)) {

    stop(
        "Metadata file not found: ",
        metadata_file
    )
}


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
    is.na(permutations) ||
    permutations < 1
) {

    stop(
        "permutations must be >= 1."
    )
}


if (is.na(seed)) {

    stop(
        "Invalid random seed."
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


required_metadata <- c(
    "SampleID",
    study_column,
    group_column
)


missing_metadata <- setdiff(
    required_metadata,
    colnames(metadata)
)


if (length(missing_metadata) > 0) {

    stop(
        "Missing metadata columns: ",
        paste(
            missing_metadata,
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

metadata[[study_column]] <- trimws(
    as.character(
        metadata[[study_column]]
    )
)

metadata[[group_column]] <- trimws(
    as.character(
        metadata[[group_column]]
    )
)


############################################################
# Duplicate SampleID check
############################################################

duplicate_ids <- unique(
    metadata$SampleID[
        duplicated(
            metadata$SampleID
        )
    ]
)


if (length(duplicate_ids) > 0) {

    stop(
        "Duplicate SampleID values found in metadata: ",
        paste(
            head(
                duplicate_ids,
                20
            ),
            collapse = ", "
        )
    )
}


############################################################
# Read distance matrix
############################################################

distance_matrix <- read.delim(
    distance_file,
    row.names = 1,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


distance_matrix <- as.matrix(
    distance_matrix
)


storage.mode(
    distance_matrix
) <- "double"


############################################################
# Validate distance matrix
############################################################

if (
    nrow(distance_matrix) !=
    ncol(distance_matrix)
) {

    stop(
        "Distance matrix must be square."
    )
}


if (
    !setequal(
        rownames(distance_matrix),
        colnames(distance_matrix)
    )
) {

    stop(
        paste(
            "Row names and column names",
            "of distance matrix do not match."
        )
    )
}


distance_matrix <- distance_matrix[
    rownames(distance_matrix),
    rownames(distance_matrix),
    drop = FALSE
]


if (
    any(
        !is.finite(
            distance_matrix
        )
    )
) {

    stop(
        "Distance matrix contains non-finite values."
    )
}


if (
    max(
        abs(
            distance_matrix -
            t(distance_matrix)
        )
    ) > 1e-8
) {

    stop(
        "Distance matrix is not symmetric."
    )
}


if (
    any(
        abs(
            diag(distance_matrix)
        ) > 1e-8
    )
) {

    stop(
        "Distance matrix diagonal is not zero."
    )
}


############################################################
# Check metadata coverage
############################################################

distance_samples <- rownames(
    distance_matrix
)


missing_from_metadata <- setdiff(
    distance_samples,
    metadata$SampleID
)


if (
    length(
        missing_from_metadata
    ) > 0
) {

    stop(
        length(
            missing_from_metadata
        ),
        " distance-matrix samples are missing from metadata."
    )
}


############################################################
# Restrict metadata to distance samples
############################################################

metadata <- metadata %>%
    filter(
        SampleID %in% distance_samples
    )


############################################################
# Standard analysis columns
############################################################

metadata$Study <- metadata[[study_column]]

metadata$Group <- metadata[[group_column]]


############################################################
# Remove incomplete / irrelevant samples
############################################################

metadata <- metadata %>%
    filter(
        !is.na(Study),
        !is.na(Group),
        Study != "",
        Group != "",
        Group %in% c(
            reference_group,
            case_group
        )
    )


############################################################
# Study eligibility
############################################################

study_eligibility <- metadata %>%
    group_by(Study) %>%
    summarise(

        N_Reference = sum(
            Group ==
            reference_group
        ),

        N_Case = sum(
            Group ==
            case_group
        ),

        .groups = "drop"
    ) %>%

    mutate(

        Eligible =
            N_Reference >=
            min_samples_per_group &
            N_Case >=
            min_samples_per_group,

        Reason = case_when(

            N_Reference <
                min_samples_per_group &
            N_Case <
                min_samples_per_group ~

                "Insufficient samples in both groups",

            N_Reference <
                min_samples_per_group ~

                paste0(
                    "Insufficient ",
                    reference_group,
                    " samples"
                ),

            N_Case <
                min_samples_per_group ~

                paste0(
                    "Insufficient ",
                    case_group,
                    " samples"
                ),

            TRUE ~
                "Eligible"
        )
    )


############################################################
# Save eligibility
############################################################

dir.create(
    dirname(
        eligibility_file
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


write.table(
    study_eligibility,
    eligibility_file,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


############################################################
# Select eligible studies
############################################################

eligible_studies <- study_eligibility %>%
    filter(
        Eligible
    )


if (
    nrow(
        eligible_studies
    ) < min_studies
) {

    stop(
        "Not enough eligible studies for ",
        metric_name,
        ": ",
        nrow(
            eligible_studies
        ),
        " available; ",
        min_studies,
        " required."
    )
}


############################################################
# Restrict metadata to eligible studies
############################################################

analysis_metadata <- metadata %>%
    filter(
        Study %in%
        eligible_studies$Study
    )


############################################################
# Match distance matrix to metadata
############################################################

analysis_samples <- analysis_metadata$SampleID


distance_matrix <- distance_matrix[
    analysis_samples,
    analysis_samples,
    drop = FALSE
]


############################################################
# Final order check
############################################################

if (
    !identical(
        rownames(
            distance_matrix
        ),
        analysis_metadata$SampleID
    )
) {

    stop(
        "Metadata and distance matrix sample order mismatch."
    )
}


############################################################
# Factors
############################################################

analysis_metadata$Group <- factor(
    analysis_metadata$Group,
    levels = c(
        reference_group,
        case_group
    )
)


analysis_metadata$Study <- factor(
    analysis_metadata$Study
)


if (
    nlevels(
        droplevels(
            analysis_metadata$Group
        )
    ) < 2
) {

    stop(
        "Both groups are required."
    )
}


if (
    nlevels(
        droplevels(
            analysis_metadata$Study
        )
    ) < min_studies
) {

    stop(
        "Not enough studies after filtering."
    )
}


############################################################
# Convert to dist
############################################################

distance_object <- as.dist(
    distance_matrix
)


############################################################
# Study-aware PERMANOVA
#
# Study is partialled out.
# Permutations are restricted within Study.
############################################################

set.seed(
    seed
)


permanova <- vegan::adonis2(

    distance_object ~
        Group +
        Condition(Study),

    data =
        analysis_metadata,

    permutations =
        permutations,

    by =
        "margin",

    strata =
        analysis_metadata$Study
)


############################################################
# Convert results
############################################################

result <- as.data.frame(
    permanova
)


result$Term <- rownames(
    result
)


rownames(
    result
) <- NULL


result$Metric <- metric_name

result$N_Samples <- nrow(
    analysis_metadata
)

result$N_Studies <- nlevels(
    analysis_metadata$Study
)

result$Reference_Group <-
    reference_group

result$Case_Group <-
    case_group

result$Permutations <-
    permutations

result$Seed <-
    seed

result$Formula <-
    "Group + Condition(Study)"


############################################################
# Reorder columns
############################################################

first_columns <- c(
    "Metric",
    "Term",
    "N_Samples",
    "N_Studies",
    "Reference_Group",
    "Case_Group",
    "Permutations",
    "Seed",
    "Formula"
)


result <- result[
    ,
    c(
        first_columns,
        setdiff(
            colnames(result),
            first_columns
        )
    )
]


############################################################
# Save full PERMANOVA result
############################################################

dir.create(
    dirname(
        result_file
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


write.table(
    result,
    result_file,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


############################################################
# Extract primary Group effect
############################################################

group_result <- result %>%
    filter(
        Term == "Group"
    )


if (
    nrow(
        group_result
    ) != 1
) {

    stop(
        "Could not uniquely extract Group PERMANOVA result."
    )
}


############################################################
# Save primary Group result
############################################################

write.table(
    group_result,
    group_effect_file,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


message(
    "Study-aware PERMANOVA completed for: ",
    metric_name
)