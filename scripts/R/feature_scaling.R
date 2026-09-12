library(caret)

########################################################
# Check arguments
########################################################

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 6) {
    stop(
        paste(
            "Usage:",
            "Rscript script.R",
            "train_file",
            "test_file",
            "method",
            "meta_cols",
            "train_out",
            "test_out"
        )
    )
}

train_file <- args[1]
test_file  <- args[2]

method <- trimws(
    strsplit(args[3], ",")[[1]]
)

meta_cols <- trimws(
    strsplit(args[4], ",")[[1]]
)

train_out <- args[5]
test_out  <- args[6]

########################################################
# Read data
########################################################

train <- read.delim(
    train_file,
    check.names = FALSE
)

test <- read.delim(
    test_file,
    check.names = FALSE
)

########################################################
# Save original column order
########################################################

train_order <- colnames(train)
test_order  <- colnames(test)

########################################################
# Check metadata columns
########################################################

missing_meta_train <- setdiff(meta_cols, colnames(train))

if (length(missing_meta_train) > 0) {
    stop(
        paste(
            "Missing metadata columns in train:",
            paste(missing_meta_train, collapse = ", ")
        )
    )
}

missing_meta_test <- setdiff(meta_cols, colnames(test))

if (length(missing_meta_test) > 0) {
    stop(
        paste(
            "Missing metadata columns in test:",
            paste(missing_meta_test, collapse = ", ")
        )
    )
}

########################################################
# Feature columns
########################################################

feature_cols <- setdiff(colnames(train), meta_cols)

if (length(feature_cols) == 0) {
    stop("No feature columns found.")
}

########################################################
# Check feature columns in test
########################################################

missing_features <- setdiff(feature_cols, colnames(test))

if (length(missing_features) > 0) {
    stop(
        paste(
            "Missing feature columns in test:",
            paste(missing_features, collapse = ", ")
        )
    )
}


########################################################
# Check extra feature columns in test
########################################################

extra_features <- setdiff(
    setdiff(colnames(test), meta_cols),
    feature_cols
)

if (length(extra_features) > 0) {
    stop(
        paste(
            "Extra feature columns in test:",
            paste(extra_features, collapse = ", ")
        )
    )
}

########################################################
# Check numeric features
########################################################

non_numeric <- feature_cols[
    !sapply(train[, feature_cols, drop = FALSE], is.numeric)
]

if (length(non_numeric) > 0) {
    stop(
        paste(
            "Non-numeric feature columns:",
            paste(non_numeric, collapse = ", ")
        )
    )
}



########################################################
# Check numeric features in test
########################################################

non_numeric_test <- feature_cols[
    !sapply(test[, feature_cols, drop = FALSE], is.numeric)
]

if (length(non_numeric_test) > 0) {
    stop(
        paste(
            "Non-numeric feature columns in test:",
            paste(non_numeric_test, collapse = ", ")
        )
    )
}

########################################################
# Warn about missing values
########################################################

if (anyNA(train[, feature_cols, drop = FALSE])) {
    warning("Training data contains missing values.")
}

if (anyNA(test[, feature_cols, drop = FALSE])) {
    warning("Test data contains missing values.")
}

########################################################
# Learn preprocessing from train
########################################################

pre <- preProcess(
    train[, feature_cols, drop = FALSE],
    method = method
)

########################################################
# Apply preprocessing
########################################################

train_scaled <- predict(
    pre,
    train[, feature_cols, drop = FALSE]
)

test_scaled <- predict(
    pre,
    test[, feature_cols, drop = FALSE]
)

########################################################
# Combine metadata and processed features
########################################################

train <- cbind(
    train[, meta_cols, drop = FALSE],
    train_scaled
)

test <- cbind(
    test[, meta_cols, drop = FALSE],
    test_scaled
)

########################################################
# Restore original column order
########################################################

train <- train[, train_order]

test <- test[, test_order]

########################################################
# Write output
########################################################

write.table(
    train,
    train_out,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

write.table(
    test,
    test_out,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)