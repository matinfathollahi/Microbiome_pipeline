#!/usr/bin/env python3

import argparse

import pandas as pd

from sklearn.preprocessing import (

    StandardScaler,

    MinMaxScaler,

    RobustScaler

)

########################################################

parser = argparse.ArgumentParser()

parser.add_argument("--train", required=True)

parser.add_argument("--test", required=True)

parser.add_argument("--method", required=True)

parser.add_argument("--metadata", required=True)

parser.add_argument("--train_output", required=True)

parser.add_argument("--test_output", required=True)

args = parser.parse_args()

########################################################

train = pd.read_csv(

    args.train,

    sep="\t"

)

test = pd.read_csv(

    args.test,

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

    if x in train.columns

]

if args.metadata and not meta_cols:
    raise ValueError(
        "None of the specified metadata columns were found in the training file."
    )

########################################################

feature_cols = [

    c

    for c in train.columns

    if c not in meta_cols

]

if not feature_cols:
    raise ValueError(
        "No feature columns found for scaling."
    )

# بررسی عددی بودن featureها
non_numeric = train[feature_cols].select_dtypes(
    exclude="number"
).columns.tolist()

if non_numeric:
    raise ValueError(
        f"The following feature columns are not numeric: {non_numeric}"
    )

########################################################


########################################################

if args.method == "standard":

    scaler = StandardScaler()

elif args.method == "minmax":

    scaler = MinMaxScaler()

elif args.method == "robust":

    scaler = RobustScaler()

else:

    raise ValueError("Unknown scaling method.")

########################################################

# بررسی وجود ستون‌های متادیتا در test
missing_meta = set(meta_cols) - set(test.columns)

if missing_meta:
    raise ValueError(
        f"The following metadata columns are missing in test file: {sorted(missing_meta)}"
    )

# بررسی وجود ستون‌های Feature در test
missing_features = set(feature_cols) - set(test.columns)

if missing_features:
    raise ValueError(
        f"The following feature columns are missing in test file: {sorted(missing_features)}"
    )

# بررسی عددی بودن Featureهای test
non_numeric_test = test[feature_cols].select_dtypes(
    exclude="number"
).columns.tolist()

if non_numeric_test:
    raise ValueError(
        f"The following feature columns in test are not numeric: {non_numeric_test}"
    )

# بررسی وجود مقادیر گمشده در train
if train[feature_cols].isnull().any().any():
    raise ValueError(
        "Training data contains missing values (NaN)."
    )

# بررسی وجود مقادیر گمشده در test
if test[feature_cols].isnull().any().any():
    raise ValueError(
        "Test data contains missing values (NaN)."
    )


train_scaled = scaler.fit_transform(
    train[feature_cols]
)

test_scaled = scaler.transform(
    test[feature_cols]
)




########################################################

train_scaled = pd.DataFrame(

    train_scaled,

    columns=feature_cols

)

########################################################

test_scaled = pd.DataFrame(

    test_scaled,

    columns=feature_cols

)

########################################################

train_out = pd.concat(

    [

        train[meta_cols].reset_index(drop=True),

        train_scaled

    ],

    axis=1

)

########################################################

test_out = pd.concat(

    [

        test[meta_cols].reset_index(drop=True),

        test_scaled

    ],

    axis=1

)

########################################################

train_out.to_csv(

    args.train_output,

    sep="\t",

    index=False

)

########################################################

test_out.to_csv(

    args.test_output,

    sep="\t",

    index=False

)

########################################################

print("Scaling method:", args.method)

print("Features:", len(feature_cols))