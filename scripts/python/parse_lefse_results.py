#!/usr/bin/env python3

import argparse
from pathlib import Path

import pandas as pd


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--results", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--taxonomy", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    mapping = pd.read_csv(
        args.mapping,
        sep="\t",
        dtype=str
    )

    id_map = dict(
        zip(
            mapping["LefseID"],
            mapping["FeatureID"]
        )
    )

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
            taxonomy[feature_column],
            taxonomy[taxon_column]
        )
    )

    rows = []

    with open(
        args.results,
        encoding="utf-8",
        errors="replace"
    ) as handle:

        for line in handle:

            parts = line.rstrip("\n").split("\t")

            # Significant LEfSe lines contain:
            # feature, mean, group, LDA, wilcoxon
            if len(parts) < 5:
                continue

            lefse_id = parts[0]
            log_mean = parts[1]
            group = parts[2]
            lda = parts[3]
            wilcoxon = parts[4]

            if not group or not lda:
                continue

            try:
                lda_value = float(lda)
            except ValueError:
                continue

            feature_id = id_map.get(
                lefse_id,
                lefse_id
            )

            taxon = taxonomy_map.get(
                feature_id,
                feature_id
            )

            if pd.isna(taxon):
                taxon = feature_id

            rows.append({
                "FeatureID": feature_id,
                "Taxon": str(taxon),
                "LDA": abs(lda_value),
                "Group": group,
                "Log10Mean": log_mean,
                "Wilcoxon": wilcoxon
            })

    result = pd.DataFrame(
        rows,
        columns=[
            "FeatureID",
            "Taxon",
            "LDA",
            "Group",
            "Log10Mean",
            "Wilcoxon"
        ]
    )

    if not result.empty:

        duplicated = result[
            "Taxon"
        ].duplicated(keep=False)

        result.loc[
            duplicated,
            "Taxon"
        ] = result.loc[
            duplicated
        ].apply(
            lambda row:
            f"{row['Taxon']} [{row['FeatureID']}]",
            axis=1
        )

        result = result.sort_values(
            "LDA",
            ascending=False
        )

    Path(args.output).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.to_csv(
        args.output,
        sep="\t",
        index=False
    )

    print(
        "Significant LEfSe features:",
        len(result)
    )


if __name__ == "__main__":
    main()