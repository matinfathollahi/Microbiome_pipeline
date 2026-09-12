#!/usr/bin/env python3

import argparse
import json
import shutil

from pathlib import Path

import pandas as pd


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".svg",
    ".tsv",
    ".csv",
    ".json"
}


SOURCES = {

    "microbiome_alpha":
        Path(
            "results/figures/alpha"
        ),

    "microbiome_alpha_statistics":
        Path(
            "results/statistics/alpha"
        ),

    "batch_diagnostics":
        Path(
            "results/batch_effect/diagnostics"
        ),
    "batch_confounding":
        Path(
            "results/batch_effect/confounding"
        ),

    "ancombc2_primary":
        Path(
            "results/ancombc2"
        ),

    "aldex2_supplementary":
        Path(
            "results/aldex2"
        ),

    "maaslin2_supplementary":
        Path(
            "results/maaslin2"
        ),

    "supplementary_da_method_comparison":
        Path(
            "results/supplementary_da"
        ),

    "lefse_primary_consensus":
        Path(
            "results/lefse/consensus"
        ),

    "lefse_primary_per_study":
        Path(
            "results/lefse/per_study"
        ),

    "lefse_supplementary_pooled_figures":
        Path(
            "results/lefse/figures"
        ),

    "lefse_supplementary_pooled_results":
        Path(
            "results/lefse/significant_taxa.tsv"
        ),

    "machine_learning_batch_corrected":
        Path(
            "results/machine_learning_batch_corrected/final"
        ),

    "deep_learning_batch_corrected_final":
        Path(
            "results/deep_learning/batch_corrected/final"
        ),

    "deep_learning_batch_corrected_explainability":
        Path(
            "results/deep_learning/batch_corrected/explainability"
        ),

    "deep_learning_batch_corrected_visualization":
        Path(
            "results/deep_learning/batch_corrected/visualization"
        ),

    "deep_learning_raw_vs_corrected":
        Path(
            "results/deep_learning/comparison"
        ),

    "selbal":
        Path(
            "results/selbal/analysis"
        ),

    "meta_forest":
        Path(
            "results/meta_analysis/figures/forest"
        ),

    "meta_funnel":
        Path(
            "results/meta_analysis/figures/funnel"
        ),

    "meta_heatmap":
        Path(
            "results/meta_analysis/figures/heatmap"
        ),

    "meta_summary":
        Path(
            "results/meta_analysis/summary"
        ),

    "machine_learning_final":
        Path(
            "results/machine_learning/final"
        ),

    "deep_learning_nested_cv":
        Path(
            "results/deep_learning/nested_cv"
        ),

    "deep_learning_final":
        Path(
            "results/deep_learning/final"
        ),

    "deep_learning_explainability":
        Path(
            "results/deep_learning/explainability"
        ),

    "deep_learning_visualization":
        Path(
            "results/deep_learning/visualization"
        )
}


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--include-predictive-sensitivity",
        action="store_true",
        help=(
            "Include MMUPHin-corrected ML/DL "
            "transductive sensitivity outputs."
        )
    )

    args = parser.parse_args()

    sources = dict(SOURCES)

    sensitivity_categories = [
        "machine_learning_batch_corrected",
        "deep_learning_batch_corrected_final",
        "deep_learning_batch_corrected_explainability",
        "deep_learning_batch_corrected_visualization",
        "deep_learning_raw_vs_corrected",
    ]

    if not args.include_predictive_sensitivity:

        for category in sensitivity_categories:

            sources.pop(
                category,
                None
            )

    output_dir = Path(
        args.output
    )

    if output_dir.exists():

        shutil.rmtree(
            output_dir
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    manifest_rows = []

    for category, source in sources.items():

        if not source.exists():

            continue

        if source.is_file():

            files = [
                source
            ]

        else:

            files = [
                path
                for path in source.rglob("*")
                if path.is_file()
            ]

        for source_file in files:

            if (
                source_file.suffix.lower()
                not in ALLOWED_EXTENSIONS
            ):

                continue

            if source.is_file():

                relative = (
                    source_file.name
                )

            else:

                relative = (
                    source_file.relative_to(
                        source
                    )
                )

            destination = (

                output_dir
                / category
                / relative
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            shutil.copy2(
                source_file,
                destination
            )

            manifest_rows.append({

                "Category":
                    category,

                "Source":
                    str(
                        source_file
                    ),

                "PublicationFile":
                    str(
                        destination
                    ),

                "Extension":
                    source_file
                    .suffix
                    .lower(),

                "Bytes":
                    source_file
                    .stat()
                    .st_size
            })

    manifest = pd.DataFrame(

        manifest_rows,

        columns=[
            "Category",
            "Source",
            "PublicationFile",
            "Extension",
            "Bytes"
        ]
    )

    manifest.to_csv(

        output_dir
        / "manifest.tsv",

        sep="\t",

        index=False
    )

    if manifest.empty:

        number_figures = 0
        categories = []

    else:

        number_figures = int(

            manifest[
                "Extension"
            ].isin(
                [
                    ".pdf",
                    ".png",
                    ".svg"
                ]
            ).sum()
        )

        categories = sorted(

            manifest[
                "Category"
            ]
            .unique()
            .tolist()
        )

    summary = {

        "files":
            int(
                len(
                    manifest
                )
            ),

        "figures":
            number_figures,

        "categories":
            categories,

        "purpose":
            (
                "Publication-ready figure "
                "and source-data bundle."
            )
    }

    with open(

        output_dir
        / "publication_summary.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            summary,
            handle,
            indent=2
        )

    print(
        f"Publication files: {len(manifest)}"
    )

    print(
        f"Publication figures: {number_figures}"
    )


if __name__ == "__main__":
    main()