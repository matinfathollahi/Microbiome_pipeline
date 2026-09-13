#!/usr/bin/env python3

import argparse
import json
import re
import sys
import zipfile

from pathlib import Path

import pandas as pd
import yaml


############################################################
# Arguments
############################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description="Validate project before pipeline execution."
    )

    parser.add_argument(
        "--config",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--accessions",
        required=True
    )

    parser.add_argument(
        "--classifier",
        required=True
    )

    parser.add_argument(
        "--json-output",
        required=True
    )

    parser.add_argument(
        "--tsv-output",
        required=True
    )

    return parser.parse_args()


############################################################
# Check collector
############################################################

CHECKS = []


def add_check(
    name,
    passed,
    message,
    severity="ERROR"
):

    CHECKS.append(
        {
            "Check": name,
            "Passed": bool(passed),
            "Severity": severity,
            "Message": str(message)
        }
    )


############################################################
# Load YAML
############################################################

def load_config(path):

    path = Path(path)

    if not path.is_file():

        raise FileNotFoundError(
            f"Config file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as handle:

        config = yaml.safe_load(
            handle
        )

    if not isinstance(
        config,
        dict
    ):

        raise ValueError(
            "Config YAML does not contain "
            "a valid dictionary."
        )

    return config


############################################################
# Table reader
############################################################

def read_table(path):

    path = Path(path)

    if not path.is_file():

        raise FileNotFoundError(
            f"File not found: {path}"
        )

    if path.stat().st_size == 0:

        raise ValueError(
            f"File is empty: {path}"
        )

    return pd.read_csv(
        path,
        sep="\t",
        dtype=str
    )


############################################################
# Main
############################################################

def main():

    args = parse_args()

    errors = []

    config = None
    metadata = None
    accessions = None

    # Safe default used even if config parsing fails
    sample_column = "SampleID"

    ########################################################
    # CONFIG
    ########################################################

    try:

        config = load_config(
            args.config
        )

        add_check(
            "config_yaml",
            True,
            "Config YAML parsed successfully."
        )

    except Exception as exc:

        add_check(
            "config_yaml",
            False,
            exc
        )

        errors.append(
            str(exc)
        )


    ########################################################
    # METADATA FILE
    ########################################################

    try:

        metadata = read_table(
            args.metadata
        )

        metadata.columns = [
            str(x).strip()
            for x in metadata.columns
        ]

        add_check(
            "metadata_file",
            True,
            f"{len(metadata)} metadata rows found."
        )

    except Exception as exc:

        add_check(
            "metadata_file",
            False,
            exc
        )

        errors.append(
            str(exc)
        )


    ########################################################
    # ACCESSIONS FILE
    ########################################################

    try:

        accessions = read_table(
            args.accessions
        )

        accessions.columns = [
            str(x).strip()
            for x in accessions.columns
        ]

        add_check(
            "accessions_file",
            True,
            f"{len(accessions)} accession rows found."
        )

    except Exception as exc:

        add_check(
            "accessions_file",
            False,
            exc
        )

        errors.append(
            str(exc)
        )


    ########################################################
    # SILVA CLASSIFIER
    ########################################################

    classifier = Path(
        args.classifier
    )

    classifier_ok = (
        classifier.is_file()
        and classifier.stat().st_size > 0
    )

    add_check(
        "classifier_exists",
        classifier_ok,
        (
            f"Classifier found: {classifier}"
            if classifier_ok
            else f"Classifier missing/empty: {classifier}"
        )
    )

    if not classifier_ok:

        errors.append(
            "Classifier missing or empty."
        )

    else:

        qza_zip = zipfile.is_zipfile(
            classifier
        )

        add_check(
            "classifier_qza_zip",
            qza_zip,
            (
                "Classifier appears to be a valid QIIME artifact archive."
                if qza_zip
                else "Classifier is not a valid ZIP/QZA archive."
            )
        )

        if not qza_zip:

            errors.append(
                "Classifier is not a valid QZA archive."
            )

        else:

            with zipfile.ZipFile(
                classifier,
                "r"
            ) as archive:

                names = archive.namelist()

            has_metadata = any(
                name.endswith(
                    "/metadata.yaml"
                )
                for name in names
            )

            has_version = any(
                name.endswith(
                    "/VERSION"
                )
                for name in names
            )

            internal_ok = (
                has_metadata
                and has_version
            )

            add_check(
                "classifier_structure",
                internal_ok,
                (
                    "QIIME artifact internal structure detected."
                    if internal_ok
                    else
                    "QIIME artifact metadata/VERSION missing."
                )
            )

            if not internal_ok:

                errors.append(
                    "Classifier QZA internal structure invalid."
                )


    ########################################################
    # Stop detailed config checks if basic files unavailable
    ########################################################

    if (
        config is not None
        and metadata is not None
    ):

        ####################################################
        # Determine column names from config
        ####################################################

        meta_cfg = config.get(
            "meta_analysis",
            {}
        )

        meta_enabled = bool(
            meta_cfg.get(
                "enabled",
                True
            )
        )


        batch_cfg = config.get(
            "batch_correction",
            {}
        )

        confounding_cfg = config.get(
            "confounding",
            {}
        )

        ml_cfg = config.get(
            "machine_learning",
            {}
        )

        sample_column = meta_cfg.get(
            "sample_column",
            "SampleID"
        )

        study_column = meta_cfg.get(
            "study_column",
            "Study"
        )

        group_column = meta_cfg.get(
            "group_column",
            "Group"
        )

        batch_column = batch_cfg.get(
            "batch_variable",
            "Batch"
        )

        confounding_batch_column = confounding_cfg.get(
            "batch",
            None
        )

        ml_label = ml_cfg.get(
            "label",
            group_column
        )


        ####################################################
        # Required metadata columns
        ####################################################

        required_columns = {
            sample_column,
            study_column,
            group_column,
            ml_label
        }

        if confounding_batch_column:

            required_columns.add(
                confounding_batch_column
            )


        batch_enabled = bool(
            batch_cfg.get(
                "enabled",
                False
            )
        )


        if batch_enabled:

            required_columns.add(
                batch_column
            )


        missing_columns = sorted(

            required_columns

            - set(
                metadata.columns
            )
        )


        columns_ok = (
            len(
                missing_columns
            )
            == 0
        )


        add_check(
            "required_metadata_columns",
            columns_ok,
            (
                "All required metadata columns exist."
                if columns_ok
                else
                "Missing columns: "
                + ", ".join(
                    missing_columns
                )
            )
        )


        if not columns_ok:

            errors.append(
                "Required metadata columns missing."
            )


        ####################################################
        # SampleID
        ####################################################

        if sample_column in metadata.columns:

            sample_ids = (
                metadata[
                    sample_column
                ]
                .fillna("")
                .astype(str)
                .str.strip()
            )

            blank_samples = (
                sample_ids.eq("")
            ).any()

            add_check(
                "sample_id_nonempty",
                not blank_samples,
                (
                    "All SampleID values are non-empty."
                    if not blank_samples
                    else "Blank SampleID values detected."
                )
            )

            if blank_samples:

                errors.append(
                    "Blank SampleID values."
                )


            duplicates = (
                sample_ids
                .duplicated()
                .sum()
            )

            add_check(
                "sample_id_unique",
                duplicates == 0,
                (
                    "SampleID values are unique."
                    if duplicates == 0
                    else
                    f"{duplicates} duplicated SampleID values found."
                )
            )

            if duplicates:

                errors.append(
                    "Duplicate SampleID values."
                )


        ####################################################
        # ML label
        ####################################################

        if ml_label in metadata.columns:

            label_values = (

                metadata[
                    ml_label
                ]
                .dropna()
                .astype(str)
                .str.strip()
            )

            n_classes = (
                label_values
                .nunique()
            )

            add_check(
                "ml_label_classes",
                n_classes >= 2,
                (
                    f"{n_classes} classes found "
                    f"in ML label '{ml_label}'."
                )
            )

            if n_classes < 2:

                errors.append(
                    "ML label has fewer than two classes."
                )


        ####################################################
        # Batch levels
        ####################################################

        if batch_column in metadata.columns:

            batch_levels = (

                metadata[
                    batch_column
                ]
                .dropna()
                .astype(str)
                .nunique()
            )





            if batch_enabled:

                add_check(
                    "batch_levels",
                    batch_levels >= 2,
                    (
                        f"{batch_levels} batch levels found."
                    )
                )

                if batch_levels < 2:

                    errors.append(
                        "Batch correction enabled but "
                        "fewer than 2 batch levels found."
                    )

            else:

                add_check(
                    "batch_correction_enabled",
                    True,
                    (
                        "Batch correction is disabled in config."
                    ),
                    severity="WARNING"
                )


        ####################################################
        # Batch method
        ####################################################

        if batch_cfg.get(
            "enabled",
            False
        ):

            method = str(

                batch_cfg.get(
                    "method",
                    ""
                )

            ).lower()


            valid_method = (
                method in
                {
                    "combat",
                    "mmuphin"
                }
            )


            add_check(
                "batch_method",
                valid_method,
                f"Configured batch method: {method}"
            )


            if not valid_method:

                errors.append(
                    "Unsupported batch correction method."
                )

















        ####################################################
        # Meta-analysis validation
        ####################################################

        if meta_enabled:

            reference_group = meta_cfg.get(
                "reference_group"
            )

            case_group = meta_cfg.get(
                "case_group"
            )

            meta_method = meta_cfg.get(
                "method",
                "DESeq2"
            )

            supported_meta_methods = {
                "DESeq2"
            }

            meta_method_ok = (
                meta_method in supported_meta_methods
            )

            add_check(
                "meta_analysis_method_supported",
                meta_method_ok,
                (
                    f"meta_analysis.method = {meta_method}"
                    if meta_method_ok
                    else
                    f"meta_analysis.method = '{meta_method}' is not "
                    "implemented. Supported methods: "
                    + ", ".join(sorted(supported_meta_methods))
                )
            )

            if not meta_method_ok:

                errors.append(
                    f"meta_analysis.method '{meta_method}' is not "
                    "implemented in this pipeline."
                )


            ################################################
            # Validate configured groups
            ################################################

            reference_configured = (
                reference_group is not None
                and
                str(reference_group).strip() != ""
            )

            case_configured = (
                case_group is not None
                and
                str(case_group).strip() != ""
            )


            add_check(
                "meta_reference_group_configured",
                reference_configured,
                (
                    f"reference_group = {reference_group}"
                    if reference_configured
                    else
                    "meta_analysis.reference_group is missing."
                )
            )

            if not reference_configured:

                errors.append(
                    "meta_analysis.reference_group is required."
                )


            add_check(
                "meta_case_group_configured",
                case_configured,
                (
                    f"case_group = {case_group}"
                    if case_configured
                    else
                    "meta_analysis.case_group is missing."
                )
            )

            if not case_configured:

                errors.append(
                    "meta_analysis.case_group is required."
                )


            ################################################
            # Meta-analysis case/reference groups
            ################################################

            if (
                group_column in metadata.columns
                and
                reference_configured
                and
                case_configured
            ):

                group_values = set(
                    metadata[
                        group_column
                    ]
                    .dropna()
                    .astype(str)
                    .str.strip()
                )


                reference_ok = (
                    str(reference_group)
                    in group_values
                )

                add_check(
                    "meta_reference_group",
                    reference_ok,
                    (
                        f"Reference group '{reference_group}' found."
                        if reference_ok
                        else
                        f"Reference group '{reference_group}' "
                        "not found in metadata."
                    )
                )

                if not reference_ok:

                    errors.append(
                        "Meta-analysis reference group missing."
                    )


                case_ok = (
                    str(case_group)
                    in group_values
                )

                add_check(
                    "meta_case_group",
                    case_ok,
                    (
                        f"Case group '{case_group}' found."
                        if case_ok
                        else
                        f"Case group '{case_group}' "
                        "not found in metadata."
                    )
                )

                if not case_ok:

                    errors.append(
                        "Meta-analysis case group missing."
                    )


                distinct = (
                    str(reference_group)
                    !=
                    str(case_group)
                )

                add_check(
                    "meta_group_direction",
                    distinct,
                    f"Contrast: {case_group} vs {reference_group}"
                )

                if not distinct:

                    errors.append(
                        "Case and reference groups are identical."
                    )


            ################################################
            # Dynamic study eligibility thresholds
            ################################################

            min_studies = int(
                meta_cfg.get(
                    "min_studies",
                    2
                )
            )

            min_samples_per_group = int(
                meta_cfg.get(
                    "min_samples_per_group",
                    2
                )
            )

            min_samples_per_study = int(
                meta_cfg.get(
                    "min_samples_per_study",
                    4
                )
            )


            min_studies_ok = (
                min_studies >= 2
            )

            add_check(
                "meta_min_studies_config",
                min_studies_ok,
                f"min_studies = {min_studies}"
            )

            if not min_studies_ok:

                errors.append(
                    "meta_analysis.min_studies must be >= 2."
                )


            min_group_ok = (
                min_samples_per_group >= 1
            )

            add_check(
                "meta_min_samples_per_group",
                min_group_ok,
                (
                    "min_samples_per_group = "
                    f"{min_samples_per_group}"
                )
            )

            if not min_group_ok:

                errors.append(
                    "meta_analysis.min_samples_per_group "
                    "must be >= 1."
                )


            min_study_ok = (
                min_samples_per_study
                >=
                2 * min_samples_per_group
            )

            add_check(
                "meta_min_samples_per_study",
                min_study_ok,
                (
                    "min_samples_per_study = "
                    f"{min_samples_per_study}; "
                    "2 * min_samples_per_group = "
                    f"{2 * min_samples_per_group}"
                )
            )

            if not min_study_ok:

                errors.append(
                    "meta_analysis.min_samples_per_study "
                    "must be at least "
                    "2 * min_samples_per_group."
                )


            ################################################
            # Count metadata-level eligible studies
            ################################################

            eligibility_columns_ok = all(
                column in metadata.columns
                for column in [
                    sample_column,
                    study_column,
                    group_column
                ]
            )


            if (
                eligibility_columns_ok
                and
                reference_configured
                and
                case_configured
                and
                min_studies_ok
                and
                min_group_ok
                and
                min_study_ok
            ):

                eligibility = metadata[
                    [
                        sample_column,
                        study_column,
                        group_column
                    ]
                ].copy()


                for column in [
                    sample_column,
                    study_column,
                    group_column
                ]:

                    eligibility[column] = (
                        eligibility[column]
                        .fillna("")
                        .astype(str)
                        .str.strip()
                    )


                eligibility = eligibility.loc[
                    (eligibility[sample_column] != "")
                    &
                    (eligibility[study_column] != "")
                    &
                    (eligibility[group_column] != "")
                ].copy()


                eligibility = eligibility.loc[
                    eligibility[
                        group_column
                    ].isin(
                        [
                            str(reference_group),
                            str(case_group)
                        ]
                    )
                ].copy()


                study_counts = (
                    eligibility
                    .groupby(
                        [
                            study_column,
                            group_column
                        ]
                    )[sample_column]
                    .nunique()
                    .unstack(
                        fill_value=0
                    )
                )


                reference_counts = (
                    study_counts[
                        str(reference_group)
                    ]
                    if str(reference_group)
                    in study_counts.columns
                    else
                    pd.Series(
                        0,
                        index=study_counts.index,
                        dtype=int
                    )
                )


                case_counts = (
                    study_counts[
                        str(case_group)
                    ]
                    if str(case_group)
                    in study_counts.columns
                    else
                    pd.Series(
                        0,
                        index=study_counts.index,
                        dtype=int
                    )
                )


                total_counts = (
                    reference_counts
                    +
                    case_counts
                )


                eligible_mask = (
                    (
                        reference_counts
                        >=
                        min_samples_per_group
                    )
                    &
                    (
                        case_counts
                        >=
                        min_samples_per_group
                    )
                    &
                    (
                        total_counts
                        >=
                        min_samples_per_study
                    )
                )


                eligible_studies = (
                    study_counts.index[
                        eligible_mask
                    ]
                    .astype(str)
                    .tolist()
                )


                eligible_count = len(
                    eligible_studies
                )

                enough_studies = (
                    eligible_count
                    >=
                    min_studies
                )


                add_check(
                    "meta_eligible_studies_metadata",
                    enough_studies,
                    (
                        f"{eligible_count} metadata-level "
                        "eligible studies found; "
                        f"minimum required = {min_studies}. "
                        "Eligible: "
                        +
                        (
                            ", ".join(
                                eligible_studies
                            )
                            if eligible_studies
                            else "none"
                        )
                    )
                )


                if not enough_studies:

                    errors.append(
                        "Insufficient metadata-level "
                        "eligible studies for meta-analysis: "
                        f"{eligible_count} < "
                        f"{min_studies}."
                    )


        else:

            add_check(
                "meta_analysis_enabled",
                True,
                "Meta-analysis is disabled in config.",
                severity="WARNING"
            )
        ####################################################
        # Filtering config
        ####################################################

        filtering = config.get(
            "filtering",
            {}
        )

        min_count = filtering.get(
            "min_count"
        )

        prevalence = filtering.get(
            "prevalence"
        )


        if min_count is not None:

            min_count_ok = (
                float(min_count) >= 0
            )

            add_check(
                "filter_min_count",
                min_count_ok,
                f"min_count = {min_count}"
            )

            if not min_count_ok:

                errors.append(
                    "filtering.min_count must be >= 0."
                )


        if prevalence is not None:

            prevalence_value = float(
                prevalence
            )

            prevalence_ok = (
                0
                <
                prevalence_value
                <=
                1
            )

            add_check(
                "filter_prevalence",
                prevalence_ok,
                f"prevalence = {prevalence}"
            )

            if not prevalence_ok:

                errors.append(
                    "filtering.prevalence must be in (0,1]."
                )


        ####################################################
        # Predictive preprocessing
        ####################################################

        predictive_cfg = ml_cfg.get(
            "predictive_preprocessing",
            {}
        )

        zero_fraction = predictive_cfg.get(
            "zero_fraction",
            0.5
        )

        zero_ok = (
            0
            <
            float(zero_fraction)
            <
            1
        )

        add_check(
            "predictive_zero_fraction",
            zero_ok,
            f"zero_fraction = {zero_fraction}"
        )

        if not zero_ok:

            errors.append(
                "zero_fraction must be between 0 and 1."
            )


        ####################################################
        # Deep Learning folds
        ####################################################

        dl_cfg = config.get(
            "deep_learning",
            {}
        )

        inner_folds = int(
            dl_cfg.get(
                "inner_folds",
                5
            )
        )

        dl_group_column = dl_cfg.get(
            "group_column",
            "Study"
        )

        folds_ok = (
            inner_folds >= 2
        )

        add_check(
            "deep_learning_folds",
            folds_ok,
            (
                "outer_folds=dynamic_by_study, "
                f"inner_folds={inner_folds}, "
                f"group_column={dl_group_column}"
            )
        )

        if not folds_ok:

            errors.append(
                "DL inner_folds must be >= 2."
            )

    ########################################################
    # ACCESSION VALIDATION
    ########################################################

    if accessions is not None:

        ####################################################
        # Strict accessions.tsv schema
        ####################################################

        required_accession_columns = {
            "SampleID",
            "accession",
            "DenoiseBatch",
            "AmpliconRegion",
            "PrimerSet"
        }


        missing_accession_columns = (
            required_accession_columns
            -
            set(accessions.columns)
        )


        schema_ok = (
            len(missing_accession_columns) == 0
        )


        add_check(
            "accessions_schema",
            schema_ok,
            (
                "Required columns found: "
                "SampleID, accession, DenoiseBatch."
                "AmpliconRegion, PrimerSet."
                if schema_ok
                else
                "metadata/accessions.tsv is missing required "
                "columns: "
                + ", ".join(
                    sorted(missing_accession_columns)
                )
            )
        )


        if not schema_ok:

            errors.append(
                "Invalid accessions.tsv schema."
            )


        ####################################################
        # Continue detailed validation only if schema valid
        ####################################################

        if schema_ok:

            ################################################
            # Normalize required columns
            ################################################

            for column in [
                "SampleID",
                "accession",
                "DenoiseBatch",
                "AmpliconRegion",
                "PrimerSet"
            ]:

                accessions[column] = (
                    accessions[column]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )


            ################################################
            # Missing / blank values
            ################################################

            for column in [
                "SampleID",
                "accession",
                "DenoiseBatch",
                "AmpliconRegion",
                "PrimerSet"
            ]:

                blank_count = (
                    accessions[column]
                    .eq("")
                    .sum()
                )


                column_ok = (
                    blank_count == 0
                )


                add_check(
                    f"accessions_{column}_nonempty",
                    column_ok,
                    (
                        f"All {column} values are non-empty."
                        if column_ok
                        else
                        f"{blank_count} blank/missing "
                        f"{column} values found."
                    )
                )


                if not column_ok:

                    errors.append(
                        f"Blank/missing values in "
                        f"accessions.tsv column '{column}'."
                    )


            ################################################
            # SampleID uniqueness
            ################################################

            duplicated_sample_ids = (
                accessions[
                    "SampleID"
                ]
                .duplicated()
                .sum()
            )


            add_check(
                "accession_sampleid_unique",
                duplicated_sample_ids == 0,
                (
                    "All accessions.tsv SampleID values are unique."
                    if duplicated_sample_ids == 0
                    else
                    f"{duplicated_sample_ids} duplicated "
                    "SampleID values found in accessions.tsv."
                )
            )


            if duplicated_sample_ids:

                errors.append(
                    "Duplicated SampleID values in accessions.tsv."
                )


            ################################################
            # Accession uniqueness
            ################################################

            accession_values = (
                accessions[
                    "accession"
                ]
            )


            duplicated_accessions = (
                accession_values
                .duplicated()
                .sum()
            )


            add_check(
                "accession_unique",
                duplicated_accessions == 0,
                (
                    "All accession values are unique."
                    if duplicated_accessions == 0
                    else
                    f"{duplicated_accessions} duplicated "
                    "SRA accession values found."
                )
            )


            if duplicated_accessions:

                errors.append(
                    "Duplicated SRA accession values."
                )


            ################################################
            # SRA accession format
            ################################################

            sra_pattern = re.compile(
                r"^(SRR|ERR|DRR)\d+$",
                re.IGNORECASE
            )


            valid_format = accession_values.map(
                lambda value:
                    bool(
                        sra_pattern.fullmatch(
                            value
                        )
                    )
            )


            recognized = int(
                valid_format.sum()
            )


            invalid_count = (
                len(accession_values)
                -
                recognized
            )


            format_ok = (
                invalid_count == 0
            )








            add_check(
                "sra_accession_format",
                format_ok,
                (
                    f"All {recognized} accessions use "
                    "standard SRR/ERR/DRR format."
                    if format_ok
                    else
                    f"{invalid_count}/{len(accession_values)} "
                    "accessions do not use standard "
                    "SRR/ERR/DRR format."
                )
            )







            if not format_ok:

                invalid_examples = (
                    accession_values[
                        ~valid_format
                    ]
                    .head(10)
                    .tolist()
                )

                errors.append(
                    "Invalid SRA accession format: "
                    + ", ".join(
                        invalid_examples
                    )
                )


            ################################################
            # DenoiseBatch validation
            ################################################

            denoise_batches = (
                accessions[
                    "DenoiseBatch"
                ]
                .dropna()
                .astype(str)
                .str.strip()
            )


            n_denoise_batches = (
                denoise_batches
                .nunique()
            )


            add_check(
                "denoise_batches",
                n_denoise_batches >= 1,
                (
                    f"{n_denoise_batches} DenoiseBatch "
                    "level(s) found."
                )
            )


            if n_denoise_batches < 1:

                errors.append(
                    "No valid DenoiseBatch values found."
                )


################################################
# Amplicon compatibility validation
################################################

            accessions["AmpliconRegion"] = (
                accessions["AmpliconRegion"]
                .str.strip()
                .str.upper()
            )

            accessions["PrimerSet"] = (
                accessions["PrimerSet"]
                .str.strip()
                .str.upper()
            )

            amplicon_pairs = (
                accessions[
                    [
                        "AmpliconRegion",
                        "PrimerSet"
                    ]
                ]
                .drop_duplicates()
            )
            n_amplicon_pairs = len(
                amplicon_pairs
            )


            amplicon_compatible = (
                n_amplicon_pairs == 1
            )


            add_check(
                "amplicon_compatibility",
                amplicon_compatible,
                (
                    "All samples use the same AmpliconRegion "
                    "and PrimerSet."
                    if amplicon_compatible
                    else
                    (
                        "Multiple AmpliconRegion/PrimerSet "
                        "combinations detected: "
                        +
                        "; ".join(
                            f"{row.AmpliconRegion}/{row.PrimerSet}"
                            for row
                            in amplicon_pairs.itertuples(
                                index=False
                            )
                        )
                    )
                )
            )


            if not amplicon_compatible:

                errors.append(
                    "ASV-level cross-study merge is unsafe because "
                    "multiple AmpliconRegion/PrimerSet combinations "
                    "were detected."
                )



            ################################################
            # Accessions SampleID vs metadata
            ################################################

            if (
                metadata is not None
                and
                sample_column in metadata.columns
            ):

                accession_samples = set(
                    accessions[
                        "SampleID"
                    ]
                )


                metadata_samples = set(
                    metadata[
                        sample_column
                    ]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )


                ################################################
                # Accessions missing from metadata
                ################################################

                missing_in_metadata = sorted(
                    accession_samples
                    -
                    metadata_samples
                )


                accessions_match_metadata = (
                    len(
                        missing_in_metadata
                    )
                    == 0
                )


                add_check(
                    "accession_metadata_match",
                    accessions_match_metadata,
                    (
                        "All accession SampleIDs occur in metadata."
                        if accessions_match_metadata
                        else
                        "Accession SampleIDs missing in metadata: "
                        + ", ".join(
                            missing_in_metadata[:10]
                        )
                    )
                )


                if not accessions_match_metadata:

                    errors.append(
                        "Accession/metadata SampleID mismatch."
                    )


                ################################################
                # Metadata samples without accession
                ################################################

                missing_accessions = sorted(
                    metadata_samples
                    -
                    accession_samples
                )


                metadata_complete = (
                    len(
                        missing_accessions
                    )
                    == 0
                )


                add_check(
                    "metadata_accession_match",
                    metadata_complete,
                    (
                        "All metadata SampleIDs have accessions."
                        if metadata_complete
                        else
                        "Metadata SampleIDs without accession: "
                        + ", ".join(
                            missing_accessions[:10]
                        )
                    )
                )


                if not metadata_complete:

                    errors.append(
                        "Metadata samples without accession."
                    )





    ########################################################
    # Save reports
    ########################################################

    output_json = Path(
        args.json_output
    )

    output_tsv = Path(
        args.tsv_output
    )


    output_json.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_tsv.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    report = {

        "status":
            (
                "PASS"
                if len(errors) == 0
                else "FAIL"
            ),

        "errors":
            errors,

        "checks":
            CHECKS
    }


    with open(

        output_json,

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            report,
            handle,
            indent=2
        )


    pd.DataFrame(
        CHECKS
    ).to_csv(

        output_tsv,

        sep="\t",

        index=False
    )


    ########################################################
    # Console output
    ########################################################

    print()
    print(
        "=" * 70
    )

    print(
        "MICROBIOME PIPELINE PREFLIGHT VALIDATION"
    )

    print(
        "=" * 70
    )


    for check in CHECKS:

        symbol = (
            "PASS"
            if check["Passed"]
            else "FAIL"
        )

        print(

            f"[{symbol:4s}] "
            f"{check['Check']}: "
            f"{check['Message']}"

        )


    print(
        "=" * 70
    )


    if errors:

        print(
            f"PREFLIGHT FAILED: {len(errors)} error(s)."
        )

        print(
            "=" * 70
        )

        sys.exit(1)


    print(
        "PREFLIGHT PASSED."
    )

    print(
        "Pipeline inputs/configuration are ready."
    )

    print(
        "=" * 70
    )




if __name__ == "__main__":

    main()