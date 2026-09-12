#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


############################################################
# Arguments
############################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Run LEfSe independently within each Study "
            "and build cross-study consensus biomarkers."
        )
    )

    parser.add_argument(
        "--table",
        required=True
    )

    parser.add_argument(
        "--taxonomy",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--outdir",
        required=True
    )

    parser.add_argument(
        "--class-column",
        required=True
    )

    parser.add_argument(
        "--study-column",
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
        "--min-studies",
        type=int,
        required=True
    )

    parser.add_argument(
        "--normalization",
        type=float,
        required=True
    )

    parser.add_argument(
        "--alpha",
        type=float,
        required=True
    )

    parser.add_argument(
        "--lda-threshold",
        type=float,
        required=True
    )

    parser.add_argument(
        "--min-significant-studies",
        type=int,
        required=True
    )

    parser.add_argument(
        "--min-direction-consistency",
        type=float,
        required=True
    )

    return parser.parse_args()


############################################################
# Run command
############################################################

def run_command(command):

    print(
        "Running:",
        " ".join(
            str(x)
            for x in command
        )
    )

    subprocess.run(
        command,
        check=True
    )


############################################################
# Main
############################################################

def main():

    args = parse_args()

    ########################################################
    # Validation
    ########################################################

    if args.min_samples_per_group < 2:
        raise ValueError(
            "min_samples_per_group must be >= 2."
        )

    if args.min_studies < 2:
        raise ValueError(
            "min_studies must be >= 2."
        )

    if args.min_significant_studies < 1:
        raise ValueError(
            "min_significant_studies must be >= 1."
        )

    if not (
        0.0 <=
        args.min_direction_consistency <=
        1.0
    ):
        raise ValueError(
            "min_direction_consistency must be between 0 and 1."
        )

    ########################################################
    # Paths
    ########################################################

    outdir = Path(
        args.outdir
    )

    by_study_dir = (
        outdir /
        "by_study"
    )

    per_study_dir = (
        outdir /
        "per_study"
    )

    consensus_dir = (
        outdir /
        "consensus"
    )

    by_study_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    per_study_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    consensus_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    ########################################################
    # Locate existing project scripts
    ########################################################

    project_root = (
        Path(__file__)
        .resolve()
        .parents[2]
    )

    prepare_script = (
        project_root /
        "scripts/python/prepare_lefse_input.py"
    )

    parse_script = (
        project_root /
        "scripts/python/parse_lefse_results.py"
    )

    if not prepare_script.exists():
        raise FileNotFoundError(
            prepare_script
        )

    if not parse_script.exists():
        raise FileNotFoundError(
            parse_script
        )

    format_executable = shutil.which(
        "lefse_format_input.py"
    )

    run_executable = shutil.which(
        "lefse_run.py"
    )

    if format_executable is None:
        raise RuntimeError(
            "lefse_format_input.py not found."
        )

    if run_executable is None:
        raise RuntimeError(
            "lefse_run.py not found."
        )

    ########################################################
    # Read metadata
    ########################################################

    metadata = pd.read_csv(
        args.metadata,
        sep="\t",
        dtype=str
    )

    if "SampleID" in metadata.columns:
        sample_column = "SampleID"
    else:
        sample_column = metadata.columns[0]

    required_columns = [
        sample_column,
        args.study_column,
        args.class_column
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in metadata.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing metadata columns: "
            + ", ".join(
                missing_columns
            )
        )

    for column in required_columns:

        metadata[column] = (
            metadata[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    if metadata[
        sample_column
    ].duplicated().any():

        duplicates = (
            metadata.loc[
                metadata[
                    sample_column
                ].duplicated(),
                sample_column
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            "Duplicate SampleID values: "
            + ", ".join(
                duplicates[:20]
            )
        )

    ########################################################
    # Restrict to relevant groups
    ########################################################

    metadata = metadata[
        (
            metadata[
                args.study_column
            ] != ""
        )
        &
        (
            metadata[
                args.class_column
            ].isin(
                [
                    args.reference_group,
                    args.case_group
                ]
            )
        )
    ].copy()

    if metadata.empty:
        raise ValueError(
            "No usable metadata rows remain."
        )

    ########################################################
    # Study eligibility
    ########################################################

    eligibility_rows = []

    study_names = sorted(
        metadata[
            args.study_column
        ].unique()
    )

    for study in study_names:

        study_metadata = metadata[
            metadata[
                args.study_column
            ] == study
        ]

        n_reference = int(
            (
                study_metadata[
                    args.class_column
                ]
                ==
                args.reference_group
            ).sum()
        )

        n_case = int(
            (
                study_metadata[
                    args.class_column
                ]
                ==
                args.case_group
            ).sum()
        )

        eligible = (
            n_reference >=
            args.min_samples_per_group
            and
            n_case >=
            args.min_samples_per_group
        )

        if eligible:

            reason = "Eligible"

        elif (
            n_reference <
            args.min_samples_per_group
            and
            n_case <
            args.min_samples_per_group
        ):

            reason = (
                "Insufficient samples "
                "in both groups"
            )

        elif (
            n_reference <
            args.min_samples_per_group
        ):

            reason = (
                f"Insufficient "
                f"{args.reference_group} samples"
            )

        else:

            reason = (
                f"Insufficient "
                f"{args.case_group} samples"
            )

        eligibility_rows.append(
            {
                "Study": study,
                "N_Reference": n_reference,
                "N_Case": n_case,
                "Eligible": eligible,
                "Reason": reason
            }
        )

    eligibility = pd.DataFrame(
        eligibility_rows
    )

    eligibility.to_csv(
        per_study_dir /
        "study_eligibility.tsv",
        sep="\t",
        index=False
    )

    eligible_studies = (
        eligibility.loc[
            eligibility["Eligible"],
            "Study"
        ]
        .astype(str)
        .tolist()
    )

    if (
        len(eligible_studies) <
        args.min_studies
    ):

        raise RuntimeError(
            f"Only {len(eligible_studies)} "
            f"eligible studies; "
            f"{args.min_studies} required."
        )

    ########################################################
    # Taxonomy map
    ########################################################

    taxonomy = pd.read_csv(
        args.taxonomy,
        sep="\t",
        dtype=str
    )

    feature_column = (
        "Feature ID"
        if "Feature ID" in taxonomy.columns
        else taxonomy.columns[0]
    )

    taxon_column = (
        "Taxon"
        if "Taxon" in taxonomy.columns
        else taxonomy.columns[1]
    )

    taxonomy_map = dict(
        zip(
            taxonomy[feature_column].astype(str),
            taxonomy[taxon_column].astype(str)
        )
    )

    ########################################################
    # Run LEfSe per Study
    ########################################################

    combined_results = []

    directory_map = []

    for index, study in enumerate(
        eligible_studies,
        start=1
    ):

        study_id = (
            f"study_{index:03d}"
        )

        study_dir = (
            by_study_dir /
            study_id
        )

        study_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        directory_map.append(
            {
                "Study": study,
                "Directory": study_id
            }
        )

        print()
        print(
            "=" * 70
        )
        print(
            "LEfSe Study:",
            study
        )
        print(
            "=" * 70
        )

        ####################################################
        # Study-specific metadata
        ####################################################

        study_metadata = metadata[
            metadata[
                args.study_column
            ] == study
        ].copy()

        metadata_file = (
            study_dir /
            "metadata.tsv"
        )

        study_metadata.to_csv(
            metadata_file,
            sep="\t",
            index=False
        )

        ####################################################
        # Paths
        ####################################################

        lefse_table = (
            study_dir /
            "lefse_input.tsv"
        )

        lefse_input = (
            study_dir /
            "lefse_input.in"
        )

        abundance = (
            study_dir /
            "feature_abundance.tsv"
        )

        mapping = (
            study_dir /
            "feature_mapping.tsv"
        )

        raw_results = (
            study_dir /
            "lefse_results.res"
        )

        significant = (
            study_dir /
            "significant_taxa.tsv"
        )

        ####################################################
        # Prepare input
        ####################################################

        run_command(
            [
                sys.executable,
                str(
                    prepare_script
                ),
                "--table",
                args.table,
                "--metadata",
                str(
                    metadata_file
                ),
                "--class-column",
                args.class_column,
                "--lefse-table",
                str(
                    lefse_table
                ),
                "--abundance",
                str(
                    abundance
                ),
                "--mapping",
                str(
                    mapping
                )
            ]
        )

        ####################################################
        # Format LEfSe input
        ####################################################

        run_command(
            [
                format_executable,
                str(
                    lefse_table
                ),
                str(
                    lefse_input
                ),
                "-c",
                "1",
                "-o",
                str(
                    args.normalization
                )
            ]
        )

        ####################################################
        # Run LEfSe
        ####################################################

        run_command(
            [
                run_executable,
                str(
                    lefse_input
                ),
                str(
                    raw_results
                ),
                "-a",
                str(
                    args.alpha
                ),
                "-w",
                str(
                    args.alpha
                ),
                "-l",
                str(
                    args.lda_threshold
                )
            ]
        )

        ####################################################
        # Parse results
        ####################################################

        run_command(
            [
                sys.executable,
                str(
                    parse_script
                ),
                "--results",
                str(
                    raw_results
                ),
                "--mapping",
                str(
                    mapping
                ),
                "--taxonomy",
                args.taxonomy,
                "--output",
                str(
                    significant
                )
            ]
        )

        ####################################################
        # Collect significant taxa
        ####################################################

        study_results = pd.read_csv(
            significant,
            sep="\t"
        )

        if study_results.empty:
            continue

        study_results[
            "Study"
        ] = study

        study_results[
            "StudyDirectory"
        ] = study_id

        combined_results.append(
            study_results
        )

    ########################################################
    # Save Study-directory map
    ########################################################

    pd.DataFrame(
        directory_map
    ).to_csv(
        per_study_dir /
        "study_directory_map.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Combined per-Study significant results
    ########################################################

    combined_columns = [
        "FeatureID",
        "Taxon",
        "LDA",
        "Group",
        "Log10Mean",
        "Wilcoxon",
        "Study",
        "StudyDirectory"
    ]

    if combined_results:

        combined = pd.concat(
            combined_results,
            ignore_index=True
        )

    else:

        combined = pd.DataFrame(
            columns=combined_columns
        )

    combined.to_csv(
        per_study_dir /
        "all_significant_taxa.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Build consensus
    ########################################################

    consensus_columns = [
        "FeatureID",
        "Taxon",
        "Significant_Studies",
        "Eligible_Studies",
        "Selection_Frequency",
        "Case_Studies",
        "Reference_Studies",
        "Direction_Consistency",
        "Consensus_Group",
        "Median_LDA",
        "Mean_LDA",
        "Min_LDA",
        "Max_LDA",
        "Studies",
        "Consensus",
        "LDA",
        "Group"
    ]

    consensus_rows = []

    if not combined.empty:

        for feature_id, feature_data in (
            combined.groupby(
                "FeatureID",
                sort=False
            )
        ):

            feature_data = (
                feature_data
                .drop_duplicates(
                    subset=[
                        "Study",
                        "FeatureID"
                    ]
                )
            )

            significant_studies = int(
                feature_data[
                    "Study"
                ].nunique()
            )

            case_studies = int(
                feature_data.loc[
                    feature_data[
                        "Group"
                    ]
                    ==
                    args.case_group,
                    "Study"
                ].nunique()
            )

            reference_studies = int(
                feature_data.loc[
                    feature_data[
                        "Group"
                    ]
                    ==
                    args.reference_group,
                    "Study"
                ].nunique()
            )

            if significant_studies > 0:

                direction_consistency = (
                    max(
                        case_studies,
                        reference_studies
                    )
                    /
                    significant_studies
                )

            else:

                direction_consistency = (
                    np.nan
                )

            if (
                case_studies >
                reference_studies
            ):

                consensus_group = (
                    args.case_group
                )

            elif (
                reference_studies >
                case_studies
            ):

                consensus_group = (
                    args.reference_group
                )

            else:

                consensus_group = "TIE"

            lda_values = pd.to_numeric(
                feature_data["LDA"],
                errors="coerce"
            )

            median_lda = float(
                lda_values.median()
            )

            consensus_flag = (
                significant_studies >=
                args.min_significant_studies
                and
                direction_consistency >=
                args.min_direction_consistency
                and
                consensus_group != "TIE"
            )

            taxon = taxonomy_map.get(
                str(
                    feature_id
                ),
                str(
                    feature_id
                )
            )

            study_list = ";".join(
                sorted(
                    feature_data[
                        "Study"
                    ].astype(str).unique()
                )
            )

            consensus_rows.append(
                {
                    "FeatureID":
                        feature_id,

                    "Taxon":
                        taxon,

                    "Significant_Studies":
                        significant_studies,

                    "Eligible_Studies":
                        len(
                            eligible_studies
                        ),

                    "Selection_Frequency":
                        significant_studies
                        /
                        len(
                            eligible_studies
                        ),

                    "Case_Studies":
                        case_studies,

                    "Reference_Studies":
                        reference_studies,

                    "Direction_Consistency":
                        direction_consistency,

                    "Consensus_Group":
                        consensus_group,

                    "Median_LDA":
                        median_lda,

                    "Mean_LDA":
                        float(
                            lda_values.mean()
                        ),

                    "Min_LDA":
                        float(
                            lda_values.min()
                        ),

                    "Max_LDA":
                        float(
                            lda_values.max()
                        ),

                    "Studies":
                        study_list,

                    "Consensus":
                        consensus_flag,

                    # Compatibility columns
                    # for later visualization.
                    "LDA":
                        median_lda,

                    "Group":
                        consensus_group
                }
            )

    consensus_all = pd.DataFrame(
        consensus_rows,
        columns=consensus_columns
    )

    if not consensus_all.empty:

        consensus_all = (
            consensus_all
            .sort_values(
                [
                    "Consensus",
                    "Significant_Studies",
                    "Direction_Consistency",
                    "Median_LDA"
                ],
                ascending=[
                    False,
                    False,
                    False,
                    False
                ]
            )
        )

    consensus_all.to_csv(
        consensus_dir /
        "consensus_all.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Primary consensus biomarkers
    ########################################################

    if consensus_all.empty:

        consensus = pd.DataFrame(
            columns=consensus_columns
        )

    else:

        consensus = (
            consensus_all[
                consensus_all[
                    "Consensus"
                ]
            ]
            .copy()
        )

    consensus.to_csv(
        consensus_dir /
        "consensus_taxa.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Summary
    ########################################################

    summary = pd.DataFrame(
        [
            {
                "Eligible_Studies":
                    len(
                        eligible_studies
                    ),

                "Total_Per_Study_Significant_Hits":
                    len(
                        combined
                    ),

                "Unique_Significant_Features":
                    (
                        combined[
                            "FeatureID"
                        ].nunique()
                        if not combined.empty
                        else 0
                    ),

                "Consensus_Features":
                    len(
                        consensus
                    ),

                "Min_Significant_Studies":
                    args.min_significant_studies,

                "Min_Direction_Consistency":
                    args.min_direction_consistency,

                "Reference_Group":
                    args.reference_group,

                "Case_Group":
                    args.case_group,

                "Alpha":
                    args.alpha,

                "LDA_Threshold":
                    args.lda_threshold
            }
        ]
    )

    summary.to_csv(
        consensus_dir /
        "consensus_summary.tsv",
        sep="\t",
        index=False
    )

    print()
    print(
        "LEfSe per-Study analysis completed."
    )

    print(
        "Eligible studies:",
        len(
            eligible_studies
        )
    )

    print(
        "Consensus features:",
        len(
            consensus
        )
    )


if __name__ == "__main__":
    main()