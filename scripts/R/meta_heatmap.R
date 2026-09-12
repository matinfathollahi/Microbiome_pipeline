library(dplyr)
library(tidyr)
library(ComplexHeatmap)
library(circlize)


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)

if (length(args) != 3) {

    stop(
        paste(
            "Usage:",
            "meta_heatmap.R",
            "study_effects.tsv",
            "meta_results.tsv",
            "output_dir"
        )
    )
}


study_effects_file <- args[1]

meta_results_file <- args[2]

output_dir <- args[3]


############################################################
# Output directory
############################################################

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Helper:
# Create informative placeholder instead of failing
############################################################

create_placeholder <- function(message) {

    ########################################################
    # PDF
    ########################################################

    pdf(
        file.path(
            output_dir,
            "meta_heatmap.pdf"
        ),
        width = 9,
        height = 6
    )

    plot.new()

    text(
        0.5,
        0.55,
        "Meta-analysis Heatmap",
        cex = 1.6,
        font = 2
    )

    text(
        0.5,
        0.45,
        message,
        cex = 1.1
    )

    dev.off()


    ########################################################
    # PNG
    ########################################################

    png(
        file.path(
            output_dir,
            "meta_heatmap.png"
        ),
        width = 1800,
        height = 1200,
        res = 200
    )

    plot.new()

    text(
        0.5,
        0.55,
        "Meta-analysis Heatmap",
        cex = 1.6,
        font = 2
    )

    text(
        0.5,
        0.45,
        message,
        cex = 1.1
    )

    dev.off()


    ########################################################
    # Status file
    ########################################################

    status <- data.frame(

        Status = "No heatmap generated",

        Reason = message,

        stringsAsFactors = FALSE
    )

    write.table(

        status,

        file.path(
            output_dir,
            "heatmap_status.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )
}


############################################################
# Read study-specific effect sizes
############################################################

study_effects <- read.delim(

    study_effects_file,

    check.names = FALSE,

    stringsAsFactors = FALSE
)


############################################################
# Read final random-effects meta-analysis
############################################################

meta_results <- read.delim(

    meta_results_file,

    check.names = FALSE,

    stringsAsFactors = FALSE
)


############################################################
# Validate study-specific data
############################################################

required_study_cols <- c(

    "FeatureID",

    "Study",

    "EffectSize"
)


missing_study_cols <- setdiff(

    required_study_cols,

    colnames(study_effects)
)


if (length(missing_study_cols) > 0) {

    stop(
        paste(
            "Missing study-effect columns:",
            paste(
                missing_study_cols,
                collapse = ", "
            )
        )
    )
}


############################################################
# Validate meta-analysis results
############################################################

required_meta_cols <- c(

    "FeatureID",

    "EffectSize",

    "FDR"
)


missing_meta_cols <- setdiff(

    required_meta_cols,

    colnames(meta_results)
)


if (length(missing_meta_cols) > 0) {

    stop(
        paste(
            "Missing meta-analysis columns:",
            paste(
                missing_meta_cols,
                collapse = ", "
            )
        )
    )
}


############################################################
# Convert numeric columns
############################################################

study_effects$EffectSize <- suppressWarnings(

    as.numeric(
        study_effects$EffectSize
    )
)


meta_results$EffectSize <- suppressWarnings(

    as.numeric(
        meta_results$EffectSize
    )
)


meta_results$FDR <- suppressWarnings(

    as.numeric(
        meta_results$FDR
    )
)


############################################################
# Remove invalid study effects
############################################################

study_effects <- study_effects %>%

    filter(

        !is.na(FeatureID),

        !is.na(Study),

        is.finite(EffectSize)
    )


############################################################
# Remove invalid meta results
############################################################

meta_results <- meta_results %>%

    filter(

        !is.na(FeatureID),

        is.finite(EffectSize),

        is.finite(FDR)
    )


############################################################
# Select taxa significant in FINAL meta-analysis
#
# Important:
# We use final random-effects FDR,
# NOT study-specific DESeq2 FDR.
############################################################

significant_meta <- meta_results %>%

    filter(
        FDR < 0.05
    ) %>%

    arrange(
        FDR
    )


############################################################
# No significant taxa:
# this is a valid scientific result, NOT an error
############################################################

if (nrow(significant_meta) == 0) {

    message(
        "No taxa were significant in the final ",
        "random-effects meta-analysis (FDR < 0.05)."
    )

    create_placeholder(

        paste(
            "No taxa reached FDR < 0.05",
            "in the final random-effects meta-analysis."
        )
    )

    quit(
        save = "no",
        status = 0
    )
}


############################################################
# Significant taxa
############################################################

significant_taxa <- unique(

    significant_meta$FeatureID
)


############################################################
# Keep study-specific effects only for
# taxa significant in final meta-analysis
############################################################

plot_data <- study_effects %>%

    filter(
        FeatureID %in% significant_taxa
    )


############################################################
# Check matching study effects
############################################################

if (nrow(plot_data) == 0) {

    message(
        "Significant meta-analysis taxa had no ",
        "matching study-specific effect estimates."
    )

    create_placeholder(

        paste(
            "Significant taxa were found,",
            "but no matching study-specific",
            "effect estimates were available."
        )
    )

    quit(
        save = "no",
        status = 0
    )
}


############################################################
# Aggregate duplicated Study/Taxon combinations
# if they somehow exist
############################################################

plot_data <- plot_data %>%

    group_by(
        FeatureID,
        Study
    ) %>%

    summarise(

        EffectSize = mean(
            EffectSize,
            na.rm = TRUE
        ),

        .groups = "drop"
    )


############################################################
# Build matrix
############################################################

mat_df <- plot_data %>%

    pivot_wider(

        names_from = Study,

        values_from = EffectSize
    )


############################################################
# Check matrix
############################################################

if (nrow(mat_df) == 0) {

    create_placeholder(
        "No valid values were available for the heatmap."
    )

    quit(
        save = "no",
        status = 0
    )
}


rownames(mat_df) <- mat_df$FeatureID
mat_df$FeatureID <- NULL


mat <- as.matrix(
    mat_df
)


storage.mode(
    mat
) <- "numeric"


############################################################
# Remove completely missing rows
############################################################

keep_rows <- apply(

    mat,

    1,

    function(x) {

        any(
            is.finite(x)
        )

    }
)


mat <- mat[
    keep_rows,
    ,
    drop = FALSE
]


############################################################
# Remove completely missing columns
############################################################

keep_cols <- apply(

    mat,

    2,

    function(x) {

        any(
            is.finite(x)
        )

    }
)


mat <- mat[
    ,
    keep_cols,
    drop = FALSE
]


############################################################
# Final matrix validation
############################################################

if (
    nrow(mat) == 0
    || ncol(mat) == 0
) {

    create_placeholder(
        "No valid study-specific effect matrix could be constructed."
    )

    quit(
        save = "no",
        status = 0
    )
}


############################################################
# Color range
############################################################

finite_values <- mat[
    is.finite(mat)
]


if (length(finite_values) == 0) {

    create_placeholder(
        "No finite effect sizes were available."
    )

    quit(
        save = "no",
        status = 0
    )
}


lim <- max(
    abs(finite_values),
    na.rm = TRUE
)


if (
    !is.finite(lim)
    || lim == 0
) {

    lim <- 1
}


col_fun <- colorRamp2(

    c(
        -lim,
        0,
        lim
    ),

    c(
        "blue",
        "white",
        "red"
    )
)


############################################################
# Clustering
#
# If only one taxon or one study exists,
# disable clustering instead of failing.
############################################################

cluster_rows_flag <- (
    nrow(mat) > 1
)


cluster_columns_flag <- (
    ncol(mat) > 1
)


############################################################
# PDF
############################################################

pdf(

    file.path(
        output_dir,
        "meta_heatmap.pdf"
    ),

    width = 9,

    height = max(
        6,
        min(
            18,
            4 + 0.25 * nrow(mat)
        )
    )
)


ht <- Heatmap(

    mat,

    name = "Effect",

    col = col_fun,

    na_col = "grey90",

    cluster_rows =
        cluster_rows_flag,

    cluster_columns =
        cluster_columns_flag,

    row_names_gp =
        grid::gpar(
            fontsize = 8
        ),

    column_names_gp =
        grid::gpar(
            fontsize = 10
        ),

    heatmap_legend_param =
        list(
            title = "Effect Size"
        )
)


draw(
    ht
)


dev.off()


############################################################
# PNG
############################################################

png(

    file.path(
        output_dir,
        "meta_heatmap.png"
    ),

    width = 2400,

    height = max(
        1600,
        min(
            5000,
            1000 + 80 * nrow(mat)
        )
    ),

    res = 300
)


ht <- Heatmap(

    mat,

    name = "Effect",

    col = col_fun,

    na_col = "grey90",

    cluster_rows =
        cluster_rows_flag,

    cluster_columns =
        cluster_columns_flag,

    row_names_gp =
        grid::gpar(
            fontsize = 8
        ),

    column_names_gp =
        grid::gpar(
            fontsize = 10
        ),

    heatmap_legend_param =
        list(
            title = "Effect Size"
        )
)


draw(
    ht
)


dev.off()


############################################################
# Save taxa used in heatmap
############################################################

heatmap_taxa <- significant_meta %>%
    filter(
        FeatureID %in% rownames(mat)
    ) %>%
    select(
        FeatureID,
        EffectSize,
        FDR
    )

write.table(

    heatmap_taxa,

    file.path(
        output_dir,
        "heatmap_taxa.tsv"
    ),

    sep = "\t",

    quote = FALSE,

    row.names = FALSE
)


############################################################
# Status
############################################################

status <- data.frame(

    Status = "Heatmap generated",

    SignificantTaxa = nrow(mat),

    Studies = ncol(mat),

    stringsAsFactors = FALSE
)


write.table(

    status,

    file.path(
        output_dir,
        "heatmap_status.tsv"
    ),

    sep = "\t",

    quote = FALSE,

    row.names = FALSE
)


############################################################
# Done
############################################################

message(
    "Meta-analysis heatmap generated successfully."
)

message(
    "Significant taxa: ",
    nrow(mat)
)

message(
    "Studies: ",
    ncol(mat)
)