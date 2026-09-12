#!/usr/bin/env python3

import argparse
import json
import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
import shap

from captum.attr import IntegratedGradients


from microbiome_preprocessing import (
    MicrobiomeCLRPreprocessor
)
from sklearn.preprocessing import LabelEncoder

from deep_learning.models.mlp import build_mlp
from deep_learning.train import get_device


############################################################
# Arguments
############################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Fold-wise explainability for "
            "nested-CV deep learning models"
        )
    )

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
        "--background-size",
        type=int,
        default=100
    )

    parser.add_argument(
        "--max-explain-samples",
        type=int,
        default=200
    )

    parser.add_argument(
        "--ig-steps",
        type=int,
        default=50
    )

    parser.add_argument(
        "--permutation-repeats",
        type=int,
        default=5
    )

    parser.add_argument(
        "--permutation-max-features",
        type=int,
        default=100,
        help=(
            "0 = all features; otherwise top-N "
            "SHAP features are tested by permutation"
        )
    )

    parser.add_argument(
        "--top-features",
        type=int,
        default=30
    )

    return parser.parse_args()


############################################################
# Seed
############################################################

def set_seed(seed):

    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():

        torch.cuda.manual_seed_all(
            seed
        )


############################################################
# Input
############################################################

def read_inputs(
    features_file,
    labels_file
):

    X = pd.read_csv(
        features_file,
        sep="\t",
        index_col=0
    )

    y_df = pd.read_csv(
        labels_file,
        sep="\t",
        index_col=0
    )

    if y_df.shape[1] != 1:

        raise ValueError(
            "Labels file must contain "
            "exactly one label column."
        )

    y_raw = y_df.iloc[:, 0]

    if not X.index.equals(
        y_raw.index
    ):

        common = X.index.intersection(
            y_raw.index
        )

        if (
            len(common) != len(X)
            or len(common) != len(y_raw)
        ):

            raise ValueError(
                "Feature and label sample IDs "
                "do not match exactly."
            )

        y_raw = y_raw.loc[
            X.index
        ]

    if X.isna().any().any():

        raise ValueError(
            "Features contain missing values."
        )

    non_numeric = (
        X
        .select_dtypes(
            exclude=[np.number]
        )
        .columns
        .tolist()
    )

    if non_numeric:

        raise ValueError(
            "Non-numeric features found: "
            f"{non_numeric[:10]}"
        )

    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y_raw.astype(str)
    )

    y = pd.Series(
        y_encoded,
        index=y_raw.index
    )

    return (
        X,
        y,
        encoder
    )


############################################################
# Load model / scaler
############################################################

def load_fold_model(
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

    ########################################################
    # Required files
    ########################################################

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

    ########################################################
    # Load fold-specific microbiome preprocessor
    ########################################################

    microbiome_preprocessor = joblib.load(
        preprocessor_path
    )

    if not hasattr(
        microbiome_preprocessor,
        "selected_features_"
    ):

        raise ValueError(
            f"Preprocessor has no selected_features_: "
            f"{preprocessor_path}"
        )

    feature_names = list(
        microbiome_preprocessor
        .selected_features_
    )

    if not feature_names:

        raise ValueError(
            f"No selected features found in "
            f"{preprocessor_path}"
        )

    input_dim = len(
        feature_names
    )

    ########################################################
    # Parameters
    ########################################################

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

    ########################################################
    # Model
    ########################################################

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

    ########################################################
    # Fold-specific scaler
    ########################################################

    scaler = joblib.load(
        scaler_path
    )

    ########################################################
    # Consistency check
    ########################################################

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

    ########################################################
    # Return all fold-specific objects
    ########################################################

    return (

        model,

        scaler,

        microbiome_preprocessor,

        feature_names
    )

############################################################
# Prediction
############################################################

def predict_probabilities(
    model,
    X,
    device,
    batch_size=256
):

    probabilities = []

    with torch.no_grad():

        for start in range(
            0,
            len(X),
            batch_size
        ):

            batch = torch.as_tensor(

                X[
                    start:
                    start + batch_size
                ],

                dtype=torch.float32,

                device=device
            )

            logits = model(
                batch
            )

            prob = torch.softmax(
                logits,
                dim=1
            )

            probabilities.append(

                prob
                .cpu()
                .numpy()
            )

    return np.vstack(
        probabilities
    )


############################################################
# Normalize SHAP output
############################################################

def normalize_shap_output(
    values,
    n_samples,
    n_features,
    n_classes
):

    ########################################################
    # Older SHAP:
    # list[class] -> samples x features
    ########################################################

    if isinstance(
        values,
        list
    ):

        arrays = [

            np.asarray(value)

            for value in values
        ]

        output = np.stack(
            arrays,
            axis=0
        )

    ########################################################
    # Newer SHAP
    ########################################################

    else:

        array = np.asarray(
            values
        )

        if array.ndim == 2:

            output = array[
                None,
                :,
                :
            ]

        elif array.ndim == 3:

            if array.shape == (
                n_samples,
                n_features,
                n_classes
            ):

                output = np.moveaxis(
                    array,
                    -1,
                    0
                )

            elif array.shape == (
                n_classes,
                n_samples,
                n_features
            ):

                output = array

            elif array.shape == (
                n_samples,
                n_classes,
                n_features
            ):

                output = np.moveaxis(
                    array,
                    1,
                    0
                )

            else:

                raise ValueError(
                    "Unexpected SHAP shape: "
                    f"{array.shape}"
                )

        else:

            raise ValueError(
                "Unexpected SHAP dimensions: "
                f"{array.ndim}"
            )

    if (
        output.shape[1]
        != n_samples
        or
        output.shape[2]
        != n_features
    ):

        raise ValueError(
            "Normalized SHAP shape mismatch: "
            f"{output.shape}"
        )

    return output


############################################################
# SHAP
############################################################

def compute_shap(
    model,
    background,
    X_explain,
    device
):

    background_tensor = torch.as_tensor(

        background,

        dtype=torch.float32,

        device=device
    )

    explain_tensor = torch.as_tensor(

        X_explain,

        dtype=torch.float32,

        device=device
    )

    ########################################################
    # DeepExplainer first
    ########################################################

    try:

        explainer = shap.DeepExplainer(

            model,

            background_tensor
        )

        values = explainer.shap_values(
            explain_tensor
        )

    ########################################################
    # Fallback
    ########################################################

    except Exception:

        explainer = shap.GradientExplainer(

            model,

            background_tensor
        )

        values = explainer.shap_values(
            explain_tensor
        )

    return values


############################################################
# Integrated Gradients
############################################################

def compute_integrated_gradients(
    model,
    X,
    n_classes,
    device,
    n_steps
):

    inputs = torch.as_tensor(

        X,

        dtype=torch.float32,

        device=device
    )

    baseline = torch.zeros_like(
        inputs
    )

    ig = IntegratedGradients(
        model
    )

    all_attributions = []

    for class_id in range(
        n_classes
    ):

        attributions = ig.attribute(

            inputs,

            baselines=baseline,

            target=class_id,

            n_steps=n_steps,

            internal_batch_size=min(
                64,
                max(
                    1,
                    len(X)
                )
            )
        )

        all_attributions.append(

            attributions
            .detach()
            .cpu()
            .numpy()
        )

    return np.stack(
        all_attributions,
        axis=0
    )


############################################################
# Permutation Importance
############################################################

def compute_permutation_importance(
    model,
    X,
    y,
    feature_names,
    device,
    repeats,
    selected_features,
    seed
):

    baseline_prob = (
        predict_probabilities(
            model,
            X,
            device
        )
    )

    baseline_prediction = (
        baseline_prob.argmax(
            axis=1
        )
    )

    baseline_accuracy = float(

        np.mean(
            baseline_prediction == y
        )
    )

    rng = np.random.default_rng(
        seed
    )

    feature_to_index = {

        feature: index

        for index, feature
        in enumerate(
            feature_names
        )
    }

    rows = []

    for feature in selected_features:

        feature_index = (
            feature_to_index[
                feature
            ]
        )

        drops = []

        for repeat in range(
            repeats
        ):

            X_permuted = X.copy()

            X_permuted[
                :,
                feature_index
            ] = rng.permutation(

                X_permuted[
                    :,
                    feature_index
                ]
            )

            prediction = (
                predict_probabilities(

                    model,

                    X_permuted,

                    device

                )
                .argmax(
                    axis=1
                )
            )

            accuracy = float(

                np.mean(
                    prediction == y
                )
            )

            drops.append(

                baseline_accuracy
                - accuracy
            )

        rows.append({

            "Feature":
                feature,

            "Importance":
                float(
                    np.mean(drops)
                ),

            "ImportanceSD":
                float(
                    np.std(
                        drops,
                        ddof=1
                    )
                )
                if repeats > 1
                else 0.0,

            "BaselineAccuracy":
                baseline_accuracy
        })

    result = pd.DataFrame(
        rows
    )

    result = result.sort_values(

        "Importance",

        ascending=False
    )

    return result


############################################################
# Plot
############################################################

def plot_importance(
    dataframe,
    value_column,
    title,
    output_file,
    top_n
):

    if dataframe.empty:
        return

    plot_df = dataframe.nlargest(

        min(
            top_n,
            len(dataframe)
        ),

        value_column
    )

    plot_df = plot_df.sort_values(
        value_column
    )

    figure, axis = plt.subplots(

        figsize=(
            10,
            max(
                5,
                0.28 * len(plot_df) + 2
            )
        )
    )

    axis.barh(

        plot_df["Feature"],

        plot_df[
            value_column
        ]
    )

    axis.set_title(
        title
    )

    axis.set_xlabel(
        value_column
    )

    figure.tight_layout()

    figure.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"
    )

    plt.close(
        figure
    )


############################################################
# Aggregate folds
############################################################

def aggregate_method(
    files,
    method,
    output_dir,
    top_n
):

    frames = []

    for path in files:

        dataframe = pd.read_csv(

            path,

            sep="\t"
        )

        frames.append(

            dataframe[
                [
                    "Feature",
                    "Importance"
                ]
            ]
        )

    combined = pd.concat(

        frames,

        ignore_index=True
    )

    aggregated = (

        combined

        .groupby(
            "Feature"
        )["Importance"]

        .agg(
            [
                "mean",
                "std",
                "count"
            ]
        )

        .reset_index()
    )

    aggregated.columns = [

        "Feature",
        "Importance",
        "ImportanceSD",
        "Folds"
    ]

    aggregated[
        "SelectionFrequency"
    ] = (

        aggregated[
            "Folds"
        ]

        / len(
            files
        )
    )

    aggregated[
        "ImportanceSD"
    ] = aggregated[
        "ImportanceSD"
    ].fillna(
        0.0
    )

    aggregated = (
        aggregated
        .sort_values(
            "Importance",
            ascending=False
        )
    )

    output_path = (

        Path(output_dir)

        / (
            f"global_{method}"
            "_importance.tsv"
        )
    )

    aggregated.to_csv(

        output_path,

        sep="\t",

        index=False
    )

    plot_importance(

        aggregated,

        "Importance",

        (
            f"Global "
            f"{method.upper()} "
            "importance"
        ),

        Path(output_dir)
        / (
            f"global_{method}"
            "_importance.png"
        ),

        top_n
    )

    return aggregated


############################################################
# Main
############################################################

def main():

    args = parse_args()

    set_seed(
        args.seed
    )

    output_dir = Path(
        args.output
    )

    output_dir.mkdir(

        parents=True,

        exist_ok=True
    )

    ########################################################
    # Data
    ########################################################

    X, y, encoder = read_inputs(

        args.features,

        args.labels
    )

    n_classes = len(
        encoder.classes_
    )

    if n_classes < 2:

        raise ValueError(
            "At least two classes required."
        )

    ########################################################
    # Save class mapping
    ########################################################

    label_mapping = pd.DataFrame({

        "EncodedClass":
            range(
                n_classes
            ),

        "Label":
            encoder.classes_
    })

    label_mapping.to_csv(

        output_dir
        / "label_mapping.tsv",

        sep="\t",

        index=False
    )

    ########################################################
    # Same Outer CV as training
    ########################################################



    shap_files = []

    ig_files = []

    permutation_files = []

    local_rows = []

    fold_feature_counts = []

    device = get_device()

    ########################################################
    # Fold loop
    ########################################################

    ########################################################
    # Discover REAL nested-CV folds
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


    ########################################################
    # Process each REAL nested-CV fold
    ########################################################

    for fold_dir in fold_dirs:

        fold = int(
            fold_dir
            .name
            .split("_")[-1]
        )


        print(
            f"Explainability fold {fold}"
        )


        fold_seed = (
            args.seed
            + fold
        )










        fold_output = (

            output_dir

            / f"fold_{fold}"
        )

        fold_output.mkdir(

            parents=True,

            exist_ok=True
        )

        model_dir = fold_dir

        ####################################################
        # Model / scaler
        ####################################################

        (
            model,
            scaler,
            microbiome_preprocessor,
            feature_names
        ) = load_fold_model(

            model_dir,

            output_dim=n_classes,

            device=device
        )

        fold_feature_counts.append({

            "fold":
                fold,

            "features":
                len(
                    feature_names
                )
        })

        pd.DataFrame({

            "Feature":
                feature_names

        }).to_csv(

            fold_output
            / "model_features.tsv",

            sep="\t",

            index=False
        )

        ####################################################
        # Reconstruct REAL outer split from predictions
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


        test_id_set = set(
            test_ids
        )


        train_ids = [
            sample
            for sample in X.index
            if sample not in test_id_set
        ]


        missing_test_ids = [
            sample
            for sample in test_ids
            if sample not in X.index
        ]


        if missing_test_ids:

            raise ValueError(
                "Held-out sample IDs missing "
                "from feature matrix: "
                f"{missing_test_ids[:10]}"
            )


        X_outer_train_raw = (
            X.loc[
                train_ids
            ]
            .copy()
        )


        X_test_raw = (
            X.loc[
                test_ids
            ]
            .copy()
        )




        y_test = (
            y.loc[
                test_ids
            ]
            .to_numpy()
        )



        ####################################################
        # SHAP background candidates
        # ONLY from outer-training samples
        ####################################################

        X_background_raw = (
            X_outer_train_raw
            .copy()
        )

        ####################################################
        # IMPORTANT:
        # use SAVED fold-specific scaler
        ####################################################

####################################################
# APPLY SAVED fold-specific microbiome preprocessor
####################################################

        X_background_processed = (
            microbiome_preprocessor
            .transform(
                X_background_raw
            )
        )

        X_test_processed = (
            microbiome_preprocessor
            .transform(
                X_test_raw
            )
        )


####################################################
# APPLY SAVED scaler
####################################################

        X_background_scaled = (
            scaler.transform(
                X_background_processed
            )
        )

        X_test_scaled = (
            scaler.transform(
                X_test_processed
            )
        )








        rng = np.random.default_rng(
            fold_seed
        )

        ####################################################
        # SHAP background:
        # ONLY outer training samples
        ####################################################

        background_size = min(

            args.background_size,

            len(
                X_background_scaled
            )
        )

        background_indices = (
            rng.choice(

                len(
                    X_background_scaled
                ),

                size=background_size,

                replace=False
            )
        )

        background = (
            X_background_scaled[
                background_indices
            ]
        )

        ####################################################
        # Samples explained:
        # ONLY outer held-out test
        ####################################################

        if (
            args.max_explain_samples > 0
            and
            len(X_test_scaled)
            >
            args.max_explain_samples
        ):

            explain_indices = (
                np.sort(
                    rng.choice(

                        len(
                            X_test_scaled
                        ),

                        size=(
                            args
                            .max_explain_samples
                        ),

                        replace=False
                    )
                )
            )

        else:

            explain_indices = (
                np.arange(
                    len(
                        X_test_scaled
                    )
                )
            )

        X_explain = (
            X_test_scaled[
                explain_indices
            ]
        )

        y_explain = (
            y_test[
                explain_indices
            ]
        )

        sample_ids = (
            X_test_raw
            .index
            .to_numpy()[
                explain_indices
            ]
        )

        ####################################################
        # SHAP
        ####################################################

        shap_raw = compute_shap(

            model,

            background,

            X_explain,

            device
        )

        shap_values = (
            normalize_shap_output(

                shap_raw,

                len(
                    X_explain
                ),

                len(
                    feature_names
                ),

                n_classes
            )
        )

        shap_importance = (

            np.abs(
                shap_values
            )

            .mean(
                axis=(0, 1)
            )
        )

        shap_df = pd.DataFrame({

            "Feature":
                feature_names,

            "Importance":
                shap_importance
        })

        shap_df = shap_df.sort_values(

            "Importance",

            ascending=False
        )

        shap_path = (

            fold_output

            / "shap_importance.tsv"
        )

        shap_df.to_csv(

            shap_path,

            sep="\t",

            index=False
        )

        shap_files.append(
            shap_path
        )

        plot_importance(

            shap_df,

            "Importance",

            f"SHAP importance - fold {fold}",

            fold_output
            / "shap_importance.png",

            args.top_features
        )

        ####################################################
        # Local SHAP
        ####################################################

        predicted = (

            predict_probabilities(

                model,

                X_explain,

                device
            )

            .argmax(
                axis=1
            )
        )

        for sample_index, sample_id in enumerate(
            sample_ids
        ):

            target = int(
                predicted[
                    sample_index
                ]
            )

            class_index = min(

                target,

                shap_values.shape[0] - 1
            )

            values = (

                shap_values[
                    class_index,
                    sample_index
                ]
            )

            top_indices = (

                np.argsort(
                    np.abs(values)
                )[::-1]

                [
                    :args.top_features
                ]
            )

            for rank, feature_index in enumerate(

                top_indices,

                start=1
            ):

                local_rows.append({

                    "Fold":
                        fold,

                    "SampleID":
                        sample_id,

                    "PredictedClass":
                        target,

                    "PredictedLabel":
                        encoder.inverse_transform(
                            [target]
                        )[0],

                    "Rank":
                        rank,

                    "Feature":
                        feature_names[
                            feature_index
                        ],

                    "SHAP":
                        float(
                            values[
                                feature_index
                            ]
                        )
                })

        ####################################################
        # Integrated Gradients
        ####################################################

        ig_values = (
            compute_integrated_gradients(

                model,

                X_explain,

                n_classes,

                device,

                args.ig_steps
            )
        )

        ig_importance = (

            np.abs(
                ig_values
            )

            .mean(
                axis=(0, 1)
            )
        )

        ig_df = pd.DataFrame({

            "Feature":
                feature_names,

            "Importance":
                ig_importance
        })

        ig_df = ig_df.sort_values(

            "Importance",

            ascending=False
        )

        ig_path = (

            fold_output

            / (
                "integrated_gradients"
                "_importance.tsv"
            )
        )

        ig_df.to_csv(

            ig_path,

            sep="\t",

            index=False
        )

        ig_files.append(
            ig_path
        )

        plot_importance(

            ig_df,

            "Importance",

            (
                "Integrated Gradients "
                f"- fold {fold}"
            ),

            fold_output
            / (
                "integrated_gradients"
                "_importance.png"
            ),

            args.top_features
        )

        ####################################################
        # Permutation Importance
        ####################################################

        if (
            args.permutation_max_features
            == 0
        ):

            selected_features = (
                feature_names.copy()
            )

        else:

            selected_features = (

                shap_df

                .head(
                    args
                    .permutation_max_features
                )

                ["Feature"]

                .tolist()
            )

        permutation_df = (
            compute_permutation_importance(

                model,

                X_explain,

                y_explain,

                feature_names,

                device,

                args.permutation_repeats,

                selected_features,

                fold_seed
            )
        )

        permutation_path = (

            fold_output

            / "permutation_importance.tsv"
        )

        permutation_df.to_csv(

            permutation_path,

            sep="\t",

            index=False
        )

        permutation_files.append(
            permutation_path
        )

        plot_importance(

            permutation_df,

            "Importance",

            (
                "Permutation importance "
                f"- fold {fold}"
            ),

            fold_output
            / "permutation_importance.png",

            args.top_features
        )

        ####################################################
        # Samples explained
        ####################################################

        samples_df = pd.DataFrame({

            "SampleID":
                sample_ids,

            "TrueClass":
                y_explain,

            "PredictedClass":
                predicted
        })

        samples_df.to_csv(

            fold_output
            / "explained_samples.tsv",

            sep="\t",

            index=False
        )

    ########################################################
    # Aggregate folds
    ########################################################

    shap_global = aggregate_method(

        shap_files,

        "shap",

        output_dir,

        args.top_features
    )

    ig_global = aggregate_method(

        ig_files,

        "ig",

        output_dir,

        args.top_features
    )

    permutation_global = aggregate_method(

        permutation_files,

        "permutation",

        output_dir,

        args.top_features
    )

    ########################################################
    # Consensus
    ########################################################

    consensus = (

        shap_global[
            [
                "Feature",
                "Importance"
            ]
        ]

        .rename(
            columns={
                "Importance":
                    "SHAP"
            }
        )
    )

    consensus = consensus.merge(

        ig_global[
            [
                "Feature",
                "Importance"
            ]
        ].rename(
            columns={
                "Importance":
                    "IG"
            }
        ),

        on="Feature",

        how="outer"
    )

    consensus = consensus.merge(

        permutation_global[
            [
                "Feature",
                "Importance"
            ]
        ].rename(
            columns={
                "Importance":
                    "Permutation"
            }
        ),

        on="Feature",

        how="outer"
    )

    consensus = consensus.fillna(
        0.0
    )


    selection_frequency = (

        shap_global[
            [
                "Feature",
                "SelectionFrequency"
            ]
        ]
        .copy()
    )

    consensus = consensus.merge(

        selection_frequency,

        on="Feature",

        how="left"
    )

    consensus[
        "SelectionFrequency"
    ] = (

        consensus[
            "SelectionFrequency"
        ]
        .fillna(
            0.0
        )
    )

    ########################################################
    # Normalize methods
    ########################################################

    for column in [
        "SHAP",
        "IG",
        "Permutation"
    ]:

        maximum = (
            consensus[column]
            .abs()
            .max()
        )

        if maximum > 0:

            consensus[
                f"{column}_Normalized"
            ] = (

                consensus[column]

                / maximum
            )

        else:

            consensus[
                f"{column}_Normalized"
            ] = 0.0

    consensus[
        "RawConsensusScore"
    ] = (

        consensus[
            [
                "SHAP_Normalized",
                "IG_Normalized",
                "Permutation_Normalized"
            ]
        ]

        .mean(
            axis=1
        )
    )

    consensus[
        "ConsensusScore"
    ] = (

        consensus[
            "RawConsensusScore"
        ]

        *

        consensus[
            "SelectionFrequency"
        ]
    )



    consensus = consensus.sort_values(

        "ConsensusScore",

        ascending=False
    )

    consensus.to_csv(

        output_dir
        / "consensus_importance.tsv",

        sep="\t",

        index=False
    )

    ########################################################
    # Consensus plot
    ########################################################

    plot_df = consensus.rename(

        columns={
            "ConsensusScore":
                "Importance"
        }
    )

    plot_importance(

        plot_df,

        "Importance",

        "Consensus explainability ranking",

        output_dir
        / "consensus_importance.png",

        args.top_features
    )

    ########################################################
    # Local explanations
    ########################################################

    pd.DataFrame(
        local_rows
    ).to_csv(

        output_dir
        / "local_shap_explanations.tsv",

        sep="\t",

        index=False
    )

    ########################################################
    # Summary
    ########################################################

    summary = {

        "outer_folds":
            len(fold_dirs),

        "classes":
            encoder.classes_.tolist(),

        "raw_features":
            int(
                X.shape[1]
            ),

        "fold_filtered_features":
            fold_feature_counts,

        "minimum_filtered_features":
            int(
                min(
                    item["features"]
                    for item
                    in fold_feature_counts
                )
            ),

        "maximum_filtered_features":
            int(
                max(
                    item["features"]
                    for item
                    in fold_feature_counts
                )
            ),

        "methods": [
            "SHAP",
            "IntegratedGradients",
            "PermutationImportance"
        ],

        "permutation_max_features":
            args.permutation_max_features,

        "note": (
            "Each fold explains only its outer "
            "held-out samples using that fold's "
            "saved microbiome preprocessor, "
            "saved scaler, and trained model. "
            "SHAP background samples are drawn only "
            "from the corresponding outer-training samples."
        )
    }






    with open(

        output_dir
        / "explainability_summary.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(

            summary,

            handle,

            indent=4
        )

    print(
        "Explainability completed successfully."
    )


if __name__ == "__main__":

    main()