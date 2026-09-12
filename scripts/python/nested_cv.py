#!/usr/bin/env python3

import argparse

from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from boruta import BorutaPy

from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import (
    StratifiedKFold,
    StratifiedGroupKFold,
    LeaveOneGroupOut,
    GridSearchCV
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import joblib

from microbiome_preprocessing import (
    MicrobiomeCLRPreprocessor
)

############################################################
# Helpers
############################################################

def metadata_columns(
    text,
    label,
    group=None
):

    cols = [
        x.strip()
        for x in text.split(",")
        if x.strip()
    ]

    if label not in cols:
        cols.append(label)

    if (
        group is not None
        and group not in cols
    ):
        cols.append(group)

    if "OriginalIndex" not in cols:
        cols.append("OriginalIndex")

    return cols


############################################################

def numeric_features(data, meta_cols):

    meta_set = set(meta_cols)

    feature_cols = [
        c
        for c in data.columns
        if c not in meta_set
    ]

    if not feature_cols:
        raise ValueError(
            "No feature columns found."
        )

    non_numeric = (
        data[feature_cols]
        .select_dtypes(exclude="number")
        .columns
        .tolist()
    )

    if non_numeric:

        raise ValueError(
            "Non-numeric feature columns found: "
            f"{non_numeric[:10]}"
        )

    if data[feature_cols].isna().any().any():

        raise ValueError(
            "Feature matrix contains missing values."
        )

    return feature_cols


############################################################
# Feature selection
############################################################

def select_features(data, args):

    meta_cols = metadata_columns(
        args.metadata,
        args.label,
        args.group
    )

    feature_cols = numeric_features(
        data,
        meta_cols
    )

    y = data[
        args.label
    ].astype(str)


    groups = data[
        args.group
    ].astype(str)


    n_groups = (
        groups
        .nunique()
    )


    print(
        f"Detected groups/studies: "
        f"{n_groups}"
    )


    if y.nunique() < 2:

        raise ValueError(
            "At least two classes are required."
        )

    ########################################################
    # 1. Variance filtering
    # FIT ONLY ON TRAINING FOLD
    ########################################################

    variance_selector = VarianceThreshold(
        threshold=args.variance_threshold
    )

    variance_selector.fit(
        data[feature_cols]
    )

    variance_features = [

        feature

        for feature, keep
        in zip(
            feature_cols,
            variance_selector.get_support()
        )

        if keep
    ]

    if not variance_features:

        raise ValueError(
            "Variance filtering removed all features."
        )

    ########################################################
    # 2. Boruta
    # FIT ONLY ON TRAINING FOLD
    ########################################################

    boruta_rf = RandomForestClassifier(

        n_estimators=args.boruta_trees,

        class_weight="balanced",

        random_state=args.boruta_seed,

        n_jobs=-1
    )

    boruta = BorutaPy(

        boruta_rf,

        n_estimators=args.boruta_trees,

        max_iter=args.boruta_max_iter,

        random_state=args.boruta_seed,

        verbose=0
    )

    boruta.fit(

        data[
            variance_features
        ].to_numpy(),

        y.to_numpy()
    )

    boruta_features = [

        feature

        for feature, keep
        in zip(
            variance_features,
            boruta.support_
        )

        if keep
    ]

    if not boruta_features:

        print(
            "WARNING: Boruta selected "
            "no features in this fold."
        )






    ########################################################
    # ElasticNet internal CV
    # Study-aware whenever possible
    ########################################################




    if n_groups >= 2:

        ####################################################
        # Multiple studies
        ####################################################

        effective_elastic_cv = min(
            args.elastic_cv,
            n_groups
        )

        if effective_elastic_cv < 2:

            raise ValueError(
                "Not enough studies for "
                "ElasticNet group-aware CV."
            )


        elastic_splitter = StratifiedGroupKFold(

            n_splits=effective_elastic_cv,

            shuffle=True,

            random_state=args.elastic_seed
        )


        elastic_cv = list(

            elastic_splitter.split(

                data[
                    variance_features
                ],

                y,

                groups=groups
            )
        )


        elastic_strategy = (
            "StratifiedGroupKFold"
        )


    else:

        ####################################################
        # Only one study
        ####################################################

        minimum_class_size = int(
            y.value_counts().min()
        )


        effective_elastic_cv = min(
            args.elastic_cv,
            minimum_class_size
        )


        if effective_elastic_cv < 2:

            raise ValueError(
                "Not enough samples per class "
                "for ElasticNet CV."
            )


        elastic_splitter = StratifiedKFold(

            n_splits=effective_elastic_cv,

            shuffle=True,

            random_state=args.elastic_seed
        )


        elastic_cv = list(

            elastic_splitter.split(

                data[
                    variance_features
                ],

                y
            )
        )


        elastic_strategy = (
            "StratifiedKFold fallback"
        )







    ########################################################
    # Validate ElasticNet folds
    ########################################################

    all_classes = set(
        y.unique()
    )

    elastic_validation_has_all_classes = True


    for (
        elastic_fold,
        (
            elastic_train_idx,
            elastic_valid_idx
        )
    ) in enumerate(
        elastic_cv,
        start=1
    ):

        train_classes = set(
            y.iloc[
                elastic_train_idx
            ].unique()
        )

        valid_classes = set(
            y.iloc[
                elastic_valid_idx
            ].unique()
        )


        ####################################################
        # Training fold MUST contain all classes
        ####################################################

        if train_classes != all_classes:

            raise ValueError(
                f"ElasticNet fold "
                f"{elastic_fold}: "
                "training split does not "
                "contain all classes."
            )


        ####################################################
        # Validation fold may contain only one class
        ####################################################

        if valid_classes != all_classes:

            elastic_validation_has_all_classes = False

            print(
                f"WARNING: ElasticNet fold "
                f"{elastic_fold} validation "
                "split does not contain "
                "all classes."
            )


    ########################################################
    # Choose scoring dynamically
    ########################################################

    if elastic_validation_has_all_classes:

        scoring = (
            "roc_auc"
            if y.nunique() == 2
            else "roc_auc_ovr_weighted"
        )

    else:

        scoring = "balanced_accuracy"

        print(
            "WARNING: Some group-aware "
            "ElasticNet validation folds "
            "do not contain all classes. "
            "Using balanced_accuracy "
            "instead of ROC-AUC."
        )



    print(
        "ElasticNet scoring:",
        scoring
    )








    print(
        "ElasticNet CV strategy:",
        elastic_strategy
    )







    ########################################################
    # Leakage-safe ElasticNet tuning
    ########################################################

    elastic_pipeline = Pipeline(

        [

            (
                "scaler",
                StandardScaler()
            ),

            (
                "model",

                LogisticRegression(

                    penalty="elasticnet",

                    solver="saga",

                    l1_ratio=
                        args.elastic_l1,

                    random_state=
                        args.elastic_seed,

                    class_weight="balanced",

                    max_iter=10000
                )
            )
        ]
    )


    elastic_param_grid = {

        "model__C":
            np.logspace(
                -4,
                4,
                10
            )
    }


    elastic = GridSearchCV(

        estimator=
            elastic_pipeline,

        param_grid=
            elastic_param_grid,

        scoring=
            scoring,

        cv=
            elastic_cv,

        n_jobs=-1,

        refit=True,

        error_score="raise"
    )


    elastic.fit(

        data[
            variance_features
        ],

        y
    )


    print(
        "ElasticNet best C:",
        elastic.best_params_[
            "model__C"
        ]
    )






    coefficients = np.asarray(

        elastic
        .best_estimator_
        .named_steps[
            "model"
        ]
        .coef_
    )

    coefficient_strength = np.max(

        np.abs(
            coefficients
        ),

        axis=0
    )




    elastic_features = [

        feature

        for feature, coefficient
        in zip(
            variance_features,
            coefficient_strength
        )

        if coefficient > 0
    ]





    if not elastic_features:

        print(
            "WARNING: ElasticNet selected "
            "no features in this fold."
        )

    ########################################################
    # 4. Random Forest selection
    # FIT ONLY ON TRAINING FOLD
    ########################################################

    rf = RandomForestClassifier(

        n_estimators=args.rf_trees,

        random_state=args.rf_seed,

        class_weight="balanced",

        n_jobs=-1
    )

    rf.fit(

        data[
            variance_features
        ],

        y
    )

    importance = pd.Series(

        rf.feature_importances_,

        index=variance_features
    )

    rf_top = min(

        args.rf_top,

        len(
            variance_features
        )
    )

    rf_features = (

        importance

        .sort_values(
            ascending=False
        )

        .head(
            rf_top
        )

        .index

        .tolist()
    )

    if not rf_features:

        print(
            "WARNING: Random Forest selected "
            "no features in this fold."
        )

    ########################################################
    # 5. Consensus
    ########################################################

    counts = Counter()

    for features in (

        boruta_features,

        elastic_features,

        rf_features

    ):

        for feature in set(features):

            counts[feature] += 1

    selected = [

        feature

        for feature in variance_features

        if counts[feature]
        >= args.consensus_min
    ]

    if not selected:

        raise ValueError(
            "No consensus features found "
            "in this fold."
        )

    feature_table = pd.DataFrame(

        {

            "Feature":
                selected,

            "Methods":
                [
                    counts[f]
                    for f in selected
                ]
        }
    )

    return (
        selected,
        feature_table
    )


############################################################

def apply_features(
    data,
    selected,
    args
):

    wanted = (

        metadata_columns(
            args.metadata,
            args.label,
            args.group
        )

        + selected
    )

    keep = []

    for column in wanted:

        if (
            column in data.columns
            and column not in keep
        ):

            keep.append(
                column
            )

    return data[
        keep
    ].copy()


############################################################
# Main
############################################################

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True
    )

    parser.add_argument(
        "--group",
        required=True
    )

    parser.add_argument(
        "--label",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--fallback_folds",
        type=int,
        default=5
    )
    parser.add_argument(
        "--inner",
        type=int,
        default=5
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=2026
    )

    parser.add_argument(
        "--variance_threshold",
        type=float,
        required=True
    )

    parser.add_argument(
        "--boruta_trees",
        type=int,
        required=True
    )

    parser.add_argument(
        "--boruta_max_iter",
        type=int,
        required=True
    )

    parser.add_argument(
        "--boruta_seed",
        type=int,
        required=True
    )

    parser.add_argument(
        "--elastic_cv",
        type=int,
        required=True
    )

    parser.add_argument(
        "--elastic_l1",
        type=float,
        required=True
    )

    parser.add_argument(
        "--elastic_seed",
        type=int,
        required=True
    )

    parser.add_argument(
        "--rf_trees",
        type=int,
        required=True
    )

    parser.add_argument(
        "--rf_top",
        type=int,
        required=True
    )

    parser.add_argument(
        "--rf_seed",
        type=int,
        required=True
    )

    parser.add_argument(
        "--consensus_min",
        type=int,
        required=True
    )


    parser.add_argument(
        "--min_count",
        type=float,
        required=True
    )

    parser.add_argument(
        "--prevalence",
        type=float,
        required=True
    )

    parser.add_argument(
        "--zero_fraction",
        type=float,
        default=0.5
    )


    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    ########################################################


    if args.inner < 2:

        raise ValueError(
            "inner must be at least 2"
        )

    if not (
        1 <= args.consensus_min <= 3
    ):

        raise ValueError(
            "consensus_min must be "
            "between 1 and 3"
        )

    ########################################################








    ########################################################
    # Read data
    ########################################################

    data = pd.read_csv(
        args.input,
        sep="\t"
    )


    ########################################################
    # Validate label
    ########################################################

    if args.label not in data.columns:

        raise ValueError(
            f"Label column "
            f"'{args.label}' not found."
        )


    if data[
        args.label
    ].isna().any():

        raise ValueError(
            "Label column contains "
            "missing values."
        )


    if data[
        args.label
    ].nunique() < 2:

        raise ValueError(
            "At least two classes "
            "are required."
        )


    ########################################################
    # Validate study/group column
    ########################################################

    if args.group not in data.columns:

        raise ValueError(
            f"Group column "
            f"'{args.group}' not found."
        )


    if data[
        args.group
    ].isna().any():

        raise ValueError(
            f"Group column "
            f"'{args.group}' contains "
            "missing values."
        )


    ########################################################
    # Add original index
    ########################################################

    data = data.copy()

    data[
        "OriginalIndex"
    ] = np.arange(
        len(data)
    )


    ########################################################
    # Labels and study groups
    ########################################################

    y = data[
        args.label
    ].astype(str)


    groups = data[
        args.group
    ].astype(str)


    n_groups = (
        groups
        .nunique()
    )


    print()

    print(
        f"Detected groups/studies: "
        f"{n_groups}"
    )


    ########################################################
    # Output directory
    ########################################################

    outdir = Path(
        args.output
    )

    outdir.mkdir(
        parents=True,
        exist_ok=True
    )









    ########################################################




    ########################################################
    # OUTER CV
    ########################################################

    if n_groups >= 2:

        ####################################################
        # Multiple studies:
        # Leave one entire study out
        ####################################################

        outer_strategy = (
            "LeaveOneGroupOut"
        )

        outer_cv = LeaveOneGroupOut()

        outer_splits = list(
            outer_cv.split(
                data,
                y,
                groups=groups
            )
        )

    else:

        ####################################################
        # Only one study:
        # Study-aware CV is impossible
        ####################################################

        outer_strategy = (
            "StratifiedKFold fallback"
        )






        minimum_class_size = int(
            y.value_counts().min()
        )

        effective_outer_folds = min(
            args.fallback_folds,
            minimum_class_size
        )

        if effective_outer_folds < 2:

            raise ValueError(
                "Not enough samples per class "
                "for outer cross-validation."
            )


        outer_cv = StratifiedKFold(

            n_splits=
                effective_outer_folds,

            shuffle=True,

            random_state=
                args.seed
        )


        outer_splits = list(
            outer_cv.split(
                data,
                y
            )
        )


    outer_fold_count = len(
        outer_splits
    )


    print(
        "Outer CV strategy:",
        outer_strategy
    )

    print(
        "Outer folds:",
        outer_fold_count
    )


    outer_summary = []





    ########################################################

    for (
        outer_fold,
        (
            train_idx,
            valid_idx
        )
    ) in enumerate(

        outer_splits,

        start=1
    ):

        outer_dir = (

            outdir
            / f"outer_fold_{outer_fold}"

        )

        outer_dir.mkdir(

            parents=True,

            exist_ok=True
        )




        ####################################################
        # RAW OUTER SPLIT
        ####################################################

        outer_train_raw = (

            data
            .iloc[
                train_idx
            ]
            .reset_index(
                drop=True
            )
        )

        outer_valid_raw = (

            data
            .iloc[
                valid_idx
            ]
            .reset_index(
                drop=True
            )
        )


        ####################################################
        # Check class availability in outer fold
        ####################################################

        all_classes = set(
            y.unique()
        )


        outer_train_classes = set(

            outer_train_raw[
                args.label
            ]
            .astype(str)
            .unique()
        )


        outer_valid_classes = set(

            outer_valid_raw[
                args.label
            ]
            .astype(str)
            .unique()
        )


        if (
            outer_train_classes
            != all_classes
        ):

            raise ValueError(
                f"Outer fold {outer_fold}: "
                "training data does not "
                "contain all classes."
            )


        if (
            outer_valid_classes
            != all_classes
        ):

            print(
                f"WARNING: Outer fold "
                f"{outer_fold} validation "
                "study does not contain "
                "all classes. "
                "ROC-AUC may not be "
                "computable for this fold."
            )


####################################################
# Check study leakage in outer split
####################################################

        outer_train_groups = set(

            outer_train_raw[
                args.group
            ]
            .astype(str)
            .unique()
        )


        outer_valid_groups = set(

            outer_valid_raw[
                args.group
            ]
            .astype(str)
            .unique()
        )


        if n_groups >= 2:

            overlap = (
                outer_train_groups
                &
                outer_valid_groups
            )

            if overlap:

                raise RuntimeError(
                    "Study leakage detected "
                    "between outer train and "
                    f"validation: {sorted(overlap)}"
                )


        print()

        print(
            f"Outer fold {outer_fold}"
        )

        print(
            "Train studies:",
            sorted(
                outer_train_groups
            )
        )

        print(
            "Validation studies:",
            sorted(
                outer_valid_groups
            )
        )









####################################################
# Leakage-safe microbiome preprocessing
# FIT ONLY on outer training fold
####################################################

        (
            outer_train_processed,
            outer_valid_processed,
            outer_preprocessor
        ) = preprocess_fold(

            outer_train_raw,

            outer_valid_raw,

            args
        )


####################################################
# Save outer-fold preprocessing object
####################################################

        joblib.dump(

            outer_preprocessor,

            outer_dir
            / "microbiome_preprocessor.joblib"
        )


####################################################
# Feature selection ONLY on processed outer train
####################################################

        (
            outer_features,
            outer_feature_table
        ) = select_features(

            outer_train_processed,

            args
        )


####################################################
# Apply selected features
####################################################

        outer_train = apply_features(

            outer_train_processed,

            outer_features,

            args
        )

        outer_valid = apply_features(

            outer_valid_processed,

            outer_features,

            args
        )

        outer_train.to_csv(

            outer_dir
            / "outer_train.tsv",

            sep="\t",

            index=False
        )

        outer_valid.to_csv(

            outer_dir
            / "outer_valid.tsv",

            sep="\t",

            index=False
        )

        outer_feature_table.to_csv(

            outer_dir
            / "outer_selected_features.tsv",

            sep="\t",

            index=False
        )









        ####################################################
        # INNER CV
        ####################################################

####################################################
# INNER CV
####################################################

        inner_y = outer_train_raw[
            args.label
        ].astype(str)


        inner_groups = outer_train_raw[
            args.group
        ].astype(str)


        n_inner_groups = (
            inner_groups
            .nunique()
        )


####################################################
# If at least two studies remain:
# group-aware inner CV
####################################################

        if n_inner_groups >= 2:

            effective_inner_folds = min(
                args.inner,
                n_inner_groups
            )

            if effective_inner_folds < 2:

                raise ValueError(
                    f"Outer fold {outer_fold}: "
                    "not enough studies for "
                    "inner group-aware CV."
                )

            inner_strategy = (
                "StratifiedGroupKFold"
            )

            inner_cv = StratifiedGroupKFold(

                n_splits=
                    effective_inner_folds,

                shuffle=True,

                random_state=(
                    args.seed
                    + outer_fold
                )
            )

            inner_splits = list(

                inner_cv.split(

                    outer_train_raw,

                    inner_y,

                    groups=inner_groups
                )
            )


####################################################
# If only one study remains:
# group-aware splitting is impossible
####################################################

        else:

            inner_strategy = (
                "StratifiedKFold fallback"
            )

            minimum_class_size = int(
                inner_y
                .value_counts()
                .min()
            )

            effective_inner_folds = min(
                args.inner,
                minimum_class_size
            )

            if effective_inner_folds < 2:

                raise ValueError(
                    f"Outer fold {outer_fold}: "
                    "not enough samples per class "
                    "for inner CV."
                )

            inner_cv = StratifiedKFold(

                n_splits=
                    effective_inner_folds,

                shuffle=True,

                random_state=(
                    args.seed
                    + outer_fold
                )
            )

            inner_splits = list(

                inner_cv.split(

                    outer_train_raw,

                    inner_y
                )
            )


        print(
            "Inner CV strategy:",
            inner_strategy
        )

        print(
            "Inner folds:",
            len(inner_splits)
        )


        inner_summary = []











        ####################################################

        for (
            inner_fold,
            (
                inner_train_idx,
                inner_valid_idx
            )
        ) in enumerate(

            inner_splits,

            start=1
        ):





            inner_train_raw = (

                outer_train_raw

                .iloc[
                    inner_train_idx
                ]

                .reset_index(
                    drop=True
                )
            )

            inner_valid_raw = (

                outer_train_raw

                .iloc[
                    inner_valid_idx
                ]

                .reset_index(
                    drop=True
                )
            )




################################################
# Check study leakage in inner split
################################################

            inner_train_groups_set = set(

                inner_train_raw[
                    args.group
                ]
                .astype(str)
                .unique()
            )


            inner_valid_groups_set = set(

                inner_valid_raw[
                    args.group
                ]
                .astype(str)
                .unique()
            )


            if n_inner_groups >= 2:

                overlap = (
                    inner_train_groups_set
                    &
                    inner_valid_groups_set
                )

                if overlap:

                    raise RuntimeError(
                        "Study leakage detected "
                        f"in outer fold {outer_fold}, "
                        f"inner fold {inner_fold}: "
                        f"{sorted(overlap)}"
                    )







################################################
# Leakage-safe microbiome preprocessing
# FIT ONLY on inner training fold
################################################

            (
                inner_train_processed,
                inner_valid_processed,
                inner_preprocessor
            ) = preprocess_fold(

                inner_train_raw,

                inner_valid_raw,

                args
            )


################################################
# Feature selection ONLY on inner training fold
################################################

            (
                inner_features,
                inner_feature_table
            ) = select_features(

                inner_train_processed,

                args
            )


################################################
# Apply selected features to
# inner train and inner validation
################################################

            inner_train = apply_features(

                inner_train_processed,

                inner_features,

                args
            )

            inner_valid = apply_features(

                inner_valid_processed,

                inner_features,

                args
            )









            ################################################

            inner_train.to_csv(

                outer_dir
                / (
                    f"inner_train_"
                    f"{inner_fold}.tsv"
                ),

                sep="\t",

                index=False
            )

            inner_valid.to_csv(

                outer_dir
                / (
                    f"inner_valid_"
                    f"{inner_fold}.tsv"
                ),

                sep="\t",

                index=False
            )

            inner_feature_table.to_csv(

                outer_dir
                / (
                    f"inner_selected_features_"
                    f"{inner_fold}.tsv"
                ),

                sep="\t",

                index=False
            )

            ################################################

            inner_summary.append(

                {
                    "InnerFold":
                        inner_fold,

                    "Strategy":
                        inner_strategy,

                    "TrainSamples":
                        len(inner_train),

                    "ValidationSamples":
                        len(inner_valid),

                    "TrainStudies":
                        ",".join(
                            sorted(
                                inner_train_groups_set
                            )
                        ),

                    "ValidationStudies":
                        ",".join(
                            sorted(
                                inner_valid_groups_set
                            )
                        ),

                    "SelectedFeatures":
                        len(inner_features)
                }
            )

        ####################################################

        pd.DataFrame(
            inner_summary
        ).to_csv(

            outer_dir
            / "inner_summary.tsv",

            sep="\t",

            index=False
        )

        ####################################################

        outer_summary.append(

            {
                "OuterFold":
                    outer_fold,

                "Strategy":
                    outer_strategy,

                "TrainSamples":
                    len(outer_train),

                "ValidationSamples":
                    len(outer_valid),

                "TrainStudies":
                    ",".join(
                        sorted(
                            outer_train_groups
                        )
                    ),

                "ValidationStudies":
                    ",".join(
                        sorted(
                            outer_valid_groups
                        )
                    ),

                "SelectedFeatures":
                    len(outer_features)
            }
        )

    ########################################################

    pd.DataFrame(
        outer_summary
    ).to_csv(

        outdir
        / "fold_summary.tsv",

        sep="\t",

        index=False
    )

    ########################################################

    print()

    print(
        f"Samples     : {len(data)}"
    )

    print(
        f"Groups/studies : {n_groups}"
    )

    print(
        f"Outer strategy : {outer_strategy}"
    )

    print(
        f"Outer folds    : {outer_fold_count}"
    )

    print(
        f"Max inner folds: {args.inner}"
    )

    print(
        f"Output      : {outdir}"
    )

    print()


############################################################
def preprocess_fold(
    train_raw,
    valid_raw,
    args
):

    meta_cols = metadata_columns(
        args.metadata,
        args.label,
        args.group
    )

    feature_cols = numeric_features(
        train_raw,
        meta_cols
    )

    preprocessor = MicrobiomeCLRPreprocessor(

        min_count=
            args.min_count,

        prevalence=
            args.prevalence,

        zero_fraction=
            args.zero_fraction
    )

    X_train = (
        preprocessor
        .fit_transform(
            train_raw[
                feature_cols
            ]
        )
    )

    X_valid = (
        preprocessor
        .transform(
            valid_raw[
                feature_cols
            ]
        )
    )

    metadata_train = train_raw[
        [
            column
            for column
            in train_raw.columns

            if column
            not in feature_cols
        ]
    ].reset_index(
        drop=True
    )

    metadata_valid = valid_raw[
        [
            column
            for column
            in valid_raw.columns

            if column
            not in feature_cols
        ]
    ].reset_index(
        drop=True
    )

    train_processed = pd.concat(

        [
            metadata_train,

            X_train.reset_index(
                drop=True
            )
        ],

        axis=1
    )

    valid_processed = pd.concat(

        [
            metadata_valid,

            X_valid.reset_index(
                drop=True
            )
        ],

        axis=1
    )

    return (
        train_processed,
        valid_processed,
        preprocessor
    )


if __name__ == "__main__":

    main()