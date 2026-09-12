#!/usr/bin/env Rscript

library(vegan)
library(ape)
library(ggplot2)

############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)

if (length(args) != 8) {

    stop(
        paste(
            "Usage:",
            "batch_before_after_diagnostics.R",
            "<before_clr.tsv>",
            "<after_corrected.tsv>",
            "<metadata.tsv>",
            "<batch_variable>",
            "<group_variable>",
            "<variance_variables_csv>",
            "<permutations>",
            "<output_dir>"
        )
    )
}

before_file <- args[1]
after_file <- args[2]
metadata_file <- args[3]
batch_variable <- args[4]
group_variable <- args[5]

variance_variables <- trimws(
    strsplit(
        args[6],
        ","
    )[[1]]
)

permutations <- as.integer(
    args[7]
)

output_dir <- args[8]


if (
    is.na(permutations) ||
    permutations < 99
) {

    stop(
        "Invalid number of PERMANOVA permutations."
    )
}


############################################################
# Output directories
############################################################

before_dir <- file.path(
    output_dir,
    "before"
)

after_dir <- file.path(
    output_dir,
    "after"
)

summary_dir <- file.path(
    output_dir,
    "summary"
)


dir.create(
    before_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

dir.create(
    after_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

dir.create(
    summary_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Read feature matrix
#
# Input:
# rows = features
# columns = samples
#
# Returned:
# rows = samples
# columns = features
############################################################

read_feature_matrix <- function(file) {

    if (!file.exists(file)) {

        stop(
            "Feature table not found: ",
            file
        )
    }

    table <- read.delim(

        file,

        row.names = 1,

        check.names = FALSE
    )

    X <- t(
        as.matrix(
            table
        )
    )

    storage.mode(
        X
    ) <- "double"


    if (anyDuplicated(
        rownames(X)
    )) {

        stop(
            "Duplicate sample IDs detected in: ",
            file
        )
    }


    if (anyDuplicated(
        colnames(X)
    )) {

        stop(
            "Duplicate feature IDs detected in: ",
            file
        )
    }


    if (
        any(
            !is.finite(X)
        )
    ) {

        stop(
            "NA/Inf values detected in: ",
            file
        )
    }


    return(
        X
    )
}


############################################################
# Read data
############################################################

before <- read_feature_matrix(
    before_file
)

after <- read_feature_matrix(
    after_file
)


############################################################
# Check feature compatibility
############################################################

if (
    !setequal(
        colnames(before),
        colnames(after)
    )
) {

    stop(
        "Before and after tables do not contain "
        "the same features."
    )
}


after <- after[
    ,
    colnames(before),
    drop = FALSE
]


############################################################
# Check sample compatibility
############################################################

if (
    !setequal(
        rownames(before),
        rownames(after)
    )
) {

    stop(
        "Before and after tables do not contain "
        "the same samples."
    )
}


after <- after[
    rownames(before),
    ,
    drop = FALSE
]


############################################################
# Metadata
############################################################

if (!file.exists(
    metadata_file
)) {

    stop(
        "Metadata not found: ",
        metadata_file
    )
}


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

    colnames(metadata)
)


if (
    length(
        missing_columns
    ) > 0
) {

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


if (
    anyDuplicated(
        metadata$SampleID
    )
) {

    stop(
        "Duplicate SampleID values in metadata."
    )
}


idx <- match(

    rownames(before),

    metadata$SampleID
)


if (
    any(
        is.na(idx)
    )
) {

    stop(
        "Some feature-table samples are missing "
        "from metadata."
    )
}


metadata <- metadata[idx, , drop = FALSE]


if (
    !identical(
        rownames(before),
        metadata$SampleID
    )
) {

    stop(
        "Metadata/sample alignment failed."
    )
}


metadata[[batch_variable]] <- factor(metadata[[batch_variable]])


metadata[[group_variable]] <- factor(metadata[[group_variable]])


if (
    nlevels(
        metadata[[batch_variable]]) < 2) {

    stop(
        "Batch variable must have at least two levels."
    )
}


############################################################
# Remove zero-variance features
############################################################

remove_zero_variance <- function(X) {

    variances <- apply(

        X,

        2,

        var
    )


    keep <- (

        is.finite(
            variances
        )

        &

        variances > 0
    )


    X <- X[
        ,
        keep,
        drop = FALSE
    ]


    if (
        ncol(X) == 0
    ) {

        stop(
            "No non-zero-variance features remain."
        )
    }


    X
}


############################################################
# PCA
############################################################

run_pca <- function(
    X,
    metadata,
    output_dir,
    stage
) {

    dir.create(
        file.path(
            output_dir,
            "pca"
        ),
        recursive = TRUE,
        showWarnings = FALSE
    )


    X <- remove_zero_variance(
        X
    )


    pca <- prcomp(

        X,

        center = TRUE,

        scale. = TRUE
    )


    scores <- data.frame(

        SampleID =
            rownames(X),

        PC1 =
            pca$x[, 1],

        stringsAsFactors = FALSE
    )


    if (
        ncol(
            pca$x
        ) >= 2
    ) {

        scores$PC2 <- (
            pca$x[, 2]
        )

    } else {

        scores$PC2 <- 0
    }


    variance <- (

        100
        *
        pca$sdev^2
        /
        sum(
            pca$sdev^2
        )
    )


    scores <- cbind(

        scores,

        metadata[
            match(
                scores$SampleID,
                metadata$SampleID
            ),
            setdiff(
                names(metadata),
                "SampleID"
            ),
            drop = FALSE
        ]
    )


    write.table(

        scores,

        file.path(
            output_dir,
            "pca",
            "pca_scores.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )


    write.table(

        data.frame(

            PC =
                paste0(
                    "PC",
                    seq_along(
                        variance
                    )
                ),

            Variance =
                variance
        ),

        file.path(
            output_dir,
            "pca",
            "pca_variance.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )


    pc2_variance <- ifelse(

        length(variance) >= 2,

        variance[2],

        0
    )


    p <- ggplot(

        scores,

        aes(

            x = PC1,

            y = PC2,

            color = .data[[batch_variable]],

            shape = .data[[group_variable]]
        )

    ) +

        geom_point(
            size = 3,
            alpha = 0.85
        ) +

        theme_classic(
            base_size = 14
        ) +

        labs(

            title =
                paste(
                    "PCA",
                    stage
                ),

            color =
                batch_variable,

            shape =
                group_variable,

            x =
                sprintf(
                    "PC1 (%.2f%%)",
                    variance[1]
                ),

            y =
                sprintf(
                    "PC2 (%.2f%%)",
                    pc2_variance
                )
        )


    ggsave(

        file.path(
            output_dir,
            "pca",
            "pca.pdf"
        ),

        p,

        width = 7,

        height = 6
    )


    ggsave(

        file.path(
            output_dir,
            "pca",
            "pca.png"
        ),

        p,

        width = 7,

        height = 6,

        dpi = 300
    )
}


############################################################
# Euclidean distance in CLR space
#
# Before correction:
# Euclidean(CLR) = Aitchison distance
#
# After correction:
# Euclidean distance is used in the corrected CLR space.
############################################################

calculate_distance <- function(
    X,
    output_dir
) {

    dir.create(

        file.path(
            output_dir,
            "distance"
        ),

        recursive = TRUE,

        showWarnings = FALSE
    )


    distance <- dist(

        X,

        method = "euclidean"
    )


    distance_matrix <- as.matrix(
        distance
    )


    write.table(

        distance_matrix,

        file.path(
            output_dir,
            "distance",
            "euclidean_clr_distance.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        col.names = NA
    )


    distance
}


############################################################
# PCoA
############################################################

run_pcoa <- function(
    distance,
    metadata,
    output_dir,
    stage
) {

    dir.create(

        file.path(
            output_dir,
            "pcoa"
        ),

        recursive = TRUE,

        showWarnings = FALSE
    )


    pcoa_result <- ape::pcoa(
        distance
    )


    coordinates <- as.data.frame(

        pcoa_result$vectors[
            ,
            1:min(
                2,
                ncol(
                    pcoa_result$vectors
                )
            ),
            drop = FALSE
        ]
    )


    if (
        ncol(
            coordinates
        ) == 1
    ) {

        coordinates$Axis.2 <- 0
    }


    names(
        coordinates
    )[1:2] <- c(
        "PCoA1",
        "PCoA2"
    )


    coordinates$SampleID <- (
        rownames(
            coordinates
        )
    )


    coordinates <- cbind(

        coordinates,

        metadata[
            match(
                coordinates$SampleID,
                metadata$SampleID
            ),
            setdiff(
                names(metadata),
                "SampleID"
            ),
            drop = FALSE
        ]
    )


    relative_eig <- (
        pcoa_result
        $values
        $Relative_eig
    )


    variance1 <- (

        if (
            length(relative_eig) >= 1
        )

            100 * relative_eig[1]

        else

            0
    )


    variance2 <- (

        if (
            length(relative_eig) >= 2
        )

            100 * relative_eig[2]

        else

            0
    )


    write.table(

        coordinates,

        file.path(
            output_dir,
            "pcoa",
            "pcoa_coordinates.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )


    write.table(

        data.frame(

            Axis =
                c(
                    "PCoA1",
                    "PCoA2"
                ),

            Variance =
                c(
                    variance1,
                    variance2
                )
        ),

        file.path(
            output_dir,
            "pcoa",
            "pcoa_variance.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )


    p <- ggplot(

        coordinates,

        aes(

            x = PCoA1,

            y = PCoA2,

            color = .data[[batch_variable]],

            shape = .data[[group_variable]]
        )

    ) +

        geom_point(
            size = 3,
            alpha = 0.85
        ) +

        theme_classic(
            base_size = 14
        ) +

        labs(

            title =
                paste(
                    "PCoA",
                    stage
                ),

            color =
                batch_variable,

            shape =
                group_variable,

            x =
                sprintf(
                    "PCoA1 (%.2f%%)",
                    variance1
                ),

            y =
                sprintf(
                    "PCoA2 (%.2f%%)",
                    variance2
                )
        )


    ggsave(

        file.path(
            output_dir,
            "pcoa",
            "pcoa.pdf"
        ),

        p,

        width = 7,

        height = 6
    )


    ggsave(

        file.path(
            output_dir,
            "pcoa",
            "pcoa.png"
        ),

        p,

        width = 7,

        height = 6,

        dpi = 300
    )
}


############################################################
# PERMANOVA
############################################################

run_permanova <- function(
    distance,
    metadata,
    output_dir
) {

    dir.create(

        file.path(
            output_dir,
            "permanova"
        ),

        recursive = TRUE,

        showWarnings = FALSE
    )


    formula <- as.formula(

        paste(

            "distance ~",

            batch_variable,

            "+",

            group_variable
        )
    )


    model <- vegan::adonis2(

        formula,

        data = metadata,

        permutations =
            permutations,

        by = "margin"
    )


    result <- data.frame(

        Variable =
            rownames(
                model
            ),

        R2 =
            model$R2,

        F =
            model$F,

        Pvalue =
            model$`Pr(>F)`,

        stringsAsFactors = FALSE
    )


    result <- result[
        result$Variable %in%
            c(
                batch_variable,
                group_variable
            ),
        ,
        drop = FALSE
    ]


    write.table(

        result,

        file.path(
            output_dir,
            "permanova",
            "permanova.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )


    result
}


############################################################
# Variance partitioning
############################################################

run_variance_partition <- function(
    X,
    metadata,
    output_dir
) {

    dir.create(

        file.path(
            output_dir,
            "variance_partition"
        ),

        recursive = TRUE,

        showWarnings = FALSE
    )


    results <- list()


    for (
        variable
        in variance_variables
    ) {

        if (
            !variable %in%
            names(metadata)
        ) {

            warning(
                paste(
                    "Variance variable not found:",
                    variable
                )
            )

            next
        }


        keep <- complete.cases(
            metadata[
                ,
                variable,
                drop = FALSE
            ]
        )


        if (
            sum(keep) < 3
        ) {

            next
        }


        X_sub <- X[
            keep,
            ,
            drop = FALSE
        ]


        metadata_sub <- metadata[
            keep,
            ,
            drop = FALSE
        ]


        predictor <- metadata_sub[[variable]]


        if (
            is.character(
                predictor
            )
        ) {

            predictor <- factor(
                predictor
            )
        }


        if (
            length(
                unique(
                    predictor
                )
            ) < 2
        ) {

            next
        }


        X_sub <- remove_zero_variance(
            X_sub
        )


        X_sub <- scale(
            X_sub
        )


        fit <- tryCatch(

            vegan::rda(

                X_sub
                ~
                predictor
            ),

            error =
                function(e)
                    NULL
        )


        if (
            is.null(fit)
        ) {

            next
        }


        r2 <- vegan::RsquareAdj(
            fit
        )


        pvalue <- tryCatch(

            vegan::anova.cca(

                fit,

                permutations =
                    permutations

            )$`Pr(>F)`[1],

            error =
                function(e)
                    NA_real_
        )


        results[[length(results) + 1]] <- data.frame(

            Variable =
                variable,

            R2 =
                r2$r.squared,

            Adjusted_R2 =
                r2$adj.r.squared,

            Pvalue =
                pvalue,

            stringsAsFactors = FALSE
        )
    }


    if (
        length(results) == 0
    ) {

        stop(
            "No valid variables for variance partitioning."
        )
    }


    results <- do.call(
        rbind,
        results
    )


    write.table(

        results,

        file.path(
            output_dir,
            "variance_partition",
            "variance_partition.tsv"
        ),

        sep = "\t",

        quote = FALSE,

        row.names = FALSE
    )


    plot_data <- results


    p <- ggplot(

        plot_data,

        aes(

            x =
                reorder(
                    Variable,
                    Adjusted_R2
                ),

            y =
                Adjusted_R2

        )

    ) +

        geom_col() +

        coord_flip() +

        theme_classic(
            base_size = 14
        ) +

        labs(

            x = "",

            y =
                "Adjusted R²"
        )


    ggsave(

        file.path(
            output_dir,
            "variance_partition",
            "variance_partition.pdf"
        ),

        p,

        width = 8,

        height = 5
    )


    ggsave(

        file.path(
            output_dir,
            "variance_partition",
            "variance_partition.png"
        ),

        p,

        width = 8,

        height = 5,

        dpi = 300
    )


    results
}


############################################################
# Run BEFORE
############################################################

run_pca(

    before,

    metadata,

    before_dir,

    "before batch correction"
)


before_distance <- calculate_distance(

    before,

    before_dir
)


run_pcoa(

    before_distance,

    metadata,

    before_dir,

    "before batch correction"
)


before_permanova <- run_permanova(

    before_distance,

    metadata,

    before_dir
)


before_variance <- run_variance_partition(

    before,

    metadata,

    before_dir
)


############################################################
# Run AFTER
############################################################

run_pca(

    after,

    metadata,

    after_dir,

    "after batch correction"
)


after_distance <- calculate_distance(

    after,

    after_dir
)


run_pcoa(

    after_distance,

    metadata,

    after_dir,

    "after batch correction"
)


after_permanova <- run_permanova(

    after_distance,

    metadata,

    after_dir
)


after_variance <- run_variance_partition(

    after,

    metadata,

    after_dir
)


############################################################
# Helper to safely extract one result
############################################################

extract_value <- function(
    table,
    variable,
    column
) {

    value <- table[
        table$Variable == variable,
        column
    ]


    if (
        length(value) == 0
    ) {

        return(
            NA_real_
        )
    }


    as.numeric(
        value[1]
    )
}


############################################################
# Summary
############################################################

summary <- data.frame(

    Metric = c(

        "Batch_PERMANOVA_R2",

        "Batch_PERMANOVA_P",

        "Group_PERMANOVA_R2",

        "Group_PERMANOVA_P",

        "Batch_Variance_Adjusted_R2",

        "Group_Variance_Adjusted_R2"
    ),


    Before = c(

        extract_value(
            before_permanova,
            batch_variable,
            "R2"
        ),

        extract_value(
            before_permanova,
            batch_variable,
            "Pvalue"
        ),

        extract_value(
            before_permanova,
            group_variable,
            "R2"
        ),

        extract_value(
            before_permanova,
            group_variable,
            "Pvalue"
        ),

        extract_value(
            before_variance,
            batch_variable,
            "Adjusted_R2"
        ),

        extract_value(
            before_variance,
            group_variable,
            "Adjusted_R2"
        )
    ),


    After = c(

        extract_value(
            after_permanova,
            batch_variable,
            "R2"
        ),

        extract_value(
            after_permanova,
            batch_variable,
            "Pvalue"
        ),

        extract_value(
            after_permanova,
            group_variable,
            "R2"
        ),

        extract_value(
            after_permanova,
            group_variable,
            "Pvalue"
        ),

        extract_value(
            after_variance,
            batch_variable,
            "Adjusted_R2"
        ),

        extract_value(
            after_variance,
            group_variable,
            "Adjusted_R2"
        )
    ),

    stringsAsFactors = FALSE
)


summary$Difference <- (

    summary$After
    -
    summary$Before
)


write.table(

    summary,

    file.path(
        summary_dir,
        "batch_diagnostics_summary.tsv"
    ),

    sep = "\t",

    quote = FALSE,

    row.names = FALSE
)


############################################################
# Comparison plot
############################################################

effect_metrics <- summary[
    summary$Metric %in%
        c(
            "Batch_PERMANOVA_R2",
            "Group_PERMANOVA_R2",
            "Batch_Variance_Adjusted_R2",
            "Group_Variance_Adjusted_R2"
        ),
    ,
    drop = FALSE
]


plot_data <- rbind(

    data.frame(

        Metric =
            effect_metrics$Metric,

        Stage =
            "Before",

        Value =
            effect_metrics$Before
    ),

    data.frame(

        Metric =
            effect_metrics$Metric,

        Stage =
            "After",

        Value =
            effect_metrics$After
    )
)


comparison_plot <- ggplot(

    plot_data,

    aes(

        x = Metric,

        y = Value,

        fill = Stage

    )

) +

    geom_col(

        position =
            position_dodge(
                width = 0.8
            ),

        width = 0.7
    ) +

    coord_flip() +

    theme_classic(
        base_size = 13
    ) +

    labs(

        x = "",

        y = "Effect size",

        title =
            "Batch diagnostics before and after correction"
    )


ggsave(

    file.path(
        summary_dir,
        "batch_diagnostics_comparison.pdf"
    ),

    comparison_plot,

    width = 9,

    height = 6
)


ggsave(

    file.path(
        summary_dir,
        "batch_diagnostics_comparison.png"
    ),

    comparison_plot,

    width = 9,

    height = 6,

    dpi = 300
)


############################################################
# Human-readable report
############################################################

sink(

    file.path(
        summary_dir,
        "batch_diagnostics_report.txt"
    )
)


cat(
    "Batch correction diagnostics\n"
)

cat(
    "============================\n\n"
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
    "PERMANOVA permutations:",
    permutations,
    "\n\n"
)


print(
    summary
)


cat(
    "\nInterpretation:\n"
)

cat(
    "- Batch PERMANOVA R2 should generally decrease after correction.\n"
)

cat(
    "- Batch variance contribution should generally decrease.\n"
)

cat(
    "- Biological Group signal should ideally be preserved.\n"
)

cat(
    "- Metadata confounding is a study-design property and is not expected to change after correction.\n"
)


sink()


cat(
    "Batch before/after diagnostics completed successfully.\n"
)