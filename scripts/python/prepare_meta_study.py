#!/usr/bin/env python3

import argparse
from io import StringIO
from pathlib import Path

import pandas as pd


def read_feature_table(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:

        lines = handle.readlines()

    lines = [
        line
        for line in lines
        if not line.startswith(
            "# Constructed from biom file"
        )
    ]

    if not lines:
        raise ValueError(
            "Feature table is empty."
        )

    table = pd.read_csv(
        StringIO("".join(lines)),
        sep="\t"
    )

    if table.shape[1] < 2:
        raise ValueError(
            "Feature table must contain feature IDs "
            "and at least one sample."
        )

    first_column = table.columns[0]

    table = table.rename(
        columns={
            first_column: "FeatureID"
        }
    )

    if table["FeatureID"].duplicated().any():

        duplicated = (
            table.loc[
                table["FeatureID"].duplicated(),
                "FeatureID"
            ]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            f"Duplicated feature IDs: {duplicated[:10]}"
        )

    return table


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--table",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--study-column",
        required=True
    )

    parser.add_argument(
        "--study-id",
        required=True
    )

    parser.add_argument(
        "--study-map",
        required=True
    )

    parser.add_argument(
        "--sample-column",
        default="SampleID"
    )

    parser.add_argument(
        "--output-table",
        required=True
    )

    parser.add_argument(
        "--output-metadata",
        required=True
    )

    args = parser.parse_args()






    study_map = pd.read_csv(
        args.study_map,
        sep="\t",
        dtype=str
    )


    required_map_columns = [
        "StudyID",
        "StudyValue"
    ]


    missing_map_columns = [
        column
        for column in required_map_columns
        if column not in study_map.columns
    ]


    if missing_map_columns:

        raise ValueError(
            "Study map missing columns: "
            f"{missing_map_columns}"
        )


    matched = study_map.loc[
        study_map["StudyID"]
        == str(args.study_id)
    ]


    if len(matched) != 1:

        raise ValueError(
            f"StudyID '{args.study_id}' "
            "was not found uniquely "
            "in study map."
        )


    study_value = (
        matched[
            "StudyValue"
        ]
        .iloc[0]
    )








    table = read_feature_table(
        args.table
    )

    metadata = pd.read_csv(
        args.metadata,
        sep="\t",
        dtype=str
    )

    required = [
        args.sample_column,
        args.study_column
    ]

    missing = [
        column
        for column in required
        if column not in metadata.columns
    ]

    if missing:
        raise ValueError(
            f"Missing metadata columns: {missing}"
        )

    if metadata[
        args.sample_column
    ].duplicated().any():

        raise ValueError(
            "Duplicated sample IDs in metadata."
        )

    study_metadata = metadata.loc[
        metadata[
            args.study_column
        ].astype(str)
        == str(study_value)
    ].copy()

    if study_metadata.empty:

        raise ValueError(
            f"No samples found for study "
            f"'{study_value}'."
        )

    available_samples = set(
        table.columns[1:]
    )

    study_samples = [
        sample
        for sample in study_metadata[
            args.sample_column
        ].astype(str)
        if sample in available_samples
    ]

    if not study_samples:

        raise ValueError(
            f"No matching feature-table samples "
            f"for study '{study_value}'."
        )

    study_metadata = (
        study_metadata
        .set_index(args.sample_column)
        .loc[study_samples]
        .reset_index()
    )

    study_table = table[
        ["FeatureID"] + study_samples
    ].copy()

    numeric = (
        study_table[study_samples]
        .apply(
            pd.to_numeric,
            errors="coerce"
        )
    )

    if numeric.isna().any().any():

        raise ValueError(
            "Non-numeric or missing count values "
            "were found."
        )

    if (numeric < 0).any().any():

        raise ValueError(
            "Negative counts were found."
        )

    study_table[
        study_samples
    ] = numeric


############################################################
    # Remove samples with zero total counts
    ############################################################

    sample_totals = numeric.sum(axis=0)

    zero_samples = [
        sample
        for sample in study_samples
        if sample_totals[sample] == 0
    ]

    if zero_samples:

        study_samples = [
            sample
            for sample in study_samples
            if sample not in zero_samples
        ]

        if not study_samples:
            raise ValueError(
                f"All samples for study '{study_value}' "
                "have zero total counts."
            )

        study_metadata = (
            study_metadata[
                study_metadata[
                    args.sample_column
                ].isin(study_samples)
            ]
            .copy()
        )

        study_table = table[
            ["FeatureID"] + study_samples
        ].copy()

        numeric = (
            study_table[study_samples]
            .apply(
                pd.to_numeric,
                errors="coerce"
            )
        )

        study_table[
            study_samples
        ] = numeric

        print(
            f"Zero-total samples removed: "
            f"{len(zero_samples)}"
        )

        print(
            "Removed samples: "
            + ", ".join(zero_samples)
        )

    Path(
        args.output_table
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    Path(
        args.output_metadata
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    study_table.to_csv(
        args.output_table,
        sep="\t",
        index=False
    )

    study_metadata.to_csv(
        args.output_metadata,
        sep="\t",
        index=False
    )

    print(
        f"Study       : {study_value}"
    )

    print(
        f"Samples     : {len(study_samples)}"
    )

    print(
        f"Features    : {len(study_table)}"
    )


if __name__ == "__main__":
    main()