#!/usr/bin/env python3

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd


def safe_study_id(value):

    value = str(value).strip()

    slug = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        value
    ).strip("_")

    if not slug:
        slug = "study"

    digest = hashlib.sha1(
        value.encode("utf-8")
    ).hexdigest()[:8]

    return f"{slug}_{digest}"


def read_feature_table_samples(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:

        for line in handle:

            if not line.strip():
                continue

            if line.startswith(
                "# Constructed from biom file"
            ):
                continue

            header = (
                line
                .rstrip("\n\r")
                .split("\t")
            )

            if len(header) < 2:

                raise ValueError(
                    "Feature table must contain "
                    "a feature ID column and "
                    "at least one sample."
                )

            samples = [
                str(x).strip()
                for x in header[1:]
                if str(x).strip()
            ]

            if not samples:

                raise ValueError(
                    "No sample columns found "
                    "in feature table."
                )

            if len(samples) != len(set(samples)):

                raise ValueError(
                    "Duplicated sample columns "
                    "found in feature table."
                )

            return set(samples)

    raise ValueError(
        "Feature table is empty."
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--feature-table",
        required=True
    )

    parser.add_argument(
        "--study-column",
        required=True
    )

    parser.add_argument(
        "--sample-column",
        required=True
    )

    parser.add_argument(
        "--group-column",
        required=True
    )

    parser.add_argument(
        "--reference-group",
        required=True
    )

    parser.add_argument(
        "--case-group",
        required=True
    )

    parser.add_argument(
        "--min-samples-per-group",
        type=int,
        required=True
    )

    parser.add_argument(
        "--min-samples-per-study",
        type=int,
        required=True
    )

    parser.add_argument(
        "--min-studies",
        type=int,
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--report",
        required=True
    )

    args = parser.parse_args()


    ########################################################
    # Validate parameters
    ########################################################

    if (
        args.reference_group
        ==
        args.case_group
    ):

        raise ValueError(
            "reference_group and case_group "
            "must be different."
        )


    if args.min_samples_per_group < 1:

        raise ValueError(
            "min_samples_per_group "
            "must be >= 1."
        )


    if args.min_samples_per_study < 2:

        raise ValueError(
            "min_samples_per_study "
            "must be >= 2."
        )


    if args.min_studies < 2:

        raise ValueError(
            "min_studies must be >= 2."
        )


    ########################################################
    # Read metadata
    ########################################################

    metadata = pd.read_csv(
        args.metadata,
        sep="\t",
        dtype=str
    )


    required_columns = [

        args.sample_column,

        args.study_column,

        args.group_column
    ]


    missing_columns = [

        column

        for column
        in required_columns

        if column
        not in metadata.columns
    ]


    if missing_columns:

        raise ValueError(
            "Metadata missing columns: "
            f"{missing_columns}"
        )


    ########################################################
    # Normalize values
    ########################################################

    for column in required_columns:

        metadata[column] = (
            metadata[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )


    metadata = metadata.loc[

        (metadata[args.sample_column] != "")

        &

        (metadata[args.study_column] != "")

        &

        (metadata[args.group_column] != "")

    ].copy()


    if metadata.empty:

        raise ValueError(
            "No usable metadata rows remain "
            "after removing blank values."
        )


    ########################################################
    # Sample IDs must be unique
    ########################################################

    if metadata[
        args.sample_column
    ].duplicated().any():

        duplicated = (

            metadata.loc[
                metadata[
                    args.sample_column
                ].duplicated(),
                args.sample_column
            ]

            .drop_duplicates()

            .tolist()
        )

        raise ValueError(
            "Duplicated sample IDs "
            f"in metadata: {duplicated[:10]}"
        )


    ########################################################
    # Only count samples actually present in feature table
    ########################################################

    feature_samples = (
        read_feature_table_samples(
            args.feature_table
        )
    )


    metadata[
        "__in_feature_table"
    ] = (

        metadata[
            args.sample_column
        ].isin(
            feature_samples
        )
    )


    ########################################################
    # Discover all study values
    ########################################################

    studies = sorted(

        metadata[
            args.study_column
        ]
        .unique()
        .tolist()
    )


    if not studies:

        raise ValueError(
            "No valid studies found "
            "in metadata."
        )


    ########################################################
    # Determine eligibility
    ########################################################

    rows = []

    eligible_rows = []

    used_ids = set()


    for study_value in studies:

        study_meta_all = metadata.loc[

            metadata[
                args.study_column
            ]
            ==
            study_value

        ].copy()


        ####################################################
        # Only matched Control/Disease samples
        ####################################################

        study_meta = study_meta_all.loc[

            study_meta_all[
                "__in_feature_table"
            ]

            &

            study_meta_all[
                args.group_column
            ].isin(
                [
                    args.reference_group,
                    args.case_group
                ]
            )

        ].copy()


        ####################################################
        # Count samples
        ####################################################

        reference_n = int(

            (
                study_meta[
                    args.group_column
                ]
                ==
                args.reference_group
            ).sum()
        )


        case_n = int(

            (
                study_meta[
                    args.group_column
                ]
                ==
                args.case_group
            ).sum()
        )


        total_n = (
            reference_n
            +
            case_n
        )


        matched_n = int(

            study_meta_all[
                "__in_feature_table"
            ].sum()
        )


        ####################################################
        # Eligibility reasons
        ####################################################

        reasons = []


        if (
            reference_n
            <
            args.min_samples_per_group
        ):

            reasons.append(

                f"{args.reference_group}="
                f"{reference_n} < "
                f"{args.min_samples_per_group}"
            )


        if (
            case_n
            <
            args.min_samples_per_group
        ):

            reasons.append(

                f"{args.case_group}="
                f"{case_n} < "
                f"{args.min_samples_per_group}"
            )


        if (
            total_n
            <
            args.min_samples_per_study
        ):

            reasons.append(

                "comparison_samples="
                f"{total_n} < "
                f"{args.min_samples_per_study}"
            )


        eligible = (
            len(reasons) == 0
        )


        ####################################################
        # Stable safe StudyID
        ####################################################

        study_id = safe_study_id(
            study_value
        )


        if study_id in used_ids:

            raise ValueError(
                "Generated duplicate "
                f"StudyID: {study_id}"
            )


        used_ids.add(
            study_id
        )


        ####################################################
        # Full eligibility report
        ####################################################

        report_row = {

            "StudyID":
                study_id,

            "StudyValue":
                study_value,

            "MatchedSamples":
                matched_n,

            "ReferenceSamples":
                reference_n,

            "CaseSamples":
                case_n,

            "ComparisonSamples":
                total_n,

            "Eligible":
                eligible,

            "Reason":
                (
                    "PASS"
                    if eligible
                    else "; ".join(reasons)
                )
        }


        rows.append(
            report_row
        )


        ####################################################
        # Only eligible studies enter study_map.tsv
        ####################################################

        if eligible:

            eligible_rows.append(
                {
                    "StudyID":
                        study_id,

                    "StudyValue":
                        study_value,

                    "ReferenceSamples":
                        reference_n,

                    "CaseSamples":
                        case_n,

                    "ComparisonSamples":
                        total_n
                }
            )


    ########################################################
    # Write files
    ########################################################

    output = Path(
        args.output
    )

    report = Path(
        args.report
    )


    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    ########################################################
    # Full audit report
    ########################################################

    pd.DataFrame(
        rows
    ).to_csv(
        report,
        sep="\t",
        index=False
    )


    ########################################################
    # Eligible studies only
    ########################################################

    eligible_df = pd.DataFrame(

        eligible_rows,

        columns=[
            "StudyID",
            "StudyValue",
            "ReferenceSamples",
            "CaseSamples",
            "ComparisonSamples"
        ]
    )


    eligible_df.to_csv(
        output,
        sep="\t",
        index=False
    )


    ########################################################
    # Log
    ########################################################

    print(
        f"Studies inspected: {len(rows)}"
    )

    print(
        f"Eligible studies: {len(eligible_rows)}"
    )

    print(
        f"Minimum required: {args.min_studies}"
    )


    for row in rows:

        print(

            f"{row['StudyValue']}: "

            f"eligible={row['Eligible']} "

            f"reference="
            f"{row['ReferenceSamples']} "

            f"case="
            f"{row['CaseSamples']} "

            f"total="
            f"{row['ComparisonSamples']} "

            f"reason={row['Reason']}"
        )


    ########################################################
    # Hard validation of min_studies
    ########################################################

    if (
        len(eligible_rows)
        <
        args.min_studies
    ):

        raise ValueError(

            "Insufficient eligible studies "
            "for meta-analysis: "

            f"{len(eligible_rows)} found, "

            f"{args.min_studies} required. "

            f"See {report} for exclusions."
        )


if __name__ == "__main__":

    main()