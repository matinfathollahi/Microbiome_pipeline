#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


############################################################
# Arguments
############################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Compare primary ANCOM-BC2 differential abundance "
            "results with supplementary ALDEx2 and MaAsLin2."
        )
    )

    parser.add_argument(
        "--ancombc2",
        required=True
    )

    parser.add_argument(
        "--aldex2",
        required=True
    )

    parser.add_argument(
        "--maaslin2",
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--primary-output",
        required=True
    )

    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05
    )

    return parser.parse_args()


############################################################
# Helpers
############################################################

def require_columns(df, columns, name):

    missing = [
        column
        for column in columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"{name} is missing required columns: "
            + ", ".join(missing)
        )


def to_bool(series):

    if series.dtype == bool:
        return series

    return (
        series
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "true": True,
            "false": False,
            "1": True,
            "0": False
        })
        .fillna(False)
        .astype(bool)
    )


############################################################
# Main
############################################################

def main():

    args = parse_args()

    output_path = Path(args.output)
    primary_output_path = Path(args.primary_output)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    primary_output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    ########################################################
    # Read ANCOM-BC2
    ########################################################

    ancombc = pd.read_csv(
        args.ancombc2,
        sep="\t"
    )

    require_columns(
        ancombc,
        [
            "FeatureID",
            "EffectSize",
            "FDR",
            "Direction",
            "RobustSignificant"
        ],
        "ANCOM-BC2"
    )

    ancombc["RobustSignificant"] = to_bool(
        ancombc["RobustSignificant"]
    )

    ancombc = ancombc[
        [
            "FeatureID",
            "EffectSize",
            "FDR",
            "Direction",
            "RobustSignificant"
        ]
    ].copy()

    ancombc = ancombc.rename(
        columns={
            "EffectSize":
                "ANCOMBC2_EffectSize",

            "FDR":
                "ANCOMBC2_FDR",

            "Direction":
                "ANCOMBC2_Direction",

            "RobustSignificant":
                "ANCOMBC2_Significant"
        }
    )


    ########################################################
    # Read ALDEx2
    ########################################################

    aldex2 = pd.read_csv(
        args.aldex2,
        sep="\t"
    )

    require_columns(
        aldex2,
        [
            "FeatureID",
            "Coefficient",
            "FDR",
            "Direction",
            "Significant"
        ],
        "ALDEx2"
    )

    aldex2["Significant"] = to_bool(
        aldex2["Significant"]
    )

    aldex2 = aldex2[
        [
            "FeatureID",
            "Coefficient",
            "FDR",
            "Direction",
            "Significant"
        ]
    ].copy()

    aldex2 = aldex2.rename(
        columns={
            "Coefficient":
                "ALDEx2_Coefficient",

            "FDR":
                "ALDEx2_FDR",

            "Direction":
                "ALDEx2_Direction",

            "Significant":
                "ALDEx2_Significant"
        }
    )


    ########################################################
    # Read MaAsLin2
    ########################################################

    maaslin2 = pd.read_csv(
        args.maaslin2,
        sep="\t"
    )

    require_columns(
        maaslin2,
        [
            "FeatureID",
            "Coefficient",
            "FDR",
            "Direction",
            "Significant"
        ],
        "MaAsLin2"
    )

    maaslin2["Significant"] = to_bool(
        maaslin2["Significant"]
    )

    maaslin2 = maaslin2[
        [
            "FeatureID",
            "Coefficient",
            "FDR",
            "Direction",
            "Significant"
        ]
    ].copy()

    maaslin2 = maaslin2.rename(
        columns={
            "Coefficient":
                "MaAsLin2_Coefficient",

            "FDR":
                "MaAsLin2_FDR",

            "Direction":
                "MaAsLin2_Direction",

            "Significant":
                "MaAsLin2_Significant"
        }
    )


    ########################################################
    # Check duplicates
    ########################################################

    for name, df in [
        ("ANCOM-BC2", ancombc),
        ("ALDEx2", aldex2),
        ("MaAsLin2", maaslin2)
    ]:

        if df["FeatureID"].duplicated().any():

            duplicated = (
                df.loc[
                    df["FeatureID"].duplicated(),
                    "FeatureID"
                ]
                .astype(str)
                .tolist()
            )

            raise ValueError(
                f"{name} contains duplicated FeatureID values: "
                + ", ".join(duplicated[:10])
            )


    ########################################################
    # Merge
    #
    # ANCOM-BC2 is PRIMARY, therefore it is the anchor table.
    ########################################################

    comparison = ancombc.merge(
        aldex2,
        on="FeatureID",
        how="left",
        validate="one_to_one"
    )

    comparison = comparison.merge(
        maaslin2,
        on="FeatureID",
        how="left",
        validate="one_to_one"
    )


    ########################################################
    # Presence flags
    ########################################################

    comparison["TestedByALDEx2"] = (
        comparison["ALDEx2_FDR"].notna()
    )

    comparison["TestedByMaAsLin2"] = (
        comparison["MaAsLin2_FDR"].notna()
    )


    ########################################################
    # Recalculate supplementary significance defensively
    ########################################################

    comparison["ALDEx2_Significant"] = (
        comparison["ALDEx2_Significant"]
        .fillna(False)
        .astype(bool)
        &
        comparison["ALDEx2_FDR"].le(args.alpha)
    )

    comparison["MaAsLin2_Significant"] = (
        comparison["MaAsLin2_Significant"]
        .fillna(False)
        .astype(bool)
        &
        comparison["MaAsLin2_FDR"].le(args.alpha)
    )


    ########################################################
    # Direction agreement
    ########################################################

    comparison["ALDEx2_DirectionAgreement"] = (
        comparison["ALDEx2_Direction"]
        ==
        comparison["ANCOMBC2_Direction"]
    )

    comparison["MaAsLin2_DirectionAgreement"] = (
        comparison["MaAsLin2_Direction"]
        ==
        comparison["ANCOMBC2_Direction"]
    )

    comparison[
        "ALDEx2_DirectionAgreement"
    ] = comparison[
        "ALDEx2_DirectionAgreement"
    ].fillna(False)

    comparison[
        "MaAsLin2_DirectionAgreement"
    ] = comparison[
        "MaAsLin2_DirectionAgreement"
    ].fillna(False)


    ########################################################
    # Supplementary support
    #
    # Support requires:
    #
    # 1. Primary ANCOM-BC2 significant
    # 2. Supplementary method significant
    # 3. Same direction
    ########################################################

    comparison["SupportedByALDEx2"] = (
        comparison["ANCOMBC2_Significant"]
        &
        comparison["ALDEx2_Significant"]
        &
        comparison["ALDEx2_DirectionAgreement"]
    )

    comparison["SupportedByMaAsLin2"] = (
        comparison["ANCOMBC2_Significant"]
        &
        comparison["MaAsLin2_Significant"]
        &
        comparison["MaAsLin2_DirectionAgreement"]
    )


    ########################################################
    # Significant but directionally conflicting
    ########################################################

    comparison["ConflictingALDEx2"] = (
        comparison["ANCOMBC2_Significant"]
        &
        comparison["ALDEx2_Significant"]
        &
        ~comparison["ALDEx2_DirectionAgreement"]
    )

    comparison["ConflictingMaAsLin2"] = (
        comparison["ANCOMBC2_Significant"]
        &
        comparison["MaAsLin2_Significant"]
        &
        ~comparison["MaAsLin2_DirectionAgreement"]
    )


    ########################################################
    # Number of supplementary methods supporting result
    ########################################################

    comparison["SupplementarySupportCount"] = (
        comparison["SupportedByALDEx2"].astype(int)
        +
        comparison["SupportedByMaAsLin2"].astype(int)
    )


    ########################################################
    # Any supplementary support
    ########################################################

    comparison["AnySupplementarySupport"] = (
        comparison["SupplementarySupportCount"] >= 1
    )


    ########################################################
    # Robustness classification
    ########################################################

    def classify(row):

        if not row["ANCOMBC2_Significant"]:
            return "Not_primary_significant"

        if (
            row["SupportedByALDEx2"]
            and
            row["SupportedByMaAsLin2"]
        ):
            return "Supported_by_both"

        if row["SupportedByALDEx2"]:
            return "Supported_by_ALDEx2"

        if row["SupportedByMaAsLin2"]:
            return "Supported_by_MaAsLin2"

        if (
            row["ConflictingALDEx2"]
            or
            row["ConflictingMaAsLin2"]
        ):
            return "Significant_direction_conflict"

        return "Not_supported_by_supplementary_methods"


    comparison["RobustnessClassification"] = (
        comparison.apply(
            classify,
            axis=1
        )
    )


    ########################################################
    # Sort
    ########################################################

    comparison = comparison.sort_values(
        by=[
            "ANCOMBC2_Significant",
            "SupplementarySupportCount",
            "ANCOMBC2_FDR"
        ],
        ascending=[
            False,
            False,
            True
        ],
        na_position="last"
    )


    ########################################################
    # Save complete comparison
    ########################################################

    comparison.to_csv(
        output_path,
        sep="\t",
        index=False
    )


    ########################################################
    # Save Primary significant findings only
    ########################################################

    primary_results = comparison.loc[
        comparison["ANCOMBC2_Significant"]
    ].copy()

    primary_results.to_csv(
        primary_output_path,
        sep="\t",
        index=False
    )


    ########################################################
    # Console summary
    ########################################################

    print(
        "ANCOM-BC2 primary significant:",
        int(
            comparison[
                "ANCOMBC2_Significant"
            ].sum()
        )
    )

    print(
        "Supported by ALDEx2:",
        int(
            comparison[
                "SupportedByALDEx2"
            ].sum()
        )
    )

    print(
        "Supported by MaAsLin2:",
        int(
            comparison[
                "SupportedByMaAsLin2"
            ].sum()
        )
    )

    print(
        "Supported by at least one supplementary method:",
        int(
            comparison[
                "AnySupplementarySupport"
            ].sum()
        )
    )

    print(
        "Supported by both supplementary methods:",
        int(
            (
                comparison[
                    "SupplementarySupportCount"
                ]
                == 2
            ).sum()
        )
    )


if __name__ == "__main__":
    main()