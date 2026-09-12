#!/usr/bin/env Rscript

library(zCompositions)


########################################################
## Arguments
########################################################

args <- commandArgs(trailingOnly = TRUE)

if(length(args) != 2){
    stop(
        "Usage: zero_replacement.R <input.tsv> <output.tsv>"
    )
}

input_file  <- args[1]
output_file <- args[2]

########################################################
## Check input
########################################################

if(!file.exists(input_file)){
    stop("Input file not found.")
}

dir.create(
    dirname(output_file),
    recursive = TRUE,
    showWarnings = FALSE
)

########################################################
## Read feature table
########################################################

counts <- read.delim(
    input_file,
    row.names = 1,
    check.names = FALSE
)



########################################################
## Check empty table
########################################################

if (nrow(counts) == 0 || ncol(counts) == 0) {
    stop("Input feature table is empty.")
}


########################################################
## Convert to numeric matrix
########################################################

counts <- as.matrix(counts)

storage.mode(counts) <- "numeric"

if(any(!is.finite(counts))){
    stop("Feature table contains Inf or NaN values.")
}

if(any(is.na(counts))){
    stop("Feature table contains NA values.")
}

if(any(counts < 0)){
    stop("Negative values detected.")
}

########################################################
## Features × Samples
## -> Samples × Features
########################################################

counts <- t(counts)



########################################################
## Remove features with all zeros
########################################################

zero_features <- colSums(counts) == 0

if (any(zero_features)) {

    cat(
        "Removing",
        sum(zero_features),
        "features containing only zeros.\n"
    )

    counts <- counts[, !zero_features, drop = FALSE]

}



########################################################
## Count zeros
########################################################

n_zero_before <- sum(counts == 0)




########################################################
## Check samples with all zeros
########################################################

if (any(rowSums(counts) == 0)) {

    zero_samples <- rownames(counts)[rowSums(counts) == 0]

    stop(
        paste(
            "The following samples contain only zeros:",
            paste(zero_samples, collapse = ", ")
        )
    )

}


########################################################
## Zero replacement
########################################################

counts_zero <- tryCatch(

    cmultRepl(
        counts,
        label = 0,
        method = "CZM"
    ),

    error = function(e){

        stop(
            paste(
                "Zero replacement failed:",
                e$message
            )
        )

    }

)



########################################################
## Samples × Features
## -> Features × Samples
########################################################

counts_zero <- t(as.matrix(counts_zero))

########################################################
## Save result
########################################################

write.table(

    counts_zero,

    output_file,

    sep = "\t",

    quote = FALSE,

    col.names = NA

)

########################################################
## Summary
########################################################

cat("\n")
cat("=====================================\n")
cat("Zero Replacement Summary\n")
cat("=====================================\n")
cat("Features :", nrow(counts_zero), "\n")
cat("Samples  :", ncol(counts_zero), "\n")
cat("Zeros replaced :", n_zero_before, "\n")
cat("Method : CZM\n")
cat("Completed successfully.\n")