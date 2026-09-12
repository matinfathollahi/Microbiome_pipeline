library(dplyr)
library(openxlsx)


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)


if (length(args) != 4) {

    stop(
        paste(
            "Usage:",
            "meta_summary.R",
            "meta.tsv",
            "bias.tsv",
            "taxonomy.tsv",
            "output_directory"
        )
    )
}


meta_file <- args[1]
bias_file <- args[2]
taxonomy_file <- args[3]
output_dir <- args[4]


############################################################
# Output directory
############################################################

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Read input files
############################################################

meta <- read.delim(
    meta_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


bias <- read.delim(
    bias_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


taxonomy <- read.delim(
    taxonomy_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


############################################################
# Standardize taxonomy FeatureID column
############################################################

if ("Feature ID" %in% names(taxonomy)) {

    names(taxonomy)[
        names(taxonomy) == "Feature ID"
    ] <- "FeatureID"

} else if (!"FeatureID" %in% names(taxonomy)) {

    stop(
        paste(
            "Taxonomy table must contain",
            "'FeatureID' or 'Feature ID'."
        )
    )
}


############################################################
# Validate required columns
############################################################

required_meta_columns <- c(
    "FeatureID",
    "EffectSize",
    "FDR",
    "I2",
    "Tau2"
)


missing_meta_columns <- setdiff(
    required_meta_columns,
    names(meta)
)


if (length(missing_meta_columns) > 0) {

    stop(
        paste(
            "Missing required columns in meta file:",
            paste(
                missing_meta_columns,
                collapse = ", "
            )
        )
    )
}


if (!"FeatureID" %in% names(bias)) {

    stop(
        "FeatureID column not found in bias file."
    )
}


if (!"Taxon" %in% names(taxonomy)) {

    stop(
        "Taxon column not found in taxonomy file."
    )
}


############################################################
# Validate FeatureID uniqueness
############################################################

if (anyDuplicated(meta$FeatureID)) {

    stop(
        "Duplicated FeatureID values found in meta results."
    )
}


if (anyDuplicated(bias$FeatureID)) {

    stop(
        "Duplicated FeatureID values found in bias results."
    )
}


if (anyDuplicated(taxonomy$FeatureID)) {

    stop(
        "Duplicated FeatureID values found in taxonomy table."
    )
}


############################################################
# Prepare taxonomy annotation
############################################################

taxonomy_annotation <- taxonomy %>%
    select(
        FeatureID,
        Taxon,
        any_of("Confidence")
    )


############################################################
# Join meta-analysis and publication-bias results
############################################################

meta_summary <- left_join(
    meta,
    bias,
    by = "FeatureID"
)


############################################################
# Add taxonomy annotation
############################################################

meta_summary <- meta_summary %>%
    left_join(
        taxonomy_annotation,
        by = "FeatureID"
    )


############################################################
# Put identifiers first
############################################################

meta_summary <- meta_summary %>%
    relocate(
        FeatureID,
        Taxon
    )


############################################################
# Sort by FDR
############################################################

meta_summary <- meta_summary %>%
    arrange(
        FDR
    )


############################################################
# Write complete TSV
############################################################

write.table(
    meta_summary,

    file.path(
        output_dir,
        "meta_summary.tsv"
    ),

    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Write Excel
############################################################

write.xlsx(
    meta_summary,

    file.path(
        output_dir,
        "meta_summary.xlsx"
    ),

    overwrite = TRUE
)


############################################################
# Significant features
############################################################

sig <- meta_summary %>%
    filter(
        !is.na(FDR),
        FDR < 0.05
    )


write.table(
    sig,

    file.path(
        output_dir,
        "meta_significant.tsv"
    ),

    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Top 20 features
############################################################

top20 <- meta_summary %>%
    slice_head(
        n = 20
    )


write.table(
    top20,

    file.path(
        output_dir,
        "meta_top20.tsv"
    ),

    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)


############################################################
# Summary statistics
############################################################

stats_file <- file.path(
    output_dir,
    "meta_summary_statistics.txt"
)


sink(stats_file)

cat(
    "Number of features:",
    nrow(meta_summary),
    "\n"
)


cat(
    "Significant features:",
    sum(
        meta_summary$FDR < 0.05,
        na.rm = TRUE
    ),
    "\n"
)


cat(
    "Features with taxonomy annotation:",
    sum(
        !is.na(meta_summary$Taxon) &
        meta_summary$Taxon != ""
    ),
    "\n"
)


cat(
    "Median Effect Size:",
    median(
        meta_summary$EffectSize,
        na.rm = TRUE
    ),
    "\n"
)


cat(
    "Median I2:",
    median(
        meta_summary$I2,
        na.rm = TRUE
    ),
    "\n"
)


cat(
    "Median Tau2:",
    median(
        meta_summary$Tau2,
        na.rm = TRUE
    ),
    "\n"
)


sink()