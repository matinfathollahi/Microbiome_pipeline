#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


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
        "--groups",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--label",
        required=True
    )

    parser.add_argument(
        "--features",
        required=True
    )

    parser.add_argument(
        "--labels",
        required=True
    )

    args = parser.parse_args()

    data = pd.read_csv(
        args.input,
        sep="\t"
    )

    metadata = pd.read_csv(
        args.metadata,
        sep="\t"
    )

    if "SampleID" not in data.columns:
        raise ValueError(
            "SampleID not found in ML dataset."
        )

    if args.label not in data.columns:
        raise ValueError(
            f"Label column '{args.label}' not found."
        )


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

    metadata_columns = set(
        metadata.columns
    )

    feature_columns = [
        column
        for column in data.columns
        if column not in metadata_columns
    ]

    if not feature_columns:
        raise ValueError(
            "No microbiome feature columns found."
        )

    non_numeric = (
        data[feature_columns]
        .select_dtypes(exclude="number")
        .columns
        .tolist()
    )

    if non_numeric:
        raise ValueError(
            "Non-numeric microbiome features found: "
            f"{non_numeric[:10]}"
        )

    X = (
        data[
            ["SampleID"] + feature_columns
        ]
        .set_index("SampleID")
    )

    y = (
        data[
            ["SampleID", args.label]
        ]
        .set_index("SampleID")
    )


    groups = (
        data[
            ["SampleID", args.group]
        ]
        .set_index("SampleID")
    )


    if X.isna().any().any():
        raise ValueError(
            "Missing values found in features."
        )

    if y[args.label].isna().any():
        raise ValueError(
            "Missing labels found."
        )

    Path(
        args.features
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    X.to_csv(
        args.features,
        sep="\t"
    )

    y.to_csv(
        args.labels,
        sep="\t"
    )

    print(
        f"Samples  : {len(X)}"
    )

    print(
        f"Features : {len(feature_columns)}"
    )


    groups.to_csv(
        args.groups,
        sep="\t"
    )

if __name__ == "__main__":
    main()