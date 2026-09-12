#!/usr/bin/env python3

import argparse
import importlib.util
import json
from pathlib import Path

import joblib
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

from sklearn.model_selection import StratifiedGroupKFold
from sklearn.preprocessing import LabelEncoder


def load_module(name, path):

    spec = importlib.util.spec_from_file_location(
        name,
        path
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Cannot load module: {path}"
        )

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


def read_tsv(path):

    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(path)

    return pd.read_csv(
        path,
        sep="\t"
    )


def auc_score(y_true, probability):

    if probability.ndim != 2:
        raise ValueError(
            "predict_proba() must return a 2-D array"
        )

    n_classes = len(
        np.unique(y_true)
    )

    if n_classes == 2:

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


def evaluate(
    y_true,
    y_pred,
    probability
):

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


def prepare_xy(
    df,
    label,
    feature_cols,
    encoder
):

    missing = [

        c
        for c in [label, *feature_cols]
        if c not in df.columns

    ]

    if missing:

        raise ValueError(
            f"Missing columns: {missing[:20]}"
        )

    X = df[
        feature_cols
    ].apply(
        pd.to_numeric,
        errors="coerce"
    )

    if X.isna().any().any():

        bad = X.columns[
            X.isna().any()
        ].tolist()

        raise ValueError(
            "Non-numeric or missing values "
            f"in features: {bad[:10]}"
        )

    labels = df[
        label
    ].astype(str)

    unknown = sorted(
        set(labels)
        - set(encoder.classes_)
    )

    if unknown:

        raise ValueError(
            f"Unknown labels encountered: {unknown}"
        )

    y = encoder.transform(
        labels
    )

    return X, y


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--train",
        required=True
    )

    parser.add_argument(
        "--test",
        required=True
    )

    parser.add_argument(
        "--features",
        required=True
    )

    parser.add_argument(
        "--best_model",
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
        "--group",
        required=True
    )

    parser.add_argument(
        "--cv",
        type=int,
        default=5
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


    if args.cv < 2:

        raise ValueError(
            "--cv must be at least 2"
        )


    if args.trials < 1:

        raise ValueError(
            "--trials must be at least 1"
        )


    outdir = Path(
        args.output
    )

    outdir.mkdir(
        parents=True,
        exist_ok=True
    )


    train = read_tsv(
        args.train
    )

    test = read_tsv(
        args.test
    )

    features_df = read_tsv(
        args.features
    )


    if "Feature" not in features_df.columns:

        raise ValueError(
            "Feature file must contain a "
            "'Feature' column"
        )


    feature_cols = (

        features_df[
            "Feature"
        ]

        .dropna()

        .astype(str)

        .tolist()

    )


    feature_cols = list(
        dict.fromkeys(
            feature_cols
        )
    )


    if not feature_cols:

        raise ValueError(
            "No consensus features were found"
        )


    with open(
        args.best_model,
        "r",
        encoding="utf-8"
    ) as handle:

        best_model_info = json.load(
            handle
        )


    model_name = best_model_info.get(
        "model"
    )


    if not model_name:

        raise ValueError(
            "best_model.json does not "
            "contain a 'model' field"
        )


    if args.label not in train.columns:

        raise ValueError(
            f"Label '{args.label}' "
            "not found in train data"
        )


    encoder = LabelEncoder()

    encoder.fit(
        train[
            args.label
        ].astype(str)
    )







    if args.group not in train.columns:

        raise ValueError(
            f"Group column '{args.group}' "
            "not found in train data"
        )


    if args.group not in test.columns:

        raise ValueError(
            f"Group column '{args.group}' "
            "not found in test data"
        )


    if train[args.group].isna().any():

        raise ValueError(
            f"Missing values in training group column "
            f"'{args.group}'"
        )


    if test[args.group].isna().any():

        raise ValueError(
            f"Missing values in test group column "
            f"'{args.group}'"
        )








    X_train, y_train = prepare_xy(

        train,
        args.label,
        feature_cols,
        encoder

    )


    X_test, y_test = prepare_xy(

        test,
        args.label,
        feature_cols,
        encoder

    )




    groups_train = (
        train[args.group]
        .astype(str)
        .reset_index(drop=True)
    )

    groups_test = (
        test[args.group]
        .astype(str)
        .reset_index(drop=True)
    )


    study_overlap = (
        set(groups_train.unique())
        &
        set(groups_test.unique())
    )


    if study_overlap:

        raise ValueError(
            "Train/test study leakage detected. "
            f"Overlapping studies: "
            f"{sorted(study_overlap)}"
        )


    groups_per_class = (

        pd.DataFrame({
            "Label": y_train,
            "Group": groups_train
        })

        .groupby(
            "Label"
        )[
            "Group"
        ]

        .nunique()
    )


    min_groups_per_class = int(
        groups_per_class.min()
    )


    effective_cv = min(

        args.cv,

        int(
            groups_train.nunique()
        ),

        min_groups_per_class
    )


    if effective_cv < 2:

        raise ValueError(

            "Study-aware final tuning is not possible "
            "because at least one class occurs in "
            "fewer than two studies. "

            f"Studies per class: "
            f"{groups_per_class.to_dict()}"
        )







    script_dir = Path(
        __file__
    ).resolve().parent


    builders = load_module(

        "local_model_builders",

        script_dir
        / "optuna"
        / "builders.py"

    )


    spaces = load_module(

        "local_search_space",

        script_dir
        / "optuna"
        / "search_space.py"

    )


    if (
        model_name
        not in builders.MODEL_BUILDERS
    ):

        raise ValueError(
            f"Unknown model: {model_name}"
        )


    if (
        model_name
        not in spaces.SEARCH_SPACE
    ):

        raise ValueError(
            f"No search space for: {model_name}"
        )


    builder = builders.MODEL_BUILDERS[
        model_name
    ]

    search_space = spaces.SEARCH_SPACE[
        model_name
    ]


    cv = StratifiedGroupKFold(

        n_splits=effective_cv,

        shuffle=True,

        random_state=args.seed
    )


    def objective(trial):

        params = search_space(
            trial
        )

        scores = []


        for (
            train_idx,
            valid_idx
        ) in cv.split(
            X_train,
            y_train,
            groups=groups_train
        ):

            model = builder(
                params,
                args.seed
            )


            model.fit(

                X_train.iloc[
                    train_idx
                ],

                y_train[
                    train_idx
                ]

            )


            probability = (
                model.predict_proba(

                    X_train.iloc[
                        valid_idx
                    ]

                )
            )


            score = auc_score(

                y_train[
                    valid_idx
                ],

                probability

            )


            scores.append(
                score
            )


        return float(
            np.mean(
                scores
            )
        )


    study = optuna.create_study(

        direction="maximize",

        sampler=TPESampler(
            seed=args.seed
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


    best_params = study.best_params


    with open(

        outdir
        / "final_best_params.json",

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

        outdir
        / "final_tuning_trials.tsv",

        sep="\t",

        index=False

    )


    final_model = builder(

        best_params,

        args.seed

    )


    final_model.fit(

        X_train,

        y_train

    )


    y_pred = final_model.predict(
        X_test
    )


    probability = (
        final_model.predict_proba(
            X_test
        )
    )


    metrics = evaluate(

        y_test,

        y_pred,

        probability

    )


    metrics.update({

        "model":
            model_name,

        "cv_best_roc_auc":
            study.best_value,

        "n_features":
            len(feature_cols),

        "n_train":
            len(X_train),

        "n_test":
            len(X_test)

    })


    pd.DataFrame(
        [metrics]
    ).to_csv(

        outdir
        / "final_test_metrics.tsv",

        sep="\t",

        index=False

    )


    predictions = pd.DataFrame()


    metadata_cols = [

        c.strip()

        for c in args.metadata.split(",")

        if (
            c.strip()
            and c.strip() in test.columns
        )

    ]


    for column in metadata_cols:

        predictions[
            column
        ] = test[
            column
        ].values


    predictions[
        "true_label"
    ] = encoder.inverse_transform(
        y_test
    )


    predictions[
        "predicted_label"
    ] = encoder.inverse_transform(
        y_pred
    )


    for (
        class_index,
        class_name
    ) in enumerate(
        encoder.classes_
    ):

        safe_name = (

            str(class_name)

            .replace(
                " ",
                "_"
            )

            .replace(
                "/",
                "_"
            )

        )


        predictions[
            f"probability_{safe_name}"
        ] = probability[
            :,
            class_index
        ]


    predictions.to_csv(

        outdir
        / "final_test_predictions.tsv",

        sep="\t",

        index=False

    )


    pd.DataFrame({

        "Feature":
            feature_cols

    }).to_csv(

        outdir
        / "final_features.tsv",

        sep="\t",

        index=False

    )


    with open(

        outdir
        / "label_classes.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(

            encoder.classes_.tolist(),

            handle,

            indent=2

        )


    joblib.dump(

        final_model,

        outdir
        / "final_model.joblib"

    )


    print(
        f"Selected model       : {model_name}"
    )

    print(
        f"Consensus features   : {len(feature_cols)}"
    )

    print(
        "Final CV best ROC-AUC: "
        f"{study.best_value:.6f}"
    )

    print(
        "Held-out ROC-AUC     : "
        f"{metrics['roc_auc']:.6f}"
    )

    print(
        "Held-out accuracy    : "
        f"{metrics['accuracy']:.6f}"
    )

    print(
        f"Output               : {outdir}"
    )


if __name__ == "__main__":

    main()