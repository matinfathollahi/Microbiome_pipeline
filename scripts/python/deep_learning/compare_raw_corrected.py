#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


############################################################
# Arguments
############################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Paired comparison of Raw versus "
            "batch-corrected deep-learning results."
        )
    )

    parser.add_argument(
        "--raw-metrics",
        required=True
    )

    parser.add_argument(
        "--corrected-metrics",
        required=True
    )

    parser.add_argument(
        "--raw-predictions",
        required=True
    )

    parser.add_argument(
        "--corrected-predictions",
        required=True
    )

    parser.add_argument(
        "--raw-nested",
        required=True
    )

    parser.add_argument(
        "--corrected-nested",
        required=True
    )

    parser.add_argument(
        "--raw-importance",
        required=True
    )

    parser.add_argument(
        "--corrected-importance",
        required=True
    )

    parser.add_argument(
        "--top-features",
        type=int,
        default=20
    )

    parser.add_argument(
        "--output",
        required=True
    )

    return parser.parse_args()


############################################################
# Helpers
############################################################

def read_tsv(path):

    df = pd.read_csv(
        path,
        sep="\t"
    )

    if df.empty:

        raise ValueError(
            f"Empty input file: {path}"
        )

    return df


############################################################
# Main
############################################################

def main():

    args = parse_args()

    output_dir = Path(
        args.output
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    ########################################################
    # Final test metrics
    ########################################################

    raw_metrics = read_tsv(
        args.raw_metrics
    )

    corrected_metrics = read_tsv(
        args.corrected_metrics
    )


    if len(raw_metrics) != 1:

        raise ValueError(
            "Raw final metrics must contain "
            "exactly one row."
        )


    if len(corrected_metrics) != 1:

        raise ValueError(
            "Corrected final metrics must contain "
            "exactly one row."
        )


    raw_metric_names = set(
        raw_metrics.columns
    )

    corrected_metric_names = set(
        corrected_metrics.columns
    )


    common_metrics = sorted(
        raw_metric_names
        &
        corrected_metric_names
    )


    metric_rows = []


    for metric in common_metrics:

        raw_value = pd.to_numeric(
            raw_metrics.iloc[0][metric],
            errors="coerce"
        )

        corrected_value = pd.to_numeric(
            corrected_metrics.iloc[0][metric],
            errors="coerce"
        )


        if (
            pd.isna(raw_value)
            or
            pd.isna(corrected_value)
        ):

            continue


        metric_rows.append(
            {
                "Metric":
                    metric,

                "Raw":
                    float(raw_value),

                "Corrected":
                    float(corrected_value),

                "Delta_Corrected_minus_Raw":
                    float(
                        corrected_value
                        -
                        raw_value
                    )
            }
        )


    metric_comparison = pd.DataFrame(
        metric_rows
    )


    if metric_comparison.empty:

        raise RuntimeError(
            "No comparable final metrics found."
        )


    metric_comparison.to_csv(
        output_dir
        / "final_metrics_comparison.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Final test predictions
    ########################################################

    raw_pred = read_tsv(
        args.raw_predictions
    )

    corrected_pred = read_tsv(
        args.corrected_predictions
    )


    required_prediction_columns = [
        "SampleID",
        "TrueLabel",
        "PredictedLabel"
    ]


    for column in required_prediction_columns:

        if column not in raw_pred.columns:

            raise ValueError(
                f"Raw predictions missing "
                f"column: {column}"
            )

        if column not in corrected_pred.columns:

            raise ValueError(
                f"Corrected predictions missing "
                f"column: {column}"
            )


    if raw_pred["SampleID"].duplicated().any():

        raise ValueError(
            "Duplicate SampleID in raw predictions."
        )


    if corrected_pred[
        "SampleID"
    ].duplicated().any():

        raise ValueError(
            "Duplicate SampleID in corrected predictions."
        )


    raw_ids = set(
        raw_pred["SampleID"]
    )

    corrected_ids = set(
        corrected_pred["SampleID"]
    )


    if raw_ids != corrected_ids:

        raise RuntimeError(
            "Raw and corrected final test SampleIDs "
            "are not identical."
        )


    merged_predictions = raw_pred.merge(

        corrected_pred,

        on="SampleID",

        how="inner",

        suffixes=(
            "_Raw",
            "_Corrected"
        ),

        validate="one_to_one"
    )


    if not (
        merged_predictions[
            "TrueLabel_Raw"
        ].astype(str)
        ==
        merged_predictions[
            "TrueLabel_Corrected"
        ].astype(str)
    ).all():

        raise RuntimeError(
            "True labels differ between "
            "Raw and Corrected predictions."
        )


    merged_predictions[
        "Raw_Correct"
    ] = (
        merged_predictions[
            "PredictedLabel_Raw"
        ].astype(str)
        ==
        merged_predictions[
            "TrueLabel_Raw"
        ].astype(str)
    )


    merged_predictions[
        "Corrected_Correct"
    ] = (
        merged_predictions[
            "PredictedLabel_Corrected"
        ].astype(str)
        ==
        merged_predictions[
            "TrueLabel_Raw"
        ].astype(str)
    )


    merged_predictions[
        "Prediction_Agreement"
    ] = (
        merged_predictions[
            "PredictedLabel_Raw"
        ].astype(str)
        ==
        merged_predictions[
            "PredictedLabel_Corrected"
        ].astype(str)
    )


    probability_columns_raw = [
        column
        for column in raw_pred.columns
        if column.startswith(
            "Probability_"
        )
    ]


    probability_columns_corrected = [
        column
        for column in corrected_pred.columns
        if column.startswith(
            "Probability_"
        )
    ]


    common_probability_columns = sorted(
        set(
            probability_columns_raw
        )
        &
        set(
            probability_columns_corrected
        )
    )


    probability_delta_columns = []


    for column in common_probability_columns:

        raw_column = (
            f"{column}_Raw"
        )

        corrected_column = (
            f"{column}_Corrected"
        )

        delta_column = (
            f"Delta_{column}"
        )

        merged_predictions[
            delta_column
        ] = (

            merged_predictions[
                corrected_column
            ]

            -

            merged_predictions[
                raw_column
            ]
        )

        probability_delta_columns.append(
            delta_column
        )


    merged_predictions.to_csv(
        output_dir
        / "prediction_comparison.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Prediction agreement summary
    ########################################################

    n_samples = len(
        merged_predictions
    )


    both_correct = int(
        (
            merged_predictions[
                "Raw_Correct"
            ]
            &
            merged_predictions[
                "Corrected_Correct"
            ]
        ).sum()
    )


    raw_only_correct = int(
        (
            merged_predictions[
                "Raw_Correct"
            ]
            &
            ~merged_predictions[
                "Corrected_Correct"
            ]
        ).sum()
    )


    corrected_only_correct = int(
        (
            ~merged_predictions[
                "Raw_Correct"
            ]
            &
            merged_predictions[
                "Corrected_Correct"
            ]
        ).sum()
    )


    both_wrong = int(
        (
            ~merged_predictions[
                "Raw_Correct"
            ]
            &
            ~merged_predictions[
                "Corrected_Correct"
            ]
        ).sum()
    )


    prediction_agreement = pd.DataFrame(
        [
            {
                "N_Test_Samples":
                    n_samples,

                "Prediction_Agreement_Rate":
                    float(
                        merged_predictions[
                            "Prediction_Agreement"
                        ].mean()
                    ),

                "Both_Correct":
                    both_correct,

                "Raw_Only_Correct":
                    raw_only_correct,

                "Corrected_Only_Correct":
                    corrected_only_correct,

                "Both_Wrong":
                    both_wrong
            }
        ]
    )


    prediction_agreement.to_csv(
        output_dir
        / "prediction_agreement_summary.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Nested CV comparison
    ########################################################

    raw_nested = read_tsv(
        args.raw_nested
    )

    corrected_nested = read_tsv(
        args.corrected_nested
    )


    if len(raw_nested) != len(
        corrected_nested
    ):

        raise RuntimeError(
            "Raw and corrected nested CV "
            "have different numbers of folds."
        )


    common_nested_metrics = [

        column

        for column in raw_nested.columns

        if (
            column
            in corrected_nested.columns

            and pd.api.types.is_numeric_dtype(
                raw_nested[column]
            )

            and pd.api.types.is_numeric_dtype(
                corrected_nested[column]
            )
        )
    ]


    nested_rows = []


    for metric in common_nested_metrics:

        raw_values = pd.to_numeric(
            raw_nested[metric],
            errors="coerce"
        )

        corrected_values = pd.to_numeric(
            corrected_nested[metric],
            errors="coerce"
        )


        valid = (
            raw_values.notna()
            &
            corrected_values.notna()
        )


        if not valid.any():

            continue


        differences = (
            corrected_values[valid]
            -
            raw_values[valid]
        )


        nested_rows.append(
            {
                "Metric":
                    metric,

                "N_Folds":
                    int(
                        valid.sum()
                    ),

                "Raw_Mean":
                    float(
                        raw_values[
                            valid
                        ].mean()
                    ),

                "Corrected_Mean":
                    float(
                        corrected_values[
                            valid
                        ].mean()
                    ),

                "Mean_Delta":
                    float(
                        differences.mean()
                    ),

                "Raw_STD":
                    float(
                        raw_values[
                            valid
                        ].std(
                            ddof=1
                        )
                    )
                    if valid.sum() > 1
                    else 0.0,

                "Corrected_STD":
                    float(
                        corrected_values[
                            valid
                        ].std(
                            ddof=1
                        )
                    )
                    if valid.sum() > 1
                    else 0.0
            }
        )


    nested_comparison = pd.DataFrame(
        nested_rows
    )


    nested_comparison.to_csv(
        output_dir
        / "nested_cv_comparison.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Explainability comparison
    ########################################################

    raw_importance = read_tsv(
        args.raw_importance
    )

    corrected_importance = read_tsv(
        args.corrected_importance
    )


    for name, df in [
        (
            "raw",
            raw_importance
        ),
        (
            "corrected",
            corrected_importance
        )
    ]:

        for column in [
            "Feature",
            "ConsensusScore"
        ]:

            if column not in df.columns:

                raise ValueError(
                    f"{name} consensus importance "
                    f"missing column: {column}"
                )


    raw_importance = (
        raw_importance
        .sort_values(
            "ConsensusScore",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )


    corrected_importance = (
        corrected_importance
        .sort_values(
            "ConsensusScore",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )


    top_n = max(
        1,
        args.top_features
    )


    raw_top = set(
        raw_importance
        .head(
            top_n
        )[
            "Feature"
        ]
    )


    corrected_top = set(
        corrected_importance
        .head(
            top_n
        )[
            "Feature"
        ]
    )


    intersection = (
        raw_top
        &
        corrected_top
    )

    union = (
        raw_top
        |
        corrected_top
    )


    jaccard = (

        len(
            intersection
        )
        /
        len(
            union
        )

        if union
        else np.nan
    )


    importance_merged = (

        raw_importance[
            [
                "Feature",
                "ConsensusScore"
            ]
        ]

        .rename(
            columns={
                "ConsensusScore":
                    "Raw_ConsensusScore"
            }
        )

        .merge(

            corrected_importance[
                [
                    "Feature",
                    "ConsensusScore"
                ]
            ].rename(
                columns={
                    "ConsensusScore":
                        "Corrected_ConsensusScore"
                }
            ),

            on="Feature",

            how="outer"
        )

        .fillna(
            0.0
        )
    )


    importance_merged[
        "Raw_Rank"
    ] = (
        importance_merged[
            "Raw_ConsensusScore"
        ]
        .rank(
            ascending=False,
            method="average"
        )
    )


    importance_merged[
        "Corrected_Rank"
    ] = (
        importance_merged[
            "Corrected_ConsensusScore"
        ]
        .rank(
            ascending=False,
            method="average"
        )
    )


    rank_correlation = (
        importance_merged[
            [
                "Raw_Rank",
                "Corrected_Rank"
            ]
        ]
        .corr(
            method="spearman"
        )
        .iloc[
            0,
            1
        ]
    )


    importance_merged[
        "Delta_ConsensusScore"
    ] = (

        importance_merged[
            "Corrected_ConsensusScore"
        ]

        -

        importance_merged[
            "Raw_ConsensusScore"
        ]
    )


    importance_merged = (
        importance_merged
        .sort_values(
            "Raw_ConsensusScore",
            ascending=False
        )
    )


    importance_merged.to_csv(
        output_dir
        / "explainability_feature_comparison.tsv",
        sep="\t",
        index=False
    )


    overlap_summary = pd.DataFrame(
        [
            {
                "Top_N":
                    top_n,

                "Raw_Top_Features":
                    len(
                        raw_top
                    ),

                "Corrected_Top_Features":
                    len(
                        corrected_top
                    ),

                "Shared_Top_Features":
                    len(
                        intersection
                    ),

                "Top_Feature_Jaccard":
                    float(
                        jaccard
                    ),

                "Consensus_Rank_Spearman":
                    float(
                        rank_correlation
                    )
            }
        ]
    )


    overlap_summary.to_csv(
        output_dir
        / "explainability_overlap_summary.tsv",
        sep="\t",
        index=False
    )

    ########################################################
    # Overall summary
    ########################################################

    primary_metrics = {}

    for metric in [
        "ROC_AUC",
        "PR_AUC",
        "BalancedAccuracy",
        "F1_macro",
        "MCC"
    ]:

        match = metric_comparison[
            metric_comparison[
                "Metric"
            ] == metric
        ]

        if not match.empty:

            row = match.iloc[0]

            primary_metrics[
                metric
            ] = {
                "Raw":
                    float(
                        row["Raw"]
                    ),

                "Corrected":
                    float(
                        row["Corrected"]
                    ),

                "Delta":
                    float(
                        row[
                            "Delta_Corrected_minus_Raw"
                        ]
                    )
            }


    summary = {

        "Comparison":
            "Raw_Inductive_vs_MMUPHin_Transductive_Sensitivity_DL",

        "Paired_Test_Set":
            True,

        "N_Test_Samples":
            int(
                n_samples
            ),

        "Prediction_Agreement_Rate":
            float(
                merged_predictions[
                    "Prediction_Agreement"
                ].mean()
            ),

        "Primary_Metrics":
            primary_metrics,

        "Top_Feature_Jaccard":
            float(
                jaccard
            ),
        "Raw_Analysis_Mode":
            "primary_inductive",

        "Raw_Primary_Analysis":
            True,

        "Corrected_Analysis_Mode":
            "transductive_sensitivity",

        "Corrected_Primary_Analysis":
            False,

        "Corrected_Uses_Global_MMUPHin":
            True,

        "Interpretation":
            (
                "Raw DL is the primary strict inductive "
                "analysis. Batch-corrected DL is a "
                "transductive MMUPHin sensitivity analysis. "
                "Performance deltas must not be interpreted "
                "as a head-to-head comparison of two fully "
                "inductive pipelines."
            ),

        "Consensus_Rank_Spearman":
            float(
                rank_correlation
            )
    }


    with open(
        output_dir
        / "comparison_summary.json",
        "w",
        encoding="utf-8"
    ) as handle:

        json.dump(
            summary,
            handle,
            indent=2
        )


    print(
        "Raw inductive vs MMUPHin transductive "
        "sensitivity DL comparison completed."
    )

    print(
        f"N test samples: {n_samples}"
    )

    print(
        "Prediction agreement:",
        round(
            summary[
                "Prediction_Agreement_Rate"
            ],
            4
        )
    )

    print(
        "Top-feature Jaccard:",
        round(
            jaccard,
            4
        )
    )


if __name__ == "__main__":

    main()