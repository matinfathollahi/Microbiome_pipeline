#!/usr/bin/env Rscript

library(vegan)
library(readr)

############################################################
## Arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if(length(args) != 4){
    stop("Usage: permanova.R <distance.tsv> <method> <metadata.tsv> <output_dir>")
}

distance_file <- args[1]
method <- args[2]
metadata_file <- args[3]
output_dir <- args[4]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

############################################################
## Read distance matrix
############################################################

distance <- read.delim(
    distance_file,
    row.names = 1,
    check.names = FALSE
)

distance <- as.matrix(distance)

if(nrow(distance) != ncol(distance)){
    stop("Distance matrix must be square.")
}

if(!identical(rownames(distance), colnames(distance))){
    stop("Row names and column names of distance matrix do not match.")
}

distance <- as.dist(distance)

############################################################
## Read metadata
############################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE
)

required <- c("SampleID", "Group", "Batch")

missing <- setdiff(required, colnames(metadata))

if(length(missing) > 0){
    stop(
        "Missing metadata columns: ",
        paste(missing, collapse = ", ")
    )
}

idx <- match(labels(distance), metadata$SampleID)

if(any(is.na(idx))){
    stop("Some samples are missing from metadata.")
}

metadata <- metadata[idx, ]
metadata$Group <- as.factor(metadata$Group)
metadata$Batch <- as.factor(metadata$Batch)

if(nlevels(metadata$Group) < 2){
    stop("Group must contain at least two levels.")
}

if(nlevels(metadata$Batch) < 2){
    stop("Batch must contain at least two levels.")
}


############################################################
## PERMANOVA
############################################################

set.seed(123)

result <- adonis2(
    distance ~ Batch + Group,
    data = metadata,
    permutations = 999,
    by = "margin"
)
############################################################
## Save results
############################################################

write.table(
    as.data.frame(result),
    file.path(
        output_dir,
        paste0(method, "_PERMANOVA.tsv")
    ),
    sep = "\t",
    quote = FALSE,
    row.names = TRUE,
    col.names = NA
)