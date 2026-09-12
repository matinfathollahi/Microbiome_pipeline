#!/usr/bin/env python3

import argparse
import json

from pathlib import Path

import joblib
import pandas as pd

from microbiome_preprocessing import (
    MicrobiomeCLRPreprocessor
)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--train",
        required=True
    )

    parser.add_argument(
        "--test",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--min-count",
        type=float,
        required=True
    )

    parser.add_argument(
        "--prevalence",
        type=float,
        required=True
    )

    parser.add_argument(
        "--zero-fraction",
        type=float,
        default=0.5
    )

    parser.add_argument(
        "--train-output",
        required=True
    )

    parser.add_argument(
        "--test-output",
        required=True
    )

    parser.add_argument(
        "--features-output",
        required=True
    )

    parser.add_argument(
        "--model-output",
        required=True
    )

    parser.add_argument(
        "--summary-output",
        required=True
    )

    args = parser.parse_args()

    train = pd.read_csv(
        args.train,
        sep="\t"
    )

    test = pd.read_csv(
        args.test,
        sep="\t"
    )

    metadata = pd.read_csv(
        args.metadata,
        sep="\t"
    )

    metadata_columns = set(
        metadata.columns
    )

    feature_columns = [

        column

        for column in train.columns

        if column not in metadata_columns
    ]

    if not feature_columns:

        raise ValueError(
            "No microbiome features found."
        )

    ########################################################
    # Same raw features in held-out test
    ########################################################

    missing_test = [

        feature

        for feature in feature_columns

        if feature not in test.columns
    ]

    if missing_test:

        raise ValueError(
            "Held-out test is missing features: "
            f"{missing_test[:10]}"
        )

    ########################################################
    # FIT ONLY ON TRAINING DATA
    ########################################################

    preprocessor = MicrobiomeCLRPreprocessor(

        min_count=
            args.min_count,

        prevalence=
            args.prevalence,

        zero_fraction=
            args.zero_fraction
    )

    train_clr = (
        preprocessor
        .fit_transform(
            train[
                feature_columns
            ]
        )
    )

    ########################################################
    # TEST ONLY TRANSFORMED
    ########################################################

    test_clr = (
        preprocessor
        .transform(
            test[
                feature_columns
            ]
        )
    )

    ########################################################
    # Preserve metadata
    ########################################################

    train_metadata_columns = [

        column

        for column in train.columns

        if column not in feature_columns
    ]

    test_metadata_columns = [

        column

        for column in test.columns

        if column not in feature_columns
    ]

    train_output = pd.concat(

        [
            train[
                train_metadata_columns
            ].reset_index(
                drop=True
            ),

            train_clr.reset_index(
                drop=True
            )
        ],

        axis=1
    )

    test_output = pd.concat(

        [
            test[
                test_metadata_columns
            ].reset_index(
                drop=True
            ),

            test_clr.reset_index(
                drop=True
            )
        ],

        axis=1
    )

    ########################################################

    Path(
        args.train_output
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    train_output.to_csv(
        args.train_output,
        sep="\t",
        index=False
    )

    test_output.to_csv(
        args.test_output,
        sep="\t",
        index=False
    )

    pd.DataFrame(
        {
            "Feature":
                preprocessor
                .selected_features_
        }
    ).to_csv(

        args.features_output,

        sep="\t",

        index=False
    )

    joblib.dump(

        preprocessor,

        args.model_output
    )

    summary = {

        "input_features":
            len(
                feature_columns
            ),

        "selected_features":
            len(
                preprocessor
                .selected_features_
            ),

        "min_count":
            args.min_count,

        "prevalence":
            args.prevalence,

        "zero_fraction":
            args.zero_fraction,

        "fit_samples":
            len(train),

        "heldout_samples":
            len(test),

        "leakage_policy":
            (
                "Abundance/prevalence feature mask "
                "was learned from training samples only."
            )
    }

    with open(

        args.summary_output,

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            summary,
            handle,
            indent=2
        )


if __name__ == "__main__":

    main()