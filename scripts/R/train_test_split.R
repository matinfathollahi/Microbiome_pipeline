#!/usr/bin/env Rscript

library(caret)

########################################################

args <- commandArgs(trailingOnly = TRUE)

if(length(args) != 6){
    stop(
        paste(
            "Usage:",
            "Rscript train_test_split.R",
            "<dataset.tsv>",
            "<label_column>",
            "<train_fraction>",
            "<seed>",
            "<train.tsv>",
            "<test.tsv>"
        )
    )
}

dataset_file <- args[1]
label        <- args[2]
train_frac   <- as.numeric(args[3])
seed         <- as.integer(args[4])
train_file   <- args[5]
test_file    <- args[6]

########################################################
## Check input
########################################################

if(!file.exists(dataset_file)){
    stop("Input dataset file does not exist.")
}

if(is.na(train_frac) || train_frac <= 0 || train_frac >= 1){
    stop("train_fraction must be between 0 and 1.")
}

########################################################

if(is.na(seed)){
    stop("Seed must be an integer.")
}

set.seed(seed)

########################################################
## Read dataset
########################################################

data <- read.delim(
    dataset_file,
    check.names = FALSE
)


########################################################
## Check dataset structure
########################################################

if (ncol(data) == 0) {
    stop("Dataset contains no columns.")
}

########################################################
## Check label column
########################################################

if(!(label %in% colnames(data))){
    stop(paste("Label column not found:", label))
}

########################################################
## Remove missing labels
########################################################

data <- data[
    !is.na(data[[label]]),
    ,
    drop = FALSE
]


########################################################
## Check if dataset is empty
########################################################

if (nrow(data) == 0) {
    stop("No samples remain after removing missing labels.")
}

########################################################
## Convert label to factor
########################################################

data[[label]] <- factor(data[[label]])

########################################################
## Check classes
########################################################

if(nlevels(data[[label]]) < 2){
    stop("At least two classes are required.")
}

class_counts <- table(data[[label]])

if(any(class_counts < 2)){
    stop("Each class must contain at least two samples.")
}

########################################################
## Stratified Train/Test split
########################################################

index <- createDataPartition(
    y = data[[label]],
    p = train_frac,
    list = FALSE
)

train <- data[
    index,
    ,
    drop = FALSE
]

test <- data[
    -index,
    ,
    drop = FALSE
]


########################################################
## Check class distribution after split
########################################################

if (nlevels(droplevels(train[[label]])) < 2) {
    stop("Training set contains fewer than two classes.")
}

if (nlevels(droplevels(test[[label]])) < 2) {
    stop("Testing set contains fewer than two classes.")
}

########################################################
## Create output directories
########################################################

dir.create(
    dirname(train_file),
    recursive = TRUE,
    showWarnings = FALSE
)

dir.create(
    dirname(test_file),
    recursive = TRUE,
    showWarnings = FALSE
)

########################################################
## Save results
########################################################

write.table(
    train,
    train_file,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

write.table(
    test,
    test_file,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

########################################################
## Summary
########################################################

cat("\n")
cat("=====================================\n")
cat("Train/Test Split Summary\n")
cat("=====================================\n")
cat("Total samples :", nrow(data), "\n")
cat("Train samples :", nrow(train), "\n")
cat("Test samples  :", nrow(test), "\n")
cat("Train fraction:", train_frac, "\n")

cat("\nTraining class distribution:\n")
print(table(train[[label]]))

cat("\nTesting class distribution:\n")
print(table(test[[label]]))

cat("\nTrain/Test split completed successfully.\n")