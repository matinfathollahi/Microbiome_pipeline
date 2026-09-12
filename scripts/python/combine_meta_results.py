#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = [

    "FeatureID",
    "EffectSize",
    "StandardError",
    "Pvalue",
    "FDR",
    "Study",
    "Method",
    "Comparison"
]


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    tables = []

    for path in args.inputs:

        path = Path(path)

        if not path.is_file():

            raise FileNotFoundError(
                path
            )

        data = pd.read_csv(
            path,
            sep="\t"
        )

        missing = [
            column
            for column in REQUIRED_COLUMNS
            if column not in data.columns
        ]

        if missing:

            raise ValueError(
                f"{path}: missing columns "
                f"{missing}"
            )

        tables.append(
            data[REQUIRED_COLUMNS].copy()
        )

    combined = pd.concat(
        tables,
        ignore_index=True
    )

    combined["EffectSize"] = pd.to_numeric(
        combined["EffectSize"],
        errors="coerce"
    )

    combined["StandardError"] = pd.to_numeric(
        combined["StandardError"],
        errors="coerce"
    )

    combined = combined.loc[

        combined["EffectSize"].notna()
        & combined["StandardError"].notna()
        & (combined["StandardError"] > 0)

    ].copy()

    if combined.empty:

        raise ValueError(
            "No valid effects remain "
            "for meta-analysis."
        )

    duplicated = combined.duplicated(
        subset=[
            "Study",
            "FeatureID"
        ]
    )

    if duplicated.any():

        bad = combined.loc[
            duplicated,
            [
                "Study",
                "FeatureID"
            ]
        ]

        raise ValueError(
            "Duplicated Study/FeatureID effects found:\n"
            + bad.head(10).to_string(
                index=False
            )
        )

    Path(
        args.output
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    combined.to_csv(
        args.output,
        sep="\t",
        index=False
    )

    print(
        f"Studies : "
        f"{combined['Study'].nunique()}"
    )

    print(
        f"Taxa    : "
        f"{combined['FeatureID'].nunique()}"
    )

    print(
        f"Effects : {len(combined)}"
    )


if __name__ == "__main__":
    main()