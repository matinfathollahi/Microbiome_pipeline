#!/usr/bin/env python3

import argparse

import pandas as pd

###########################################################

parser = argparse.ArgumentParser()

parser.add_argument("--table", required=True)

parser.add_argument("--metadata", required=True)

parser.add_argument("--label", required=True)

parser.add_argument("--output", required=True)

args = parser.parse_args()

###########################################################

table = pd.read_csv(

    args.table,

    sep="\t",

    index_col=0

)

###########################################################

# Features become columns

table = table.T

table.index.name = "SampleID"

table.reset_index(inplace=True)


if "SampleID" not in table.columns:
    raise ValueError(
        "SampleID column was not created from the feature table."
    )

###########################################################

metadata = pd.read_csv(

    args.metadata,

    sep="\t"

)


if "SampleID" not in metadata.columns:
    raise ValueError(
        "SampleID column not found in metadata."
    )

###########################################################

dataset = metadata.merge(

    table,

    on="SampleID",

    how="inner"

)

if dataset.empty:
    raise ValueError(
        "No matching SampleID between metadata and feature table."
    )

###########################################################

dataset.drop_duplicates(

    subset="SampleID",

    inplace=True

)

###########################################################

if args.label not in dataset.columns:
    raise ValueError(
        f"Label column '{args.label}' not found."
    )

dataset = dataset.dropna(

    subset=[args.label]

)

###########################################################

priority = [

    "SampleID",

    args.label,

    "Study",

    "Age",

    "Sex",

    "BMI"

]

priority = [

    c for c in priority

    if c in dataset.columns

]

###########################################################

others = [

    c for c in dataset.columns

    if c not in priority

]

###########################################################

dataset = dataset[

    priority + others

]

###########################################################

dataset.to_csv(

    args.output,

    sep="\t",

    index=False

)

###########################################################

print(

    "Samples:",

    dataset.shape[0]

)

print(

    "Features:",

    len(others)

)