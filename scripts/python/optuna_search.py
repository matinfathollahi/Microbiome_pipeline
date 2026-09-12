#!/usr/bin/env python3

import argparse
import importlib.util
import json
from pathlib import Path

import numpy as np
import optuna
import pandas as pd

from optuna.samplers import TPESampler

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
)

from sklearn.preprocessing import LabelEncoder


def load_module(name, path):

    spec = importlib.util.spec_from_file_location(name, path)

    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module: {path}")

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


def read_tsv(path):

    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(path)

    return pd.read_csv(path, sep="\t")


def prepare_xy(df, label, feature_cols, encoder):

    missing = [
        c for c in [label, *feature_cols]
        if c not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns: {missing}"
        )

    X = df[feature_cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    if X.isna().any().any():

        bad = X.columns[
            X.isna().any()
        ].tolist()

        raise ValueError(
            f"Non-numeric or missing values in features: {bad[:10]}"
        )

    labels = df[label].astype(str)

    unknown = sorted(
        set(labels) - set(encoder.classes_)
    )

    if unknown:
        raise ValueError(
            f"Unknown labels encountered: {unknown}"
        )

    y = encoder.transform(labels)

    return X, y


def auc_score(y_true, probability):

    if probability.ndim != 2:
        raise ValueError(
            "predict_proba() must return a 2-D array"
        )

    n_classes = len(
        np.unique(y_true)
    )

    if n_classes == 2:

        if probability.shape[1] != 2:
            raise ValueError(
                "Binary classification requires two probability columns"
            )

        return roc_auc_score(
            y_true,
            probability[:, 1]
        )

    return roc_auc_score(
        y_true,
        probability,
        multi_class="ovr",
        average="weighted"
    )


def evaluate(y_true, y_pred, probability):

    return {

        "accuracy":
            accuracy_score(
                y_true,
                y_pred
            ),

        "balanced_accuracy":
            balanced_accuracy_score(
                y_true,
                y_pred
            ),

        "f1_weighted":
            f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

        "mcc":
            matthews_corrcoef(
                y_true,
                y_pred
            ),

        "roc_auc":
            auc_score(
                y_true,
                probability
            )
    }


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--nested",
        required=True
    )

    parser.add_argument(
        "--label",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=100
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=3600
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=2026
    )

    parser.add_argument(
        "--output",
        required=True
    )

    args = parser.parse_args()

    if args.trials < 1:
        raise ValueError(
            "--trials must be at least 1"
        )

    nested_dir = Path(
        args.nested
    )

    if not nested_dir.is_dir():
        raise FileNotFoundError(
            nested_dir
        )

    outdir = Path(
        args.output
    )

    outdir.mkdir(
        parents=True,
        exist_ok=True
    )

    script_dir = Path(
        __file__
    ).resolve().parent

    builders = load_module(
        "local_model_builders",
        script_dir / "optuna" / "builders.py"
    )

    spaces = load_module(
        "local_search_space",
        script_dir / "optuna" / "search_space.py"
    )

    model_builders = builders.MODEL_BUILDERS

    search_spaces = spaces.SEARCH_SPACE

    model_names = [
        model
        for model in model_builders
        if model in search_spaces
    ]

    if not model_names:
        raise RuntimeError(
            "No models found."
        )

    metadata_cols = {
        c.strip()
        for c in args.metadata.split(",")
        if c.strip()
    }

    metadata_cols.add(
        args.label
    )

    metadata_cols.add(
        "OriginalIndex"
    )

    outer_dirs = sorted(

        [
            p
            for p in nested_dir.glob("outer_fold_*")
            if p.is_dir()
        ],

        key=lambda p:
            int(
                p.name.rsplit("_", 1)[-1]
            )

    )

    if not outer_dirs:
        raise RuntimeError(
            f"No outer_fold directories found in {nested_dir}"
        )

    all_results = []

    for outer_pos, outer_dir in enumerate(
        outer_dirs,
        start=1
    ):

        outer_train = read_tsv(
            outer_dir / "outer_train.tsv"
        )

        outer_valid = read_tsv(
            outer_dir / "outer_valid.tsv"
        )

        if args.label not in outer_train.columns:
            raise ValueError(
                f"Label '{args.label}' not found."
            )

        encoder = LabelEncoder()

        encoder.fit(
            outer_train[
                args.label
            ].astype(str)
        )

        numeric_cols = outer_train.select_dtypes(
            include=[np.number]
        ).columns.tolist()

        feature_cols = [

            column

            for column in numeric_cols

            if column not in metadata_cols

        ]

        if not feature_cols:
            raise ValueError(
                f"No numeric features in {outer_dir}"
            )

        X_outer_train, y_outer_train = prepare_xy(

            outer_train,

            args.label,

            feature_cols,

            encoder

        )

        X_outer_valid, y_outer_valid = prepare_xy(

            outer_valid,

            args.label,

            feature_cols,

            encoder

        )

        inner_train_files = sorted(

            outer_dir.glob(
                "inner_train_*.tsv"
            ),

            key=lambda p:
                int(
                    p.stem.rsplit("_", 1)[-1]
                )

        )

        inner_valid_files = sorted(

            outer_dir.glob(
                "inner_valid_*.tsv"
            ),

            key=lambda p:
                int(
                    p.stem.rsplit("_", 1)[-1]
                )

        )

        if (
            not inner_train_files
            or len(inner_train_files)
            != len(inner_valid_files)
        ):

            raise RuntimeError(
                f"Incomplete inner folds in {outer_dir}"
            )

        inner_pairs = list(
            zip(
                inner_train_files,
                inner_valid_files
            )
        )

        for model_pos, model_name in enumerate(
            model_names,
            start=1
        ):

            print(
                f"Outer fold {outer_pos} | Model {model_name}"
            )

            model_out = (
                outdir
                / model_name
                / outer_dir.name
            )

            model_out.mkdir(
                parents=True,
                exist_ok=True
            )

            builder = model_builders[
                model_name
            ]

            search_space = search_spaces[
                model_name
            ]

            def objective(trial):

                params = search_space(
                    trial
                )

                scores = []

                for train_file, valid_file in inner_pairs:

                    inner_train = read_tsv(
                        train_file
                    )

                    inner_valid = read_tsv(
                        valid_file
                    )







                    inner_numeric_cols = (

                        inner_train

                        .select_dtypes(
                            include=[np.number]
                        )

                        .columns

                        .tolist()
                    )


                    inner_feature_cols = [

                        column

                        for column in inner_numeric_cols

                        if column not in metadata_cols
                    ]


                    if not inner_feature_cols:

                        raise ValueError(

                            f"No selected features found "
                            f"in {train_file}"

                        )


                    X_train, y_train = prepare_xy(

                        inner_train,

                        args.label,

                        inner_feature_cols,

                        encoder

                    )


                    X_valid, y_valid = prepare_xy(

                        inner_valid,

                        args.label,

                        inner_feature_cols,

                        encoder

                    )








                    try:

                        model = builder(
                            params,
                            args.seed
                        )

                        model.fit(
                            X_train,
                            y_train
                        )

                        probability = model.predict_proba(
                            X_valid
                        )

                        score = auc_score(
                            y_valid,
                            probability
                        )

                        scores.append(
                            score
                        )

                    except Exception as exc:

                        raise optuna.TrialPruned(
                            str(exc)
                        ) from exc

                return float(
                    np.mean(scores)
                )

            sampler_seed = (
                args.seed
                + outer_pos * 100
                + model_pos
            )

            study = optuna.create_study(

                direction="maximize",

                sampler=TPESampler(
                    seed=sampler_seed
                )

            )

            study.optimize(

                objective,

                n_trials=args.trials,

                timeout=(
                    None
                    if args.timeout <= 0
                    else args.timeout
                ),

                show_progress_bar=False

            )

            best_params = (
                study.best_params
            )

            with open(

                model_out
                / "best_params.json",

                "w",

                encoding="utf-8"

            ) as handle:

                json.dump(
                    best_params,
                    handle,
                    indent=2,
                    default=float
                )

            study.trials_dataframe().to_csv(

                model_out
                / "trials.tsv",

                sep="\t",

                index=False

            )

            final_model = builder(

                best_params,

                args.seed

            )

            final_model.fit(

                X_outer_train,

                y_outer_train

            )

            y_pred = final_model.predict(
                X_outer_valid
            )

            probability = final_model.predict_proba(
                X_outer_valid
            )

            metrics = evaluate(

                y_outer_valid,

                y_pred,

                probability

            )

            metrics.update({

                "model":
                    model_name,

                "outer_fold":
                    outer_pos,

                "best_inner_auc":
                    study.best_value,

                "n_features":
                    len(feature_cols),

                "n_train":
                    len(X_outer_train),

                "n_valid":
                    len(X_outer_valid)

            })

            all_results.append(
                metrics
            )

    results = pd.DataFrame(
        all_results
    )

    results.to_csv(

        outdir
        / "outer_fold_results.tsv",

        sep="\t",

        index=False

    )

    summary = (

        results

        .groupby("model")

        .agg(

            mean_roc_auc=(
                "roc_auc",
                "mean"
            ),

            sd_roc_auc=(
                "roc_auc",
                "std"
            ),

            mean_balanced_accuracy=(
                "balanced_accuracy",
                "mean"
            ),

            mean_f1_weighted=(
                "f1_weighted",
                "mean"
            ),

            mean_mcc=(
                "mcc",
                "mean"
            )

        )

        .reset_index()

        .sort_values(
            "mean_roc_auc",
            ascending=False
        )

    )

    summary.to_csv(

        outdir
        / "model_summary.tsv",

        sep="\t",

        index=False

    )

    best_model = (
        summary.iloc[0].to_dict()
    )

    with open(

        outdir
        / "best_model.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            best_model,
            handle,
            indent=2,
            default=float
        )

    print()
    print(
        f"Outer folds : {len(outer_dirs)}"
    )
    print(
        f"Models      : {', '.join(model_names)}"
    )
    print(
        f"Output      : {outdir}"
    )
    print(
        f"Best model  : {best_model['model']}"
    )
    print(
        f"Mean ROC-AUC: {best_model['mean_roc_auc']:.6f}"
    )


if __name__ == "__main__":
    main()