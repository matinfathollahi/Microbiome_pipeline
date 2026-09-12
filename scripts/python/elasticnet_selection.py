#!/usr/bin/env python3

import argparse
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold

########################################################

parser = argparse.ArgumentParser()

parser.add_argument("--input", required=True)

parser.add_argument(
    "--label",
    required=True
)

parser.add_argument("--cv", type=int, default=5)

parser.add_argument("--l1", type=float, default=0.5)

parser.add_argument("--seed", type=int, default=2026)

parser.add_argument("--metadata", required=True)

parser.add_argument("--train_output", required=True)

parser.add_argument("--feature_output", required=True)

parser.add_argument("--coef_output", required=True)

args = parser.parse_args()
target_col = args.label

########################################################

data = pd.read_csv(

    args.input,

    sep="\t"

)

########################################################

meta_cols = [

    x.strip()

    for x in args.metadata.split(",")

]

meta_cols = [

    x

    for x in meta_cols

    if x in data.columns

]

########################################################

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

    c

    for c in meta_cols

    if c in data.columns
]


feature_cols = [

    c

    for c in data.columns

    if c not in meta_cols
]

########################################################


X = data[
    feature_cols
]

y = data[
    target_col
]






cv = StratifiedKFold(
    n_splits=args.cv,
    shuffle=True,
    random_state=args.seed
)

########################################################

pipe = Pipeline(

    [

        (

            "scaler",

            StandardScaler()

        ),

        (

            "model",

            LogisticRegressionCV(

                penalty="elasticnet",

                solver="saga",

                cv=cv,

                l1_ratios=[args.l1],

                random_state=args.seed,
                class_weight="balanced",

                max_iter=10000,

                scoring="roc_auc",

                n_jobs=-1

            )

        )

    ]

)

########################################################

if X.isnull().values.any():
    raise ValueError("Input data contains missing values.")

non_numeric = X.select_dtypes(exclude="number").columns

if len(non_numeric):
    raise ValueError(
        f"Non-numeric feature columns found: {list(non_numeric)}"
    )

pipe.fit(

    X,

    y

)

########################################################

coef = pipe.named_steps["model"].coef_[0]

########################################################

coef_table = pd.DataFrame(

    {

        "Feature": feature_cols,

        "Coefficient": coef

    }

)

########################################################

coef_table = coef_table.sort_values(

    "Coefficient",

    key=lambda x: abs(x),

    ascending=False

)

########################################################

selected = coef_table[

    coef_table["Coefficient"] != 0

]

########################################################

selected_features = selected["Feature"].tolist()

########################################################

filtered = pd.concat(

    [

        data[meta_cols],

        data[selected_features]

    ],

    axis=1

)

########################################################

filtered.to_csv(

    args.train_output,

    sep="\t",

    index=False

)

########################################################

selected.to_csv(

    args.feature_output,

    sep="\t",

    index=False

)

########################################################

coef_table.to_csv(

    args.coef_output,

    sep="\t",

    index=False

)

########################################################

print()
print("Input Features :", len(feature_cols))
print("ElasticNet Selected Features :", len(selected_features))
print()