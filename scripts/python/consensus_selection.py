#!/usr/bin/env python3

import argparse
import pandas as pd
from collections import Counter


############################################################
# Arguments
############################################################

parser = argparse.ArgumentParser()

parser.add_argument(
    "--train",
    required=True
)

parser.add_argument(
    "--boruta",
    required=True
)

parser.add_argument(
    "--elastic",
    required=True
)

parser.add_argument(
    "--rf",
    required=True
)

parser.add_argument(
    "--minimum",
    type=int,
    default=2
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

args = parser.parse_args()


############################################################
# Validate minimum votes
############################################################

if args.minimum < 1 or args.minimum > 3:
    raise ValueError(
        "--minimum must be between 1 and 3"
    )


############################################################
# Read training data
############################################################

train = pd.read_csv(
    args.train,
    sep="\t"
)


############################################################
# Label
############################################################

target_col = args.label


if target_col not in train.columns:
    raise ValueError(
        f"Label column '{target_col}' "
        "not found in training data."
    )


############################################################
# Metadata columns
############################################################

meta_cols = [

    x.strip()

    for x in args.metadata.split(",")

    if x.strip()
]


# Make sure label is metadata, not a feature
if target_col not in meta_cols:
    meta_cols.append(
        target_col
    )


# Keep only metadata columns present in dataset
meta_cols = [

    x

    for x in meta_cols

    if x in train.columns
]


############################################################
# Read selected features from each method
############################################################

boruta_table = pd.read_csv(
    args.boruta,
    sep="\t"
)

elastic_table = pd.read_csv(
    args.elastic,
    sep="\t"
)

rf_table = pd.read_csv(
    args.rf,
    sep="\t"
)


############################################################
# Validate Feature column
############################################################

for name, table in [

    ("Boruta", boruta_table),

    ("ElasticNet", elastic_table),

    ("RandomForest", rf_table)

]:

    if "Feature" not in table.columns:

        raise ValueError(
            f"{name} feature file does not "
            "contain a 'Feature' column."
        )


############################################################
# Feature lists
############################################################

boruta = (
    boruta_table["Feature"]
    .dropna()
    .astype(str)
    .str.strip()
    .tolist()
)


elastic = (
    elastic_table["Feature"]
    .dropna()
    .astype(str)
    .str.strip()
    .tolist()
)


rf = (
    rf_table["Feature"]
    .dropna()
    .astype(str)
    .str.strip()
    .tolist()
)


############################################################
# Count votes
############################################################

counter = Counter()


for feature in set(boruta):

    if feature:
        counter[feature] += 1


for feature in set(elastic):

    if feature:
        counter[feature] += 1


for feature in set(rf):

    if feature:
        counter[feature] += 1


############################################################
# Consensus selection
############################################################

selected = [

    feature

    for feature, votes in counter.items()

    if votes >= args.minimum
]


############################################################
# Remove metadata accidentally appearing in feature lists
############################################################

selected = [

    feature

    for feature in selected

    if feature not in meta_cols
]


############################################################
# Check features exist in training data
############################################################

missing = [

    feature

    for feature in selected

    if feature not in train.columns
]


if missing:

    print(
        f"Warning: {len(missing)} consensus "
        "features were not found in training data:"
    )

    print(
        ", ".join(missing[:20])
    )


selected = [

    feature

    for feature in selected

    if feature in train.columns
]


############################################################
# Stop if nothing selected
############################################################

if not selected:

    raise ValueError(
        "No consensus features found "
        "after filtering."
    )


############################################################
# Consensus table
############################################################

consensus = pd.DataFrame(

    {

        "Feature":
            selected,

        "Methods":
            [
                counter[feature]
                for feature in selected
            ]

    }

)


############################################################
# Sort consensus
############################################################

consensus = consensus.sort_values(

    [
        "Methods",
        "Feature"
    ],

    ascending=[
        False,
        True
    ]

).reset_index(
    drop=True
)


# Preserve the same order in filtered training data
selected = (
    consensus["Feature"]
    .tolist()
)


############################################################
# Create consensus training dataset
############################################################

filtered = pd.concat(

    [

        train[
            meta_cols
        ],

        train[
            selected
        ]

    ],

    axis=1

)


############################################################
# Save outputs
############################################################

filtered.to_csv(

    args.train_output,

    sep="\t",

    index=False

)


consensus.to_csv(

    args.feature_output,

    sep="\t",

    index=False

)


############################################################
# Summary
############################################################

print()

print(
    "Label column       :",
    target_col
)

print(
    "Minimum methods    :",
    args.minimum
)

print(
    "Boruta features    :",
    len(set(boruta))
)

print(
    "ElasticNet features:",
    len(set(elastic))
)

print(
    "RF features        :",
    len(set(rf))
)

print(
    "Consensus features :",
    len(selected)
)

print()