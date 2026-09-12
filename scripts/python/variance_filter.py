#!/usr/bin/env python3

import argparse
import pandas as pd

from sklearn.feature_selection import VarianceThreshold

############################################################

parser = argparse.ArgumentParser()

parser.add_argument("--input", required=True)

parser.add_argument("--threshold", type=float, required=True)

parser.add_argument("--metadata", required=True)
parser.add_argument("--label", required=True)

parser.add_argument("--train_output", required=True)

parser.add_argument("--selected_output", required=True)

parser.add_argument("--removed_output", required=True)

args = parser.parse_args()

############################################################

data = pd.read_csv(

    args.input,

    sep="\t"

)

############################################################

meta_cols = [

    x.strip()

    for x in args.metadata.split(",")

    if x.strip()
]


if args.label not in data.columns:

    raise ValueError(
        f"Label column '{args.label}' "
        "not found in input file."
    )


if args.label not in meta_cols:

    meta_cols.append(
        args.label
    )


meta_cols = [

    x

    for x in meta_cols

    if x in data.columns
]

############################################################

feature_cols = [

    c

    for c in data.columns

    if c not in meta_cols

]

############################################################

X = data[feature_cols]

original_feature_count = len(feature_cols)

# حذف ستون‌های غیرعددی از feature ها
non_numeric = X.select_dtypes(exclude=["number"]).columns
non_numeric_count = len(non_numeric)

if len(non_numeric) > 0:
    print("Non-numeric columns removed:")
    for col in non_numeric:
        print("  ", col)

X = X.select_dtypes(include=["number"])

feature_cols = list(X.columns)

if len(feature_cols) == 0:
    raise ValueError(
        "No numeric feature columns available."
    )

if X.isna().sum().sum() > 0:
    print("Missing values detected. Filling with median.")
    X = X.fillna(X.median())




############################################################

selector = VarianceThreshold(

    threshold=args.threshold

)

selector.fit(X)

############################################################

selected = X.columns[

    selector.get_support()

]


if len(selected) == 0:
    raise ValueError(
        "All features were removed by variance threshold."
    )

############################################################

removed = X.columns[

    ~selector.get_support()

]

############################################################

filtered = pd.concat(

    [

        data[meta_cols],

        X[selected]

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

        "Feature": selected

    }

).to_csv(

    args.selected_output,

    sep="\t",

    index=False

)

############################################################

pd.DataFrame(

    {

        "Feature": removed

    }

).to_csv(

    args.removed_output,

    sep="\t",

    index=False

)

############################################################

print()

print("Original features        :", original_feature_count)
print("Non-numeric removed      :", non_numeric_count)
print("Variance selected        :", len(selected))
print("Variance removed         :", len(removed))
print("Final feature count      :", len(selected))

print()