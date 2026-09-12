#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Apply an existing train/test SampleID split "
            "to another dataset."
        )
    )

    parser.add_argument(
        "--dataset",
        required=True
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
        "--sample-column",
        default="SampleID"
    )

    parser.add_argument(
        "--train-output",
        required=True
    )

    parser.add_argument(
        "--test-output",
        required=True
    )

    return parser.parse_args()


def main():

    args = parse_args()

    dataset = pd.read_csv(
        args.dataset,
        sep="\t"
    )

    train_manifest = pd.read_csv(
        args.train_samples,
        sep="\t"
    )

    test_manifest = pd.read_csv(
        args.test_samples,
        sep="\t"
    )


    sample_column = args.sample_column


    ########################################################
    # Validate columns
    ########################################################

    for name, frame in [
        ("dataset", dataset),
        ("train manifest", train_manifest),
        ("test manifest", test_manifest),
    ]:

        if sample_column not in frame.columns:

            raise ValueError(
                f"{sample_column} missing from {name}."
            )


    ########################################################
    # Clean SampleIDs
    ########################################################

    dataset[sample_column] = (
        dataset[sample_column]
        .astype(str)
        .str.strip()
    )

    train_manifest[sample_column] = (
        train_manifest[sample_column]
        .astype(str)
        .str.strip()
    )

    test_manifest[sample_column] = (
        test_manifest[sample_column]
        .astype(str)
        .str.strip()
    )


    ########################################################
    # Duplicate checks
    ########################################################

    if dataset[sample_column].duplicated().any():

        raise ValueError(
            "Duplicate SampleIDs in dataset."
        )


    if train_manifest[sample_column].duplicated().any():

        raise ValueError(
            "Duplicate SampleIDs in train manifest."
        )


    if test_manifest[sample_column].duplicated().any():

        raise ValueError(
            "Duplicate SampleIDs in test manifest."
        )


    ########################################################
    # Train/test overlap check
    ########################################################

    train_ids = set(
        train_manifest[sample_column]
    )

    test_ids = set(
        test_manifest[sample_column]
    )


    overlap = (
        train_ids
        &
        test_ids
    )


    if overlap:

        raise ValueError(
            "Train/test overlap detected: "
            + ", ".join(
                sorted(overlap)[:20]
            )
        )


    ########################################################
    # Dataset completeness
    ########################################################

    dataset_ids = set(
        dataset[sample_column]
    )


    missing_train = (
        train_ids
        -
        dataset_ids
    )

    missing_test = (
        test_ids
        -
        dataset_ids
    )


    if missing_train:

        raise ValueError(
            "Train SampleIDs missing from corrected dataset: "
            + ", ".join(
                sorted(missing_train)[:20]
            )
        )


    if missing_test:

        raise ValueError(
            "Test SampleIDs missing from corrected dataset: "
            + ", ".join(
                sorted(missing_test)[:20]
            )
        )


    ########################################################
    # Subset while preserving manifest order
    ########################################################

    indexed = dataset.set_index(
        sample_column,
        drop=False
    )


    train_df = indexed.loc[
        train_manifest[sample_column]
    ].reset_index(
        drop=True
    )


    test_df = indexed.loc[
        test_manifest[sample_column]
    ].reset_index(
        drop=True
    )


    ########################################################
    # Write
    ########################################################

    Path(
        args.train_output
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    Path(
        args.test_output
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )


    train_df.to_csv(
        args.train_output,
        sep="\t",
        index=False
    )

    test_df.to_csv(
        args.test_output,
        sep="\t",
        index=False
    )


    print(
        "Existing split applied successfully."
    )

    print(
        f"Train samples: {len(train_df)}"
    )

    print(
        f"Test samples: {len(test_df)}"
    )


if __name__ == "__main__":

    main()