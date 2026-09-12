#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

import matplotlib.pyplot as plt

from sklearn.manifold import TSNE

from sklearn.preprocessing import LabelEncoder
from microbiome_preprocessing import (
    MicrobiomeCLRPreprocessor
)

import umap

from deep_learning.models.mlp import build_mlp


def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--features",
        required=True
    )

    parser.add_argument(
        "--labels",
        required=True
    )

    parser.add_argument(
        "--models-dir",
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )



    parser.add_argument(
        "--seed",
        type=int,
        default=2026
    )

    parser.add_argument(
        "--tsne-perplexity",
        type=float,
        default=30
    )

    parser.add_argument(
        "--tsne-iterations",
        type=int,
        default=1000
    )

    parser.add_argument(
        "--umap-neighbors",
        type=int,
        default=15
    )

    parser.add_argument(
        "--umap-min-dist",
        type=float,
        default=0.1
    )

    return parser.parse_args()


def load_data(
    features_file,
    labels_file
):

    X = pd.read_csv(
        features_file,
        sep="\t",
        index_col=0
    )

    labels = pd.read_csv(
        labels_file,
        sep="\t",
        index_col=0
    )

    if labels.shape[1] != 1:

        raise ValueError(
            "Labels file must contain exactly one column."
        )

    if not X.index.equals(
        labels.index
    ):

        raise ValueError(
            "Feature and label sample order mismatch."
        )

    y_raw = labels.iloc[:, 0].astype(str)

    encoder = LabelEncoder()

    y = pd.Series(
        encoder.fit_transform(
            y_raw
        ),
        index=y_raw.index
    )

    return (
        X,
        y,
        y_raw,
        encoder
    )








def load_fold(
    fold_dir,
    output_dim,
    device
):

    fold_dir = Path(
        fold_dir
    )

    params_path = (
        fold_dir
        / "best_parameters.json"
    )

    model_path = (
        fold_dir
        / "final_model.pt"
    )

    scaler_path = (
        fold_dir
        / "scaler.joblib"
    )

    preprocessor_path = (
        fold_dir
        / "microbiome_preprocessor.joblib"
    )

    for path in [
        params_path,
        model_path,
        scaler_path,
        preprocessor_path
    ]:

        if not path.is_file():
            raise FileNotFoundError(
                path
            )

    microbiome_preprocessor = joblib.load(
        preprocessor_path
    )

    feature_names = list(
        microbiome_preprocessor
        .selected_features_
    )

    if not feature_names:
        raise ValueError(
            f"No selected features found in {preprocessor_path}"
        )

    input_dim = len(
        feature_names
    )

    with open(
        params_path,
        "r",
        encoding="utf-8"
    ) as handle:

        payload = json.load(
            handle
        )

    params = payload.get(
        "best_parameters",
        payload
    )

    model = build_mlp(
        params=params,
        input_dim=input_dim,
        output_dim=output_dim
    )

    state = torch.load(
        model_path,
        map_location=device
    )

    if (
        isinstance(state, dict)
        and
        "model_state_dict" in state
    ):
        state = state[
            "model_state_dict"
        ]

    model.load_state_dict(
        state
    )

    model.to(
        device
    )

    model.eval()

    scaler = joblib.load(
        scaler_path
    )

    if (
        hasattr(
            scaler,
            "n_features_in_"
        )
        and
        scaler.n_features_in_
        != input_dim
    ):
        raise ValueError(
            f"Fold feature mismatch: "
            f"preprocessor={input_dim}, "
            f"scaler={scaler.n_features_in_}"
        )

    extractor = nn.Sequential(
        *list(
            model.network.children()
        )[:-1]
    )

    extractor.to(
        device
    )

    extractor.eval()

    return (
        extractor,
        scaler,
        microbiome_preprocessor,
        feature_names
    )






def extract_latent(
    extractor,
    X,
    device
):

    with torch.no_grad():

        tensor = torch.as_tensor(
            X,
            dtype=torch.float32,
            device=device
        )

        latent = extractor(
            tensor
        )

    return (
        latent
        .cpu()
        .numpy()
    )


def save_scatter(
    data,
    x_column,
    y_column,
    label_column,
    title,
    output_base
):

    figure, axis = plt.subplots(
        figsize=(8, 7)
    )

    classes = sorted(
        data[
            label_column
        ].astype(str).unique()
    )

    for cls in classes:

        mask = (
            data[
                label_column
            ].astype(str)
            == str(cls)
        )

        axis.scatter(
            data.loc[
                mask,
                x_column
            ],
            data.loc[
                mask,
                y_column
            ],
            s=40,
            alpha=0.8,
            label=str(cls)
        )

    axis.set_xlabel(
        x_column
    )

    axis.set_ylabel(
        y_column
    )

    axis.set_title(
        title
    )

    axis.legend(
        title=label_column,
        frameon=False
    )

    figure.tight_layout()

    ########################################################
    # PNG 300 DPI
    ########################################################

    figure.savefig(
        str(output_base) + ".png",
        dpi=300,
        bbox_inches="tight"
    )

    ########################################################
    # Vector PDF
    ########################################################

    figure.savefig(
        str(output_base) + ".pdf",
        bbox_inches="tight"
    )

    plt.close(
        figure
    )


def main():

    args = parse_args()

    output_dir = Path(
        args.output
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    X, y, y_raw, encoder = load_data(
        args.features,
        args.labels
    )

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )










    ########################################################
    # Use the REAL held-out samples from nested CV
    ########################################################

    fold_dirs = sorted(

        Path(
            args.models_dir
        ).glob(
            "fold_*"
        ),

        key=lambda path:
            int(
                path.name.split("_")[-1]
            )
    )


    if not fold_dirs:

        raise ValueError(
            "No nested-CV fold "
            "directories found."
        )


    summary = []


    for fold_dir in fold_dirs:

        fold = int(
            fold_dir
            .name
            .split("_")[-1]
        )


        print(
            f"Visualization fold {fold}"
        )


        fold_output = (
            output_dir
            / f"fold_{fold}"
        )

        fold_output.mkdir(
            parents=True,
            exist_ok=True
        )


        ####################################################
        # Load the exact trained model for this fold
        ####################################################

        (
            extractor,
            scaler,
            microbiome_preprocessor,
            feature_names
        ) = load_fold(

            fold_dir,

            len(
                encoder.classes_
            ),

            device
        )


        ####################################################
        # Read the REAL held-out sample IDs
        ####################################################

        prediction_file = (
            fold_dir
            / "predictions.tsv"
        )


        if not prediction_file.exists():

            raise FileNotFoundError(
                f"Missing predictions file: "
                f"{prediction_file}"
            )


        prediction_df = pd.read_csv(
            prediction_file,
            sep="\t"
        )


        if "Sample" not in prediction_df.columns:

            raise ValueError(
                f"'Sample' column not found "
                f"in {prediction_file}"
            )


        test_ids = (
            prediction_df[
                "Sample"
            ]
            .astype(str)
            .tolist()
        )


        ####################################################
        # Validate sample IDs
        ####################################################

        missing_features = [
            sample
            for sample in test_ids
            if sample not in X.index
        ]


        if missing_features:

            raise ValueError(
                "Held-out samples missing "
                "from feature matrix: "
                f"{missing_features[:10]}"
            )


        missing_labels = [
            sample
            for sample in test_ids
            if sample not in y_raw.index
        ]


        if missing_labels:

            raise ValueError(
                "Held-out samples missing "
                "from label data: "
                f"{missing_labels[:10]}"
            )


        ####################################################
        # ONLY the true outer held-out samples
        ####################################################

        X_test_raw = (
            X.loc[
                test_ids
            ]
            .copy()
        )


        y_test_raw = (
            y_raw.loc[
                test_ids
            ]
            .copy()
        )











        ####################################################
        # SAVED fold-specific scaler
        ####################################################

        X_test_processed = (
            microbiome_preprocessor
            .transform(
                X_test_raw
            )
        )

        X_test_scaled = (
            scaler.transform(
                X_test_processed
            )
        )
        ####################################################
        # Latent representation
        ####################################################

        latent = extract_latent(
            extractor,
            X_test_scaled,
            device
        )

        latent_df = pd.DataFrame(

            latent,

            index=X_test_raw.index,

            columns=[
                f"Latent_{i + 1}"
                for i in range(
                    latent.shape[1]
                )
            ]
        )

        latent_df.insert(
            0,
            "TrueLabel",
            y_test_raw.values
        )

        latent_df.insert(
            0,
            "SampleID",
            X_test_raw.index
        )

        latent_df.to_csv(
            fold_output
            / "latent_features.tsv",
            sep="\t",
            index=False
        )

        latent_df.filter(
            like="Latent_"
        ).describe().T.to_csv(
            fold_output
            / "latent_statistics.tsv",
            sep="\t"
        )

        n_samples = len(
            X_test_raw
        )

        status = {

            "Fold": fold,

            "Samples": n_samples,
            "MicrobiomeFeatures":
                len(
                    feature_names
                ),

            "LatentDimensions":
                latent.shape[1],

            "tSNE": "skipped",

            "UMAP": "skipped"
        }

        ####################################################
        # Need enough samples
        ####################################################

        if n_samples >= 3:

            ################################################
            # t-SNE
            ################################################

            perplexity = min(
                float(
                    args.tsne_perplexity
                ),
                float(
                    n_samples - 1
                )
            )

            tsne_kwargs = dict(

                n_components=2,

                perplexity=perplexity,

                learning_rate="auto",

                init="pca",

                random_state=
                    args.seed + fold
            )

            try:

                tsne = TSNE(
                    **tsne_kwargs,
                    max_iter=
                        args.tsne_iterations
                )

            except TypeError:

                tsne = TSNE(
                    **tsne_kwargs,
                    n_iter=
                        args.tsne_iterations
                )

            tsne_embedding = (
                tsne.fit_transform(
                    latent
                )
            )

            tsne_df = pd.DataFrame({

                "SampleID":
                    X_test_raw.index,

                "TrueLabel":
                    y_test_raw.values,

                "TSNE1":
                    tsne_embedding[:, 0],

                "TSNE2":
                    tsne_embedding[:, 1]
            })

            tsne_df.to_csv(
                fold_output
                / "tsne_coordinates.tsv",
                sep="\t",
                index=False
            )

            save_scatter(

                tsne_df,

                "TSNE1",

                "TSNE2",

                "TrueLabel",

                (
                    "t-SNE latent space "
                    f"— outer fold {fold}"
                ),

                fold_output / "tsne"
            )

            status[
                "tSNE"
            ] = "generated"

            ################################################
            # UMAP
            ################################################

            neighbors = max(
                2,
                min(
                    args.umap_neighbors,
                    n_samples - 1
                )
            )

            reducer = umap.UMAP(

                n_components=2,

                n_neighbors=neighbors,

                min_dist=
                    args.umap_min_dist,

                metric="euclidean",

                random_state=
                    args.seed + fold
            )

            umap_embedding = (
                reducer.fit_transform(
                    latent
                )
            )

            umap_df = pd.DataFrame({

                "SampleID":
                    X_test_raw.index,

                "TrueLabel":
                    y_test_raw.values,

                "UMAP1":
                    umap_embedding[:, 0],

                "UMAP2":
                    umap_embedding[:, 1]
            })

            umap_df.to_csv(
                fold_output
                / "umap_coordinates.tsv",
                sep="\t",
                index=False
            )

            save_scatter(

                umap_df,

                "UMAP1",

                "UMAP2",

                "TrueLabel",

                (
                    "UMAP latent space "
                    f"— outer fold {fold}"
                ),

                fold_output / "umap"
            )

            status[
                "UMAP"
            ] = "generated"

        summary.append(
            status
        )

    ########################################################
    # Summary
    ########################################################

    pd.DataFrame(
        summary
    ).to_csv(

        output_dir
        / "visualization_status.tsv",

        sep="\t",

        index=False
    )

    with open(

        output_dir
        / "visualization_summary.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(

            {

                "outer_folds":
                    len(fold_dirs),

                "classes":
                    encoder.classes_.tolist(),

                "folds":
                    summary,

                "note":
                    (
                        "Each embedding uses only "
                        "outer held-out samples and "
                        "the corresponding fold model "
                        "and scaler."
                    )
            },

            handle,

            indent=2
        )


if __name__ == "__main__":
    main()