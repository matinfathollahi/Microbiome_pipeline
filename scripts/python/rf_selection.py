#!/usr/bin/env python3

import argparse
import pandas as pd

from sklearn.ensemble import RandomForestClassifier


########################################################
# Arguments
########################################################

parser = argparse.ArgumentParser()

parser.add_argument(
    "--input",
    required=True
)

parser.add_argument(
    "--trees",
    type=int,
    default=1000
)

parser.add_argument(
    "--seed",
    type=int,
    default=2026
)

parser.add_argument(
    "--top",
    type=int,
    default=100
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
    "--train_output",
    required=True
)

parser.add_argument(
    "--feature_output",
    required=True
)

parser.add_argument(
    "--importance_output",
    required=True
)

args = parser.parse_args()


########################################################
# Read input data
########################################################

data = pd.read_csv(
    args.input,
    sep="\t"
)


########################################################
# Label
########################################################

target_col = args.label


if target_col not in data.columns:
    raise ValueError(
        f"Label column '{target_col}' "
        "not found in input file."
    )


########################################################
# Metadata columns
########################################################

meta_cols = [

    x.strip()

    for x in args.metadata.split(",")

    if x.strip()
]


# Make absolutely sure label is NOT treated as a feature
if target_col not in meta_cols:
    meta_cols.append(
        target_col
    )


# Keep metadata columns that actually exist
meta_cols = [

    col

    for col in meta_cols

    if col in data.columns
]


########################################################
# Feature columns
########################################################

feature_cols = [

    col

    for col in data.columns

    if col not in meta_cols
]


if len(feature_cols) == 0:
    raise ValueError(
        "No feature columns found after "
        "removing metadata and label."
    )


########################################################
# X and y
########################################################

X = data[
    feature_cols
]

y = data[
    target_col
]


########################################################
# Check missing values
########################################################

if y.isnull().any():
    raise ValueError(
        f"Label column '{target_col}' "
        "contains missing values."
    )


if X.isnull().values.any():
    raise ValueError(
        "Input feature data contains missing values."
    )


########################################################
# Check numeric features
########################################################

non_numeric = (
    X.select_dtypes(
        exclude="number"
    )
    .columns
    .tolist()
)


if non_numeric:
    raise ValueError(
        "Non-numeric feature columns found: "
        + ", ".join(non_numeric)
    )


########################################################
# Random Forest
########################################################

rf = RandomForestClassifier(

    n_estimators=args.trees,

    random_state=args.seed,

    class_weight="balanced",

    n_jobs=-1

)


rf.fit(
    X,
    y
)


########################################################
# Feature importance
########################################################

importance = pd.DataFrame(

    {

        "Feature":
            feature_cols,

        "Importance":
            rf.feature_importances_

    }

)


importance = importance.sort_values(

    "Importance",

    ascending=False

).reset_index(
    drop=True
)


########################################################
# Select top features
########################################################

top = min(
    args.top,
    len(feature_cols)
)


if args.top > len(feature_cols):

    print(
        f"Requested top={args.top}, "
        f"but only {len(feature_cols)} "
        "features are available."
    )


selected = (
    importance
    .head(top)
    .copy()
)


selected_features = (
    selected["Feature"]
    .tolist()
)


########################################################
# Create filtered training dataset
########################################################

filtered = pd.concat(

    [

        data[
            meta_cols
        ],

        data[
            selected_features
        ]

    ],

    axis=1

)


########################################################
# Save filtered training data
########################################################

filtered.to_csv(

    args.train_output,

    sep="\t",

    index=False

)


########################################################
# Save selected features
########################################################

selected.to_csv(

    args.feature_output,

    sep="\t",

    index=False

)


########################################################
# Save all feature importances
########################################################

importance.to_csv(

    args.importance_output,

    sep="\t",

    index=False

)


########################################################
# Summary
########################################################

print()

print(
    "Label column      :",
    target_col
)

print(
    "Original Features :",
    len(feature_cols)
)

print(
    "Selected Features :",
    len(selected_features)
)

print()