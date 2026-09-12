#!/usr/bin/env python3

import argparse

import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import GroupShuffleSplit


############################################################
# Arguments
############################################################

parser = argparse.ArgumentParser()

parser.add_argument(
    "--input",
    required=True
)

parser.add_argument(
    "--label",
    required=True
)

parser.add_argument(
    "--group",
    required=True,
    help="Study/cohort column used for leakage-free splitting"
)

parser.add_argument(
    "--train_fraction",
    type=float,
    default=0.8
)

parser.add_argument(
    "--seed",
    type=int,
    default=2026
)

parser.add_argument(
    "--no_stratify",
    action="store_true",
    help=(
        "Do not require all classes to be present "
        "in both train and test"
    )
)

parser.add_argument(
    "--train-samples",
    required=True
)

parser.add_argument(
    "--test-samples",
    required=True
)

parser.add_argument(
    "--search_splits",
    type=int,
    default=2000,
    help=(
        "Number of group-disjoint candidate splits "
        "to evaluate"
    )
)

parser.add_argument(
    "--train_output",
    required=True
)

parser.add_argument(
    "--test_output",
    required=True
)

args = parser.parse_args()


############################################################
# Validate arguments
############################################################

if not 0 < args.train_fraction < 1:

    raise ValueError(
        "--train_fraction must be between 0 and 1"
    )


if args.search_splits < 1:

    raise ValueError(
        "--search_splits must be >= 1"
    )


############################################################
# Read data
############################################################

data = pd.read_csv(
    args.input,
    sep="\t",
    encoding="utf-8"
)


############################################################
# Required columns
############################################################

for column in (
    "SampleID",
    args.label,
    args.group
):

    if column not in data.columns:

        raise ValueError(
            f"Required column '{column}' "
            "not found in input file"
        )



############################################################
# Validate SampleID
############################################################

data["SampleID"] = (
    data["SampleID"]
    .fillna("")
    .astype(str)
    .str.strip()
)


if (
    data["SampleID"]
    == ""
).any():

    raise ValueError(
        "SampleID contains missing/blank values."
    )


if (
    data["SampleID"]
    .duplicated()
    .any()
):

    duplicated_ids = (
        data.loc[
            data["SampleID"].duplicated(
                keep=False
            ),
            "SampleID"
        ]
        .unique()
        .tolist()
    )

    raise ValueError(
        "Duplicate SampleID values detected: "
        + ", ".join(
            duplicated_ids[:20]
        )
    )


############################################################
# Validate labels / groups
############################################################

if data[args.label].isna().any():

    raise ValueError(
        f"Label column '{args.label}' "
        "contains missing values"
    )


if data[args.group].isna().any():

    raise ValueError(
        f"Group column '{args.group}' "
        "contains missing values"
    )


data[args.group] = (
    data[args.group]
    .astype(str)
    .str.strip()
)


if (
    data[args.group]
    == ""
).any():

    raise ValueError(
        f"Group column '{args.group}' "
        "contains empty values"
    )


############################################################
# Number of studies
############################################################

n_groups = (
    data[args.group]
    .nunique()
)


if n_groups < 2:

    raise ValueError(
        "At least 2 distinct studies/groups "
        "are required for a study-level "
        "holdout split."
    )


############################################################
# Global class information
############################################################

labels_as_string = (
    data[args.label]
    .astype(str)
)

classes = set(
    labels_as_string.unique()
)


if len(classes) < 2:

    raise ValueError(
        "At least two classes are required."
    )


global_distribution = (
    labels_as_string
    .value_counts(
        normalize=True
    )
)


############################################################
# Group-aware split
#
# IMPORTANT:
# Entire Study values remain together.
############################################################

splitter = GroupShuffleSplit(
    n_splits=args.search_splits,
    train_size=args.train_fraction,
    random_state=args.seed
)


best_split = None
best_score = np.inf


for train_index, test_index in splitter.split(
    data,
    groups=data[args.group]
):

    train_candidate = (
        data.iloc[train_index]
        .copy()
    )

    test_candidate = (
        data.iloc[test_index]
        .copy()
    )


    ########################################################
    # Absolute leakage check
    ########################################################

    train_groups = set(
        train_candidate[
            args.group
        ].unique()
    )

    test_groups = set(
        test_candidate[
            args.group
        ].unique()
    )

    overlap = (
        train_groups
        &
        test_groups
    )


    if overlap:

        raise RuntimeError(
            "Internal error: Study overlap "
            f"detected: {sorted(overlap)}"
        )




    ########################################################
    # Require all classes in train AND test
    ########################################################

    if not args.no_stratify:

        train_classes = set(
            train_candidate[
                args.label
            ]
            .astype(str)
            .unique()
        )

        test_classes = set(
            test_candidate[
                args.label
            ]
            .astype(str)
            .unique()
        )


        if train_classes != classes:

            continue


        if test_classes != classes:

            continue


    ########################################################
    # Prefer split close to requested sample fraction
    ########################################################

    actual_train_fraction = (
        len(train_candidate)
        /
        len(data)
    )


    fraction_error = abs(
        actual_train_fraction
        -
        args.train_fraction
    )


    ########################################################
    # Prefer similar class distributions
    ########################################################

    train_distribution = (
        train_candidate[
            args.label
        ]
        .astype(str)
        .value_counts(
            normalize=True
        )
        .reindex(
            global_distribution.index,
            fill_value=0.0
        )
    )


    test_distribution = (
        test_candidate[
            args.label
        ]
        .astype(str)
        .value_counts(
            normalize=True
        )
        .reindex(
            global_distribution.index,
            fill_value=0.0
        )
    )


    class_balance_error = (

        (
            train_distribution
            -
            global_distribution
        )
        .abs()
        .mean()

        +

        (
            test_distribution
            -
            global_distribution
        )
        .abs()
        .mean()
    )


    ########################################################
    # Overall split quality
    ########################################################

    score = (
        fraction_error
        +
        class_balance_error
    )


    if score < best_score:

        best_score = score

        best_split = (
            train_candidate,
            test_candidate
        )


############################################################
# No valid grouped split
############################################################

if best_split is None:

    raise ValueError(
        "Could not find a study-disjoint "
        "train/test split containing all "
        "classes in both partitions. "
        "Possible reasons: too few studies, "
        "Study is strongly confounded with Group, "
        "or train_fraction is unsuitable."
    )


############################################################
# Final split
############################################################

train, test = best_split


train_groups = sorted(
    train[
        args.group
    ]
    .unique()
    .tolist()
)


test_groups = sorted(
    test[
        args.group
    ]
    .unique()
    .tolist()
)


############################################################
# FINAL leakage check
############################################################

overlap = sorted(
    set(train_groups)
    &
    set(test_groups)
)


if overlap:

    raise RuntimeError(
        "FATAL: Study leakage detected "
        f"after split: {overlap}"
    )

############################################################
# FINAL SampleID split validation
############################################################

train_sample_ids = set(
    train["SampleID"]
)

test_sample_ids = set(
    test["SampleID"]
)


sample_overlap = sorted(
    train_sample_ids
    &
    test_sample_ids
)


if sample_overlap:

    raise RuntimeError(
        "FATAL: SampleID overlap detected "
        "between train and test: "
        + ", ".join(
            sample_overlap[:20]
        )
    )


all_split_sample_ids = (
    train_sample_ids
    |
    test_sample_ids
)


all_input_sample_ids = set(
    data["SampleID"]
)


if (
    all_split_sample_ids
    !=
    all_input_sample_ids
):

    missing_samples = sorted(
        all_input_sample_ids
        -
        all_split_sample_ids
    )

    unexpected_samples = sorted(
        all_split_sample_ids
        -
        all_input_sample_ids
    )

    raise RuntimeError(
        "Train/test SampleIDs do not exactly "
        "cover the input dataset. "
        f"Missing={missing_samples[:20]}, "
        f"Unexpected={unexpected_samples[:20]}"
    )

############################################################
# Create output directories
############################################################

for output_path in (
    args.train_output,
    args.test_output,
    args.train_samples,
    args.test_samples
):

    Path(
        output_path
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

############################################################
# Write outputs
############################################################

train.to_csv(
    args.train_output,
    sep="\t",
    index=False
)


test.to_csv(
    args.test_output,
    sep="\t",
    index=False
)


############################################################
# Write reusable SampleID manifests
############################################################

train[
    ["SampleID"]
].to_csv(
    args.train_samples,
    sep="\t",
    index=False
)


test[
    ["SampleID"]
].to_csv(
    args.test_samples,
    sep="\t",
    index=False
)
############################################################
# Report
############################################################

print(
    f"Total samples : {len(data)}"
)

print(
    f"Total studies : {n_groups}"
)

print()

print(
    f"Train samples : {len(train)}"
)

print(
    f"Test samples  : {len(test)}"
)

print()

print(
    f"Train studies ({len(train_groups)}): "
    f"{train_groups}"
)

print(
    f"Test studies ({len(test_groups)}): "
    f"{test_groups}"
)

print()

print(
    f"Study overlap : {overlap}"
)

print(
    "Actual train fraction: "
    f"{len(train) / len(data):.4f}"
)

print()

print(
    "Train distribution"
)

print(
    train[
        args.label
    ]
    .value_counts()
)

print()

print(
    "Test distribution"
)

print(
    test[
        args.label
    ]
    .value_counts()
)