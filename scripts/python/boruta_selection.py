#!/usr/bin/env python3

import argparse
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

from boruta import BorutaPy



############################################################

parser = argparse.ArgumentParser()

parser.add_argument(
    "--label",
    required=True
)

parser.add_argument("--input", required=True)

parser.add_argument("--trees", type=int, default=1000)

parser.add_argument("--max_iter", type=int, default=200)

parser.add_argument("--seed", type=int, default=2026)

parser.add_argument("--metadata", required=True)

parser.add_argument("--train_output", required=True)

parser.add_argument("--feature_output", required=True)

parser.add_argument("--ranking_output", required=True)

args = parser.parse_args()

############################################################

data = pd.read_csv(

    args.input,

    sep="\t"

)

target_col = args.label

############################################################

meta_cols = [

    x.strip()

    for x in args.metadata.split(",")

    if x.strip()
]


if target_col not in data.columns:

    raise ValueError(
        f"Target column '{target_col}' "
        "not found in input file."
    )


if target_col not in meta_cols:

    meta_cols.append(
        target_col
    )


meta_cols = [

    x

    for x in meta_cols

    if x in data.columns
]

############################################################
if target_col not in data.columns:
    raise ValueError(f"Target column '{target_col}' not found in input file.")


feature_cols = [
    c
    for c in data.columns
    if c not in meta_cols and c != target_col
]

if len(feature_cols) == 0:
    raise ValueError("No feature columns found.")

############################################################

X = data[feature_cols].values

y = data[target_col].values

############################################################

rf = RandomForestClassifier(

    n_estimators=args.trees,

    class_weight="balanced",

    random_state=args.seed,

    n_jobs=-1

)

############################################################

selector = BorutaPy(

    rf,

    n_estimators=args.trees,

    max_iter=args.max_iter,

    random_state=args.seed,

    verbose=2

)

############################################################

if data[feature_cols].isnull().any().any():
    raise ValueError("Missing values detected in feature matrix.")

selector.fit(

    X,

    y

)

############################################################

selected_features = [

    feature_cols[i]

    for i in range(len(feature_cols))

    if selector.support_[i]

]

############################################################

filtered = pd.concat(
    [
        data[meta_cols],
        data[selected_features]
    ],
    axis=1
)

############################################################

filtered.to_csv(

    args.train_output,

    sep="\t",

    index=False

)

############################################################

pd.DataFrame(

    {

        "Feature": selected_features

    }

).to_csv(

    args.feature_output,

    sep="\t",

    index=False

)

############################################################

ranking = pd.DataFrame(

    {

        "Feature": feature_cols,

        "Ranking": selector.ranking_,

        "Selected": selector.support_

    }

)

############################################################

ranking.to_csv(

    args.ranking_output,

    sep="\t",

    index=False

)

############################################################

print()

print("Original Features :", len(feature_cols))

print("Boruta Features   :", len(selected_features))

print()