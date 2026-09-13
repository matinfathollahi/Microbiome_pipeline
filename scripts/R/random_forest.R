#!/usr/bin/env Rscript

library(randomForest)

library(dplyr)
library(caret)
library(pROC)
library(ggplot2)


############################################################
## Arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if(length(args) != 3){
    stop("Usage: random_forest.R table.tsv metadata.tsv output_dir")
}

table_file <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

############################################################
## Read data
############################################################

counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE
)

metadata <- read.delim(
    metadata_file,
    row.names = 1,
    check.names = FALSE
)

############################################################
## Samples × Features
############################################################

counts <- as.data.frame(t(counts))

# Convert all features to numeric
counts[] <- lapply(counts, function(x) suppressWarnings(as.numeric(x)))

# Check for missing or non-numeric values
if (any(is.na(counts))) {
    stop("Counts table contains missing or non-numeric values.")
}

############################################################
## Match metadata
############################################################

idx <- match(rownames(counts), rownames(metadata))

# Check for missing samples in metadata
if (any(is.na(idx))) {
    missing_samples <- rownames(counts)[is.na(idx)]
    stop(
        paste(
            "The following samples are missing in metadata:",
            paste(missing_samples, collapse = ", ")
        )
    )
}

metadata <- metadata[idx, ]

# Double-check that sample order matches
if (!identical(rownames(counts), rownames(metadata))) {
    stop("Sample order mismatch between counts and metadata.")
}

# Check Group column
if (any(is.na(metadata$Group))) {
    stop("Group column contains missing values.")
}

counts$Group <- factor(metadata$Group)

# Check number of classes
if (nlevels(counts$Group) < 2) {
    stop("At least two groups are required.")
}

############################################################
## Train/Test split
############################################################

set.seed(2026)

train_index <- createDataPartition(
    counts$Group,
    p = 0.8,
    list = FALSE
)

train <- counts[train_index, ]
test <- counts[-train_index, ]

# Check training/testing datasets
if (nrow(train) == 0 || nrow(test) == 0) {
    stop("Training or testing dataset is empty.")
}

if (length(unique(train$Group)) < 2) {
    stop("Training dataset must contain at least two classes.")
}
############################################################
## Random Forest
############################################################

rf <- randomForest(
    Group ~ .,
    data = train,
    importance = TRUE,
    ntree = 1000
)

saveRDS(
    rf,
    file.path(output_dir, "random_forest_model.rds")
)

############################################################
## Feature Importance
############################################################

importance_table <- as.data.frame(importance(rf))
importance_table$Feature <- rownames(importance_table)

write.table(
    importance_table,
    file.path(output_dir, "feature_importance.tsv"),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

############################################################
## Top 20
############################################################

if(!"MeanDecreaseGini" %in% colnames(importance_table)){
    stop("MeanDecreaseGini column not found.")
}

selected <- importance_table %>%
    arrange(desc(MeanDecreaseGini)) %>%
    slice_head(n = 20)

write.table(
    selected,
    file.path(output_dir, "selected_features.tsv"),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

############################################################
## Variable Importance Plot
############################################################

pdf(
    file.path(output_dir, "Feature_Importance.pdf"),
    width = 8,
    height = 8
)

varImpPlot(
    rf,
    n.var = 20,
    main = "Top 20 Important Features"
)

dev.off()

############################################################
## Prediction
############################################################

pred <- predict(
    rf,
    newdata = test
)

# Ensure prediction levels match the true labels
pred <- factor(
    pred,
    levels = levels(test$Group)
)

cm <- confusionMatrix(
    data = pred,
    reference = test$Group
)
write.table(
    as.data.frame(cm$table),
    file.path(output_dir, "confusion_matrix.tsv"),
    sep = "\t",
    quote = FALSE
)

############################################################
## OOB Error
############################################################

oob <- data.frame(
    Trees = seq_len(nrow(rf$err.rate)),
    OOB = rf$err.rate[, "OOB"]
)

write.table(
    oob,
    file.path(output_dir, "oob_error.tsv"),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

############################################################
## ROC (Binary only)
############################################################

if (length(unique(test$Group)) == 2) {

    prob <- predict(
        rf,
        newdata = test,
        type = "prob"
    )

    positive_class <- levels(test$Group)[2]

    roc_obj <- roc(
        response = test$Group,
        predictor = prob[, positive_class],
        levels = levels(test$Group)
    )

    pdf(
        file.path(output_dir, "ROC.pdf")
    )

    plot(roc_obj)

    dev.off()

    write.table(
        data.frame(AUC = as.numeric(auc(roc_obj))),
        file.path(output_dir, "AUC.tsv"),
        sep = "\t",
        quote = FALSE,
        row.names = FALSE
    )

}

############################################################
## MDS Plot
############################################################

pdf(
    file.path(output_dir, "MDS.pdf"),
    width = 7,
    height = 7
)

MDSplot(
    rf,
    train$Group
)

dev.off()

############################################################
## Top20 Plot
############################################################

p <- ggplot(
    selected,
    aes(
        reorder(Feature, MeanDecreaseGini),
        MeanDecreaseGini
    )
) +
    geom_col() +
    coord_flip() +
    theme_classic()

ggsave(
    file.path(output_dir, "Top20_Features.pdf"),
    p,
    width = 8,
    height = 6
)

############################################################
## Importance Histogram
############################################################

p_hist <- ggplot(
    importance_table,
    aes(MeanDecreaseGini)
) +
    geom_histogram(bins = 30) +
    theme_classic()

ggsave(
    file.path(output_dir, "Importance_Distribution.pdf"),
    p_hist,
    width = 7,
    height = 5
)

############################################################

cat("Training samples :", nrow(train), "\n")
cat("Testing samples  :", nrow(test), "\n")
cat("Features         :", ncol(train) - 1, "\n")