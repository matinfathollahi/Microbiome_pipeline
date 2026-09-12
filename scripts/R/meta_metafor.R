library(metafor)
library(dplyr)

###########################################################
# Read command-line arguments
###########################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {

    stop(
        paste(
            "Usage:",
            "meta_metafor.R",
            "input.tsv output.tsv min_studies"
        )
    )
}

input_file <- args[1]
output_file <- args[2]

min_studies <- as.integer(
    args[3]
)

if (
    is.na(min_studies)
    || min_studies < 2
) {

    stop(
        "min_studies must be >= 2."
    )
}

###########################################################
# Read input data
###########################################################

meta <- read.delim(
    input_file,
    check.names = FALSE,
    stringsAsFactors = FALSE
)

###########################################################
# Check required columns
###########################################################

required_columns <- c(
    "FeatureID",
    "EffectSize",
    "Variance"
)

missing_columns <- setdiff(required_columns, names(meta))

if (length(missing_columns) > 0) {
    stop(
        paste(
            "Missing required columns:",
            paste(missing_columns, collapse = ", ")
        )
    )
}

###########################################################
# Get taxa
###########################################################

features <- unique(
    na.omit(
        meta$FeatureID
    )
)

###########################################################
# Store results
###########################################################

result_list <- list()

###########################################################
# Meta-analysis for each taxon
###########################################################

for (feature_id in features) {

    x <- meta %>%
        filter(
            FeatureID == feature_id,
            is.finite(EffectSize),
            is.finite(Variance),
            Variance >= 1e-8
        )


    if (nrow(x) < min_studies)
        next

    fit <- tryCatch(
        suppressWarnings(
            rma(
                yi = EffectSize,
                vi = Variance,
                data = x,
                method = "REML"
            )
        ),
        error = function(e) NULL
    )

    if (is.null(fit))
        next

    result_list[[length(result_list) + 1]] <- data.frame(

        FeatureID = feature_id,
        Studies = fit$k,

        EffectSize = as.numeric(fit$b),
        SE = fit$se,
        Z = fit$zval,
        Pvalue = fit$pval,

        Lower95 = fit$ci.lb,
        Upper95 = fit$ci.ub,

        Tau2 = fit$tau2,
        I2 = fit$I2,
        H2 = fit$H2,

        QE = fit$QE,
        QEp = fit$QEp,

        stringsAsFactors = FALSE
    )
}

###########################################################
# Combine results
###########################################################

if (length(result_list) == 0) {

    stop(
        paste(
            "No feature had at least",
            min_studies,
            "valid study-specific effect estimates."
        )
    )

} else {

    results <- bind_rows(result_list)

    results$FDR <- p.adjust(
        results$Pvalue,
        method = "BH"
    )

    results <- results %>%
        arrange(FDR)

}

###########################################################
# Write output
###########################################################

write.table(

    results,

    file = output_file,

    sep = "\t",

    quote = FALSE,

    row.names = FALSE

)