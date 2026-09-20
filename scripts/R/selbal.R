#!/usr/bin/env Rscript

library(selbal)
library(pROC)


############################################################
# Arguments
############################################################

args <- commandArgs(
    trailingOnly = TRUE
)

if (length(args) != 17) {

    stop(
        paste(
            "Usage: Rscript selbal.R",
            "<feature_table.tsv>",
            "<metadata.tsv>",
            "<output_dir>",
            "<study_column>",
            "<group_column>",
            "<reference_group>",
            "<case_group>",
            "<min_samples_per_group>",
            "<min_studies>",
            "<min_count>",
            "<prevalence>",
            "<inner_folds>",
            "<inner_iterations>",
            "<max_features>",
            "<seed>",
            "<zero_replacement>",
            "<opt_criterion>"
        )
    )
}


table_file <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

study_column <- args[4]
group_column <- args[5]

reference_group <- args[6]
case_group <- args[7]

min_samples_per_group <- as.integer(
    args[8]
)

min_studies <- as.integer(
    args[9]
)

min_count <- as.numeric(
    args[10]
)

prevalence <- as.numeric(
    args[11]
)

inner_folds <- as.integer(
    args[12]
)

inner_iterations <- as.integer(
    args[13]
)

max_features <- as.integer(
    args[14]
)

seed <- as.integer(
    args[15]
)

zero_replacement <- args[16]

opt_criterion <- args[17]


############################################################
# Validate arguments
############################################################

if (!file.exists(table_file)) {
    stop(
        "Feature table not found: ",
        table_file
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
    is.na(prevalence) ||
    prevalence < 0 ||
    prevalence > 1
) {
    stop(
        "prevalence must be between 0 and 1."
    )
}


if (
    is.na(inner_folds) ||
    inner_folds < 2
) {
    stop(
        "inner_folds must be >= 2."
    )
}


if (
    is.na(inner_iterations) ||
    inner_iterations < 1
) {
    stop(
        "inner_iterations must be >= 1."
    )
}


if (
    is.na(max_features) ||
    max_features < 2
) {
    stop(
        "max_features must be >= 2."
    )
}


if (is.na(seed)) {
    stop(
        "Invalid seed."
    )
}


if (
    !zero_replacement %in%
    c("bayes", "one")
) {
    stop(
        "zero_replacement must be bayes or one."
    )
}


if (
    !opt_criterion %in%
    c("1se", "max")
) {
    stop(
        "opt_criterion must be 1se or max."
    )
}


############################################################
# Output directory
############################################################

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)


############################################################
# Read feature table
#
# Input:
# Features × Samples
############################################################

counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


counts <- as.matrix(
    counts
)


storage.mode(
    counts
) <- "numeric"


if (
    nrow(counts) == 0 ||
    ncol(counts) == 0
) {
    stop(
        "Feature table is empty."
    )
}


if (
    any(
        !is.finite(counts)
    )
) {
    stop(
        "Feature table contains non-finite values."
    )
}


if (
    any(
        counts < 0
    )
) {
    stop(
        "Feature table contains negative values."
    )
}


############################################################
# Duplicate feature check
############################################################

if (
    any(
        duplicated(
            rownames(counts)
        )
    )
) {
    stop(
        "Duplicate feature IDs detected."
    )
}


############################################################
# Duplicate sample check
############################################################

if (
    any(
        duplicated(
            colnames(counts)
        )
    )
) {
    stop(
        "Duplicate sample IDs detected in feature table."
    )
}


############################################################
# Samples × Features
############################################################

counts <- t(
    counts
)


############################################################
# Read metadata
############################################################

metadata <- read.delim(
    metadata_file,
    row.names = 1,
    check.names = FALSE,
    stringsAsFactors = FALSE
)


metadata$SampleID <- rownames(
    metadata
)


required_columns <- c(
    study_column,
    group_column
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
        "Missing metadata columns: ",
        paste(
            missing_columns,
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


metadata$Study <- trimws(
    as.character(
        metadata[[study_column]]
    )
)


metadata$Group <- trimws(
    as.character(
        metadata[[group_column]]
    )
)


############################################################
# Duplicate metadata IDs
############################################################

if (
    any(
        duplicated(
            metadata$SampleID
        )
    )
) {
    stop(
        "Duplicate SampleID values detected in metadata."
    )
}


############################################################
# Metadata samples must exist in feature table
############################################################

missing_samples <- setdiff(
    metadata$SampleID,
    rownames(counts)
)


if (
    length(
        missing_samples
    ) > 0
) {
    stop(
        length(
            missing_samples
        ),
        " metadata samples are missing from the feature table."
    )
}


############################################################
# Keep relevant samples
############################################################

metadata <- metadata[
    metadata$Study != "" &
    metadata$Group != "" &
    metadata$Group %in%
        c(
            reference_group,
            case_group
        ),
    ,
    drop = FALSE
]


############################################################
# Study eligibility
############################################################

study_names <- sort(
    unique(
        metadata$Study
    )
)


eligibility_list <- lapply(
    study_names,
    function(study_name) {

        study_data <- metadata[
            metadata$Study ==
                study_name,
            ,
            drop = FALSE
        ]

        n_reference <- sum(
            study_data$Group ==
                reference_group
        )

        n_case <- sum(
            study_data$Group ==
                case_group
        )

        eligible <-
            n_reference >=
                min_samples_per_group &&
            n_case >=
                min_samples_per_group


        if (eligible) {

            reason <- "Eligible"

        } else if (
            n_reference <
                min_samples_per_group &&
            n_case <
                min_samples_per_group
        ) {

            reason <-
                "Insufficient samples in both groups"

        } else if (
            n_reference <
                min_samples_per_group
        ) {

            reason <- paste0(
                "Insufficient ",
                reference_group,
                " samples"
            )

        } else {

            reason <- paste0(
                "Insufficient ",
                case_group,
                " samples"
            )
        }


        data.frame(

            Study =
                study_name,

            N_Reference =
                n_reference,

            N_Case =
                n_case,

            Eligible =
                eligible,

            Reason =
                reason,

            stringsAsFactors = FALSE
        )
    }
)


study_eligibility <- do.call(
    rbind,
    eligibility_list
)


write.table(

    study_eligibility,

    file.path(
        output_dir,
        "study_eligibility.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


eligible_studies <-
    study_eligibility$Study[
        study_eligibility$Eligible
    ]


if (
    length(
        eligible_studies
    ) < min_studies
) {

    stop(
        "Only ",
        length(eligible_studies),
        " eligible studies; ",
        min_studies,
        " required."
    )
}


############################################################
# Restrict to eligible studies
############################################################

metadata <- metadata[
    metadata$Study %in%
        eligible_studies,
    ,
    drop = FALSE
]


counts <- counts[
    metadata$SampleID,
    ,
    drop = FALSE
]


if (
    !identical(
        rownames(counts),
        metadata$SampleID
    )
) {
    stop(
        "Feature table and metadata order mismatch."
    )
}


############################################################
# Helper: training-only feature filtering
############################################################

filter_features <- function(
    x_train,
    min_count,
    prevalence
) {

    abundance_ok <-
        colSums(
            x_train
        ) >= min_count


    prevalence_ok <-
        colMeans(
            x_train > 0
        ) >= prevalence


    nonzero_ok <-
        colSums(
            x_train
        ) > 0


    keep <-
        abundance_ok &
        prevalence_ok &
        nonzero_ok


    colnames(
        x_train
    )[keep]
}


############################################################
# Selbal zero replacement function
############################################################

cmultRepl2_fun <- get(
    "cmultRepl2",
    envir =
        asNamespace(
            "selbal"
        )
)


############################################################
# LOSO storage
############################################################

all_predictions <- data.frame()

fold_metrics <- data.frame()

fold_balances <- data.frame()


############################################################
# Leave-One-Study-Out
############################################################

for (
    i in seq_along(
        eligible_studies
    )
) {

    held_out_study <-
        eligible_studies[i]


    message(
        "LOSO fold ",
        i,
        "/",
        length(eligible_studies),
        " | held out: ",
        held_out_study
    )


    ########################################################
    # Outer split
    ########################################################

    train_idx <-
        metadata$Study !=
        held_out_study


    test_idx <-
        metadata$Study ==
        held_out_study


    x_train_raw <- counts[
        train_idx,
        ,
        drop = FALSE
    ]


    x_test_raw <- counts[
        test_idx,
        ,
        drop = FALSE
    ]


    y_train <- factor(
        metadata$Group[
            train_idx
        ],
        levels = c(
            reference_group,
            case_group
        )
    )


    y_test <- factor(
        metadata$Group[
            test_idx
        ],
        levels = c(
            reference_group,
            case_group
        )
    )


    ########################################################
    # Both groups must exist
    ########################################################

    if (
        any(
            table(y_train) == 0
        )
    ) {
        stop(
            "Training data missing a group in fold: ",
            held_out_study
        )
    }


    if (
        any(
            table(y_test) == 0
        )
    ) {
        stop(
            "Held-out study missing a group: ",
            held_out_study
        )
    }


    ########################################################
    # TRAIN-ONLY feature filtering
    ########################################################

    selected_features <-
        filter_features(
            x_train =
                x_train_raw,

            min_count =
                min_count,

            prevalence =
                prevalence
        )


    if (
        length(
            selected_features
        ) < 2
    ) {

        stop(
            "Fewer than two features remain in fold: ",
            held_out_study
        )
    }


    x_train <- x_train_raw[
        ,
        selected_features,
        drop = FALSE
    ]


    x_test <- x_test_raw[
        ,
        selected_features,
        drop = FALSE
    ]


    ########################################################
    # Dynamic inner folds
    ########################################################

    minimum_class_size <- min(
        table(
            y_train
        )
    )


    fold_inner_folds <- min(
        inner_folds,
        minimum_class_size
    )


    if (
        fold_inner_folds < 2
    ) {

        stop(
            "Not enough training samples for inner CV in fold: ",
            held_out_study
        )
    }


    ########################################################
    # Maximum balance size
    ########################################################

    fold_max_features <- min(
        max_features,
        ncol(
            x_train
        )
    )


    if (
        fold_max_features < 2
    ) {

        stop(
            "Not enough features for Selbal in fold: ",
            held_out_study
        )
    }


    ########################################################
    # Fit Selbal ONLY on training Studies
    ########################################################

    fold_seed <- seed + i - 1


    set.seed(
        fold_seed
    )


    fit <- selbal::selbal.cv(

        x =
            x_train,

        y =
            y_train,

        n.fold =
            fold_inner_folds,

        n.iter =
            inner_iterations,

        seed =
            fold_seed,

        logit.acc =
            "AUC",

        maxV =
            fold_max_features,

        zero.rep =
            zero_replacement,

        opt.cri =
            opt_criterion
    )


    ########################################################
    # Validate selected balance
    ########################################################

    balance_table <-
        fit$global.balance


    if (
        is.null(
            balance_table
        ) ||
        nrow(
            balance_table
        ) < 2
    ) {

        stop(
            "Invalid Selbal balance for fold: ",
            held_out_study
        )
    }


    if (
        !all(
            c(
                "Taxa",
                "Group"
            ) %in%
            colnames(
                balance_table
            )
        )
    ) {

        stop(
            "Unexpected global.balance structure."
        )
    }


    ########################################################
    # Ensure selected taxa exist in held-out data
    ########################################################

    selected_balance_taxa <-
        as.character(
            balance_table$Taxa
        )


    missing_test_taxa <- setdiff(
        selected_balance_taxa,
        colnames(
            x_test
        )
    )


    if (
        length(
            missing_test_taxa
        ) > 0
    ) {

        stop(
            "Selected balance taxa missing from held-out study: ",
            paste(
                missing_test_taxa,
                collapse = ", "
            )
        )
    }


    ########################################################
    # Apply SAME zero-replacement method to held-out Study
    ########################################################

    x_test_balance <- x_test[
        ,
        selected_balance_taxa,
        drop = FALSE
    ]

    x_test_log <- log(
        cmultRepl2_fun(
            x_test_balance,
            zero.rep =
                zero_replacement
        )
    )


    if (
        any(
            !is.finite(
                x_test_log
            )
        )
    ) {

        stop(
            "Non-finite transformed values in held-out study: ",
            held_out_study
        )
    }


    ########################################################
    # Compute held-out balance
    ########################################################

    test_balance <-
        selbal::bal.value(

            balance_table,

            x_test_log
        )


    ########################################################
    # Prediction using TRAINED Selbal GLM
    ########################################################

    test_probability <- as.numeric(

        predict(

            fit$fit,

            newdata =
                data.frame(
                    V1 =
                        test_balance
                ),

            type =
                "response"
        )
    )


    test_probability <- pmin(
        pmax(
            test_probability,
            0
        ),
        1
    )


    ########################################################
    # Held-out ROC
    ########################################################

    roc_object <- pROC::roc(

        response =
            y_test,

        predictor =
            test_probability,

        levels =
            c(
                reference_group,
                case_group
            ),

        direction =
            "<",

        quiet =
            TRUE
    )


    fold_auc <- as.numeric(
        pROC::auc(
            roc_object
        )
    )


    ########################################################
    # Classification metrics
    ########################################################

    predicted_case <-
        test_probability >=
        0.5


    true_case <-
        y_test ==
        case_group


    TP <- sum(
        predicted_case &
        true_case
    )


    TN <- sum(
        !predicted_case &
        !true_case
    )


    FP <- sum(
        predicted_case &
        !true_case
    )


    FN <- sum(
        !predicted_case &
        true_case
    )


    sensitivity <- if (
        TP + FN > 0
    ) {

        TP / (
            TP + FN
        )

    } else {

        NA_real_
    }


    specificity <- if (
        TN + FP > 0
    ) {

        TN / (
            TN + FP
        )

    } else {

        NA_real_
    }


    accuracy <-
        (
            TP + TN
        ) /
        length(
            y_test
        )


    balanced_accuracy <- mean(
        c(
            sensitivity,
            specificity
        ),
        na.rm = TRUE
    )


    predicted_group <- ifelse(

        predicted_case,

        case_group,

        reference_group
    )


    ########################################################
    # Save sample-level predictions
    ########################################################

    fold_predictions <- data.frame(

        SampleID =
            rownames(
                x_test
            ),

        Study =
            held_out_study,

        Truth =
            as.character(
                y_test
            ),

        Balance =
            as.numeric(
                test_balance
            ),

        Probability_Case =
            test_probability,

        Predicted_Group =
            predicted_group,

        Fold =
            i,

        stringsAsFactors = FALSE
    )


    all_predictions <- rbind(
        all_predictions,
        fold_predictions
    )


    ########################################################
    # Fold metrics
    ########################################################

    fold_metric <- data.frame(

        Fold =
            i,

        HeldOutStudy =
            held_out_study,

        N_Train =
            nrow(
                x_train
            ),

        N_Test =
            nrow(
                x_test
            ),

        N_Test_Reference =
            sum(
                y_test ==
                reference_group
            ),

        N_Test_Case =
            sum(
                y_test ==
                case_group
            ),

        N_Prefilter_Features =
            length(
                selected_features
            ),

        Optimal_Balance_Size =
            fit$opt.nvar,

        Inner_Folds =
            fold_inner_folds,

        Inner_Iterations =
            inner_iterations,

        AUC =
            fold_auc,

        Accuracy =
            accuracy,

        Balanced_Accuracy =
            balanced_accuracy,

        Sensitivity =
            sensitivity,

        Specificity =
            specificity,

        Seed =
            fold_seed,

        stringsAsFactors = FALSE
    )


    fold_metrics <- rbind(
        fold_metrics,
        fold_metric
    )


    ########################################################
    # Selected balance taxa for stability analysis
    ########################################################

    fold_balance <- data.frame(

        Fold =
            i,

        HeldOutStudy =
            held_out_study,

        Taxon =
            as.character(
                balance_table$Taxa
            ),

        Side =
            as.character(
                balance_table$Group
            ),

        stringsAsFactors = FALSE
    )


    fold_balances <- rbind(
        fold_balances,
        fold_balance
    )
}


############################################################
# Save LOSO predictions
############################################################

write.table(

    all_predictions,

    file.path(
        output_dir,
        "loso_predictions.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


############################################################
# Save fold metrics
############################################################

write.table(

    fold_metrics,

    file.path(
        output_dir,
        "loso_fold_metrics.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


############################################################
# Save fold balances
############################################################

write.table(

    fold_balances,

    file.path(
        output_dir,
        "loso_fold_balances.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


############################################################
# Taxon stability across Studies
############################################################

all_taxa <- sort(
    unique(
        fold_balances$Taxon
    )
)


stability_list <- lapply(

    all_taxa,

    function(taxon) {

        taxon_data <-
            fold_balances[
                fold_balances$Taxon ==
                    taxon,
                ,
                drop = FALSE
            ]


        selected_folds <- length(
            unique(
                taxon_data$Fold
            )
        )


        numerator_folds <- length(
            unique(
                taxon_data$Fold[
                    taxon_data$Side ==
                        "NUM"
                ]
            )
        )


        denominator_folds <- length(
            unique(
                taxon_data$Fold[
                    taxon_data$Side ==
                        "DEN"
                ]
            )
        )


        consistency <- if (
            selected_folds > 0
        ) {

            max(
                numerator_folds,
                denominator_folds
            ) /
            selected_folds

        } else {

            NA_real_
        }


        consensus_side <- if (
            numerator_folds >
            denominator_folds
        ) {

            "NUM"

        } else if (
            denominator_folds >
            numerator_folds
        ) {

            "DEN"

        } else {

            "TIE"
        }


        data.frame(

            Taxon =
                taxon,

            Selected_Folds =
                selected_folds,

            Total_Folds =
                length(
                    eligible_studies
                ),

            Selection_Frequency =
                selected_folds /
                length(
                    eligible_studies
                ),

            Numerator_Folds =
                numerator_folds,

            Denominator_Folds =
                denominator_folds,

            Side_Consistency =
                consistency,

            Consensus_Side =
                consensus_side,

            stringsAsFactors = FALSE
        )
    }
)


taxon_stability <- do.call(
    rbind,
    stability_list
)


taxon_stability <- taxon_stability[
    order(
        -taxon_stability$Selection_Frequency,
        -taxon_stability$Side_Consistency
    ),
]


write.table(

    taxon_stability,

    file.path(
        output_dir,
        "taxon_stability.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


############################################################
# Pooled out-of-study ROC
############################################################

all_truth <- factor(

    all_predictions$Truth,

    levels = c(
        reference_group,
        case_group
    )
)


pooled_roc <- pROC::roc(

    response =
        all_truth,

    predictor =
        all_predictions$Probability_Case,

    levels =
        c(
            reference_group,
            case_group
        ),

    direction =
        "<",

    quiet =
        TRUE
)


pooled_auc <- as.numeric(
    pROC::auc(
        pooled_roc
    )
)


############################################################
# ROC plot
############################################################

pdf(

    file.path(
        output_dir,
        "LOSO_ROC.pdf"
    ),

    width = 7,

    height = 7
)


plot(

    pooled_roc,

    main =
        paste0(
            "Selbal Leave-One-Study-Out ROC\nAUC = ",
            round(
                pooled_auc,
                3
            )
        )
)


abline(
    a = 0,
    b = 1,
    lty = 2
)


dev.off()


############################################################
# LOSO summary
############################################################

weighted_auc <- weighted.mean(

    fold_metrics$AUC,

    w =
        fold_metrics$N_Test
)


summary_result <- data.frame(

    N_Studies =
        length(
            eligible_studies
        ),

    N_Samples =
        nrow(
            all_predictions
        ),

    Pooled_LOSO_AUC =
        pooled_auc,

    Mean_Study_AUC =
        mean(
            fold_metrics$AUC
        ),

    SD_Study_AUC =
        sd(
            fold_metrics$AUC
        ),

    Weighted_Mean_Study_AUC =
        weighted_auc,

    Mean_Balanced_Accuracy =
        mean(
            fold_metrics$
                Balanced_Accuracy
        ),

    Reference_Group =
        reference_group,

    Case_Group =
        case_group,

    Min_Count =
        min_count,

    Prevalence =
        prevalence,

    Seed =
        seed,

    stringsAsFactors = FALSE
)


write.table(

    summary_result,

    file.path(
        output_dir,
        "selbal_loso_summary.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


############################################################
# Final model
#
# IMPORTANT:
# Performance is NOT estimated from this model.
# Performance comes only from LOSO predictions above.
############################################################

final_features <- filter_features(

    x_train =
        counts,

    min_count =
        min_count,

    prevalence =
        prevalence
)


if (
    length(
        final_features
    ) < 2
) {

    stop(
        "Fewer than two features remain for final Selbal model."
    )
}


write.table(

    data.frame(
        Feature =
            final_features
    ),

    file.path(
        output_dir,
        "final_prefilter_features.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


x_final <- counts[
    ,
    final_features,
    drop = FALSE
]


y_final <- factor(

    metadata$Group,

    levels = c(
        reference_group,
        case_group
    )
)


final_inner_folds <- min(

    inner_folds,

    min(
        table(
            y_final
        )
    )
)


final_max_features <- min(

    max_features,

    ncol(
        x_final
    )
)


set.seed(
    seed + 10000
)


final_fit <- selbal::selbal.cv(

    x =
        x_final,

    y =
        y_final,

    n.fold =
        final_inner_folds,

    n.iter =
        inner_iterations,

    seed =
        seed + 10000,

    logit.acc =
        "AUC",

    maxV =
        final_max_features,

    zero.rep =
        zero_replacement,

    opt.cri =
        opt_criterion
)


saveRDS(

    final_fit,

    file.path(
        output_dir,
        "final_model.rds"
    )
)


write.table(

    final_fit$global.balance,

    file.path(
        output_dir,
        "final_balance.tsv"
    ),

    sep = "\t",

    row.names = FALSE,

    quote = FALSE
)


message(
    "Selbal Leave-One-Study-Out analysis completed successfully."
)