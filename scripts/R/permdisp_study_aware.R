#!/usr/bin/env Rscript

library(dplyr)
library(vegan)


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)

if (length(args) != 14) {

    stop(
        paste(
            "Usage: Rscript permdisp_study_aware.R",
            "<distance.tsv>",
            "<metadata.tsv>",
            "<metric>",
            "<per_study_output.tsv>",
            "<summary_output.tsv>",
            "<eligibility_output.tsv>",
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

per_study_output <- args[4]

summary_output <- args[5]

eligibility_output <- args[6]

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
        "Invalid seed."
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
            "Distance matrix row names",
            "and column names do not match."
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
# Match metadata and distance matrix
############################################################

distance_samples <- rownames(
    distance_matrix
)


missing_metadata_samples <- setdiff(
    distance_samples,
    metadata$SampleID
)


if (
    length(
        missing_metadata_samples
    ) > 0
) {

    stop(
        length(
            missing_metadata_samples
        ),
        " distance samples are missing from metadata."
    )
}


metadata <- metadata %>%
    filter(
        SampleID %in%
        distance_samples
    )


############################################################
# Standard columns
############################################################

metadata$Study <- metadata[
    [study_column]
]

metadata$Group <- metadata[
    [group_column]
]


############################################################
# Filter incomplete samples
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

            TRUE ~ "Eligible"
        )
    )


############################################################
# Output directories
############################################################

dir.create(
    dirname(
        per_study_output
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


dir.create(
    dirname(
        summary_output
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


dir.create(
    dirname(
        eligibility_output
    ),
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Save eligibility
############################################################

write.table(
    study_eligibility,
    eligibility_output,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


############################################################
# Eligible studies
############################################################

eligible_studies <- study_eligibility %>%
    filter(
        Eligible
    )


n_eligible_studies <- nrow(
    eligible_studies
)


if (
    n_eligible_studies < min_studies
) {

    stop(
        paste0(
            "Insufficient eligible studies for Study-aware PERMDISP metric '",
            metric_name,
            "'. Found ",
            n_eligible_studies,
            " eligible studies, but at least ",
            min_studies,
            " are required."
        )
    )
}


############################################################
# Storage
############################################################

results <- data.frame()


############################################################
# PERMDISP within each Study
############################################################

for (
    i in seq_len(
        nrow(
            eligible_studies
        )
    )
) {

    study_name <- eligible_studies$Study[i]


    study_metadata <- metadata %>%
        filter(
            Study == study_name
        )


    ########################################################
    # Preserve metadata ordering
    ########################################################

    study_samples <-
        study_metadata$SampleID


    study_distance_matrix <-
        distance_matrix[
            study_samples,
            study_samples,
            drop = FALSE
        ]


    if (
        !identical(
            rownames(
                study_distance_matrix
            ),
            study_metadata$SampleID
        )
    ) {

        stop(
            "Sample order mismatch for study: ",
            study_name
        )
    }


    ########################################################
    # Group factor
    ########################################################

    study_metadata$Group <- factor(
        study_metadata$Group,
        levels = c(
            reference_group,
            case_group
        )
    )


    study_metadata$Group <-
        droplevels(
            study_metadata$Group
        )


    if (
        nlevels(
            study_metadata$Group
        ) != 2
    ) {

        warning(
            "Skipping study ",
            study_name,
            ": both groups are not present."
        )

        next
    }


    ########################################################
    # Convert to dist
    ########################################################

    distance_object <- as.dist(
        study_distance_matrix
    )


    ########################################################
    # PERMDISP
    #
    # Median is more robust than centroid.
    # Bias adjustment is useful with small /
    # unequal group sizes.
    ########################################################

    dispersion_model <- vegan::betadisper(
        distance_object,
        group =
            study_metadata$Group,
        type = "median",
        bias.adjust = TRUE
    )


    ########################################################
    # Reproducible permutation test
    ########################################################

    set.seed(
        seed + i - 1
    )


    dispersion_test <- vegan::permutest(
        dispersion_model,
        permutations =
            permutations,
        pairwise = FALSE
    )


    ########################################################
    # Extract test result
    ########################################################

    test_table <- as.data.frame(
        dispersion_test$tab
    )


    if (
        nrow(
            test_table
        ) < 1
    ) {

        warning(
            "No PERMDISP test result for study: ",
            study_name
        )

        next
    }


    F_value <- as.numeric(
        test_table[1, "F"]
    )


    p_value <- as.numeric(
        test_table[
            1,
            "Pr(>F)"
        ]
    )


    ########################################################
    # Distances to study-specific group medians
    ########################################################

    distances_to_center <-
        dispersion_model$distances


    dispersion_data <- data.frame(

        SampleID =
            study_metadata$SampleID,

        Group =
            study_metadata$Group,

        Distance =
            distances_to_center,

        stringsAsFactors = FALSE
    )


    ########################################################
    # Group summaries
    ########################################################

    reference_distances <-
        dispersion_data$Distance[
            dispersion_data$Group ==
            reference_group
        ]


    case_distances <-
        dispersion_data$Distance[
            dispersion_data$Group ==
            case_group
        ]


    mean_reference <- mean(
        reference_distances,
        na.rm = TRUE
    )


    mean_case <- mean(
        case_distances,
        na.rm = TRUE
    )


    median_reference <- median(
        reference_distances,
        na.rm = TRUE
    )


    median_case <- median(
        case_distances,
        na.rm = TRUE
    )


    difference <-
        mean_case -
        mean_reference


    ratio <- if (
        is.finite(mean_reference) &&
        mean_reference > 0
    ) {

        mean_case /
            mean_reference

    } else {

        NA_real_
    }


    ########################################################
    # Store result
    ########################################################

    study_result <- data.frame(

        Metric =
            metric_name,

        Study =
            study_name,

        Reference_Group =
            reference_group,

        Case_Group =
            case_group,

        N_Reference =
            length(
                reference_distances
            ),

        N_Case =
            length(
                case_distances
            ),

        Mean_Distance_Reference =
            mean_reference,

        Mean_Distance_Case =
            mean_case,

        Median_Distance_Reference =
            median_reference,

        Median_Distance_Case =
            median_case,

        Mean_Difference_Case_Minus_Reference =
            difference,

        Dispersion_Ratio_Case_Reference =
            ratio,

        F =
            F_value,

        Pvalue =
            p_value,

        Permutations =
            permutations,

        Seed =
            seed + i - 1,

        stringsAsFactors = FALSE
    )


    results <- rbind(
        results,
        study_result
    )
}


############################################################
# Check results
############################################################

if (nrow(results) == 0) {

    stop(
        "No Study-specific PERMDISP results produced for: ",
        metric_name
    )
}


############################################################
# Multiple-testing correction across Studies
############################################################

results$FDR <- p.adjust(
    results$Pvalue,
    method = "BH"
)


############################################################
# Direction
############################################################

results$Direction <- ifelse(

    results$
        Mean_Difference_Case_Minus_Reference >
        0,

    paste0(
        case_group,
        "_more_dispersed"
    ),

    ifelse(

        results$
            Mean_Difference_Case_Minus_Reference <
            0,

        paste0(
            reference_group,
            "_more_dispersed"
        ),

        "equal"
    )
)


############################################################
# Save per-Study results
############################################################

write.table(
    results,
    per_study_output,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


############################################################
# Combined diagnostic summary
############################################################

summary_result <- data.frame(

    Metric =
        metric_name,

    N_Studies =
        nrow(
            results
        ),

    N_Samples =
        sum(
            results$N_Reference +
            results$N_Case
        ),

    Significant_Raw_P =
        sum(
            results$Pvalue < 0.05,
            na.rm = TRUE
        ),

    Significant_FDR =
        sum(
            results$FDR < 0.05,
            na.rm = TRUE
        ),

    Case_More_Dispersed =
        sum(
            results$
                Mean_Difference_Case_Minus_Reference >
                0,
            na.rm = TRUE
        ),

    Reference_More_Dispersed =
        sum(
            results$
                Mean_Difference_Case_Minus_Reference <
                0,
            na.rm = TRUE
        ),

    Median_Dispersion_Ratio =
        median(
            results$
                Dispersion_Ratio_Case_Reference,
            na.rm = TRUE
        ),

    stringsAsFactors = FALSE
)


############################################################
# Diagnostic flag
############################################################

summary_result$Dispersion_Warning <-

    summary_result$
        Significant_FDR > 0


############################################################
# Save summary
############################################################

write.table(
    summary_result,
    summary_output,
    sep = "\t",
    row.names = FALSE,
    quote = FALSE
)


message(
    "Study-aware PERMDISP completed for: ",
    metric_name
)