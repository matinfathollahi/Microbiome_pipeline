#!/usr/bin/env python3

import argparse
import csv
import io
from pathlib import Path

import pandas as pd


def read_feature_table(path):
    text = Path(path).read_text(encoding="utf-8-sig")

    lines = [
        line
        for line in text.splitlines()
        if not line.startswith("# Constructed from biom file")
    ]

    df = pd.read_csv(
        io.StringIO("\n".join(lines) + "\n"),
        sep="\t"
    )

    df = df.rename(
        columns={df.columns[0]: "FeatureID"}
    )

    df["FeatureID"] = df["FeatureID"].astype(str)

    return df


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--table", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--class-column", required=True)

    parser.add_argument("--lefse-table", required=True)
    parser.add_argument("--abundance", required=True)
    parser.add_argument("--mapping", required=True)

    args = parser.parse_args()

    table = read_feature_table(args.table)

    metadata = pd.read_csv(
        args.metadata,
        sep="\t",
        dtype=str
    )

    if "SampleID" in metadata.columns:
        sample_column = "SampleID"
    else:
        sample_column = metadata.columns[0]

    if args.class_column not in metadata.columns:
        raise ValueError(
            f"Class column '{args.class_column}' not found."
        )

    if metadata[sample_column].duplicated().any():
        raise ValueError(
            "Duplicate SampleID found in metadata."
        )

    metadata = metadata.set_index(
        sample_column,
        drop=False
    )

    feature_samples = [
        column
        for column in table.columns
        if column != "FeatureID"
    ]

    common_samples = [
        sample
        for sample in feature_samples
        if sample in metadata.index
    ]

    if not common_samples:
        raise ValueError(
            "No common samples between feature table and metadata."
        )

    classes = metadata.loc[
        common_samples,
        args.class_column
    ]

    if classes.isna().any():
        raise ValueError(
            "Missing class values detected."
        )

    if classes.nunique() < 2:
        raise ValueError(
            "LEfSe requires at least two groups."
        )

    counts = table[
        ["FeatureID"] + common_samples
    ].copy()

    for sample in common_samples:
        counts[sample] = pd.to_numeric(
            counts[sample],
            errors="raise"
        )

    # Clean abundance table for heatmap
    counts.to_csv(
        args.abundance,
        sep="\t",
        index=False
    )

    # LEfSe changes some feature IDs internally.
    # Therefore create safe IDs.
    mapping = pd.DataFrame({
        "LefseID": [
            f"F{i:07d}"
            for i in range(1, len(counts) + 1)
        ],
        "FeatureID": counts["FeatureID"]
    })

    mapping.to_csv(
        args.mapping,
        sep="\t",
        index=False
    )

    Path(args.lefse_table).parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        args.lefse_table,
        "w",
        newline="",
        encoding="utf-8"
    ) as handle:

        writer = csv.writer(
            handle,
            delimiter="\t",
            lineterminator="\n"
        )

        # First row = LEfSe class
        writer.writerow(
            [args.class_column]
            + classes.astype(str).tolist()
        )

        for lefse_id, (_, row) in zip(
            mapping["LefseID"],
            counts.iterrows()
        ):

            writer.writerow(
                [lefse_id]
                + [
                    row[sample]
                    for sample in common_samples
                ]
            )

    print("LEfSe input prepared.")
    print("Samples:", len(common_samples))
    print("Features:", len(counts))
    print(
        "Groups:",
        ", ".join(sorted(classes.unique()))
    )


if __name__ == "__main__":
    main()