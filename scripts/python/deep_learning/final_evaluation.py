#!/usr/bin/env python3

import argparse
import json
import random
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import optuna
import pandas as pd
import torch
import torch.nn as nn

from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from sklearn.model_selection import (
    GroupShuffleSplit
)

from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler,
    label_binarize
)

from torch.utils.data import DataLoader

from deep_learning.dataset import MicrobiomeDataset
from deep_learning.early_stopping import EarlyStopping
from deep_learning.models.mlp import build_mlp
from deep_learning.nested_cv import inner_cv_objective

from deep_learning.train import (
    fit,
    get_device,
    predict,
    predict_proba
)

from microbiome_preprocessing import (
    MicrobiomeCLRPreprocessor
)

############################################################
# Arguments
############################################################

def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Final held-out evaluation "
            "for the deep-learning model."
        )
    )

    parser.add_argument(
        "--train",
        required=True
    )

    parser.add_argument(
        "--test",
        required=True
    )

    parser.add_argument(
        "--metadata",
        required=True
    )

    parser.add_argument(
        "--label",
        required=True
    )

    parser.add_argument(
        "--group",
        required=True
    )

    parser.add_argument(
        "--output",
        required=True
    )

    parser.add_argument(
        "--inner-folds",
        type=int,
        default=5
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=100
    )

    parser.add_argument(
        "--validation-fraction",
        type=float,
        default=0.10
    )

    parser.add_argument(
        "--max-epochs",
        type=int,
        default=200
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=2026
    )

    parser.add_argument(
        "--min-count",
        type=float,
        required=True
    )

    parser.add_argument(
        "--prevalence",
        type=float,
        required=True
    )

    parser.add_argument(
        "--zero-fraction",
        type=float,
        default=0.5
    )

    parser.add_argument(
        "--analysis-mode",
        choices=[
            "primary_inductive",
            "transductive_sensitivity"
        ],
        default="primary_inductive",
        help=(
            "Primary inductive analysis or "
            "transductive MMUPHin sensitivity analysis."
        )
    )

    return parser.parse_args()


############################################################
# Reproducibility
############################################################

def set_seed(seed):

    random.seed(seed)

    np.random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():

        torch.cuda.manual_seed_all(seed)

        torch.backends.cudnn.deterministic = True

        torch.backends.cudnn.benchmark = False


############################################################
# Read Train / Test
############################################################

def extract_xy(
    path,
    metadata_columns,
    label
):

    data = pd.read_csv(
        path,
        sep="\t"
    )

    if "SampleID" not in data.columns:

        raise ValueError(
            f"SampleID not found in {path}"
        )

    if label not in data.columns:

        raise ValueError(
            f"Label column '{label}' "
            f"not found in {path}"
        )

    if data["SampleID"].duplicated().any():

        raise ValueError(
            f"Duplicated SampleID values in {path}"
        )

    feature_columns = [

        column

        for column in data.columns

        if column not in metadata_columns
    ]

    if not feature_columns:

        raise ValueError(
            f"No microbiome features found in {path}"
        )

    non_numeric = (

        data[
            feature_columns
        ]

        .select_dtypes(
            exclude="number"
        )

        .columns

        .tolist()
    )

    if non_numeric:

        raise ValueError(

            f"Non-numeric features in {path}: "
            f"{non_numeric[:10]}"
        )

    X = (

        data[
            ["SampleID"] + feature_columns
        ]

        .set_index(
            "SampleID"
        )
    )

    y = (

        data[
            ["SampleID", label]
        ]

        .set_index(
            "SampleID"
        )[label]
    )

    if X.isna().any().any():

        raise ValueError(
            f"Missing feature values in {path}"
        )

    if y.isna().any():

        raise ValueError(
            f"Missing labels in {path}"
        )

    return (
        X,
        y.astype(str)
    )


############################################################
# Optimizer
############################################################

def build_optimizer(
    model,
    params
):

    common = {

        "lr":
            params[
                "learning_rate"
            ],

        "weight_decay":
            params[
                "weight_decay"
            ]
    }

    if params["optimizer"] == "Adam":

        return torch.optim.Adam(
            model.parameters(),
            **common
        )

    if params["optimizer"] == "AdamW":

        return torch.optim.AdamW(
            model.parameters(),
            **common
        )

    if params["optimizer"] == "RMSprop":

        return torch.optim.RMSprop(
            model.parameters(),
            **common
        )

    raise ValueError(
        f"Unknown optimizer: "
        f"{params['optimizer']}"
    )


############################################################
# Scheduler
############################################################

def build_scheduler(
    optimizer,
    params
):

    name = params.get(
        "scheduler",
        "None"
    )

    if name == "Plateau":

        return (
            torch.optim.lr_scheduler
            .ReduceLROnPlateau(

                optimizer,

                mode="min",

                patience=5
            )
        )

    if name == "Cosine":

        return (
            torch.optim.lr_scheduler
            .CosineAnnealingLR(

                optimizer,

                T_max=200
            )
        )

    if name == "Step":

        return (
            torch.optim.lr_scheduler
            .StepLR(

                optimizer,

                step_size=
                    params["step_size"],

                gamma=
                    params["gamma"]
            )
        )

    if name in (
        None,
        "None"
    ):

        return None

    raise ValueError(
        f"Unknown scheduler: {name}"
    )


############################################################
# Metrics
############################################################

def calculate_metrics(
    y_true,
    y_pred,
    y_prob,
    n_classes
):

    y_true = np.asarray(
        y_true,
        dtype=int
    )

    y_pred = np.asarray(
        y_pred,
        dtype=int
    )

    y_prob = np.asarray(
        y_prob,
        dtype=float
    )

    metrics = {

        "Accuracy":
            accuracy_score(
                y_true,
                y_pred
            ),

        "BalancedAccuracy":
            balanced_accuracy_score(
                y_true,
                y_pred
            ),

        "Precision":
            precision_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

        "Recall":
            recall_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

        "F1":
            f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

        "F1_macro":
            f1_score(
                y_true,
                y_pred,
                average="macro",
                zero_division=0
            ),

        "MCC":
            matthews_corrcoef(
                y_true,
                y_pred
            )
    }

    labels = np.arange(
        n_classes
    )

    cm = confusion_matrix(

        y_true,

        y_pred,

        labels=labels
    )

    ########################################################
    # Binary
    ########################################################

    if n_classes == 2:

        tn, fp, fn, tp = cm.ravel()

        metrics[
            "Sensitivity"
        ] = (

            tp / (tp + fn)

            if (tp + fn)

            else 0.0
        )

        metrics[
            "Specificity"
        ] = (

            tn / (tn + fp)

            if (tn + fp)

            else 0.0
        )

        try:

            metrics[
                "ROC_AUC"
            ] = roc_auc_score(

                y_true,

                y_prob[:, 1]
            )

        except ValueError:

            metrics[
                "ROC_AUC"
            ] = np.nan

        try:

            metrics[
                "PR_AUC"
            ] = average_precision_score(

                y_true,

                y_prob[:, 1]
            )

        except ValueError:

            metrics[
                "PR_AUC"
            ] = np.nan

    ########################################################
    # Multiclass
    ########################################################

    else:

        y_bin = label_binarize(

            y_true,

            classes=labels
        )

        try:

            metrics[
                "ROC_AUC"
            ] = roc_auc_score(

                y_bin,

                y_prob,

                multi_class="ovr",

                average="weighted"
            )

        except ValueError:

            metrics[
                "ROC_AUC"
            ] = np.nan

        try:

            metrics[
                "PR_AUC"
            ] = average_precision_score(

                y_bin,

                y_prob,

                average="weighted"
            )

        except ValueError:

            metrics[
                "PR_AUC"
            ] = np.nan

    return (
        metrics,
        cm
    )


############################################################
# Confusion Matrix
############################################################

def save_confusion_matrix(
    cm,
    class_names,
    output_dir
):

    table = pd.DataFrame(

        cm,

        index=class_names,

        columns=class_names
    )

    table.index.name = (
        "TrueLabel"
    )

    table.columns.name = (
        "PredictedLabel"
    )

    table.to_csv(

        output_dir
        / "confusion_matrix.tsv",

        sep="\t"
    )

    figure, axis = plt.subplots(
        figsize=(7, 6)
    )

    image = axis.imshow(
        cm,
        interpolation="nearest"
    )

    figure.colorbar(
        image,
        ax=axis
    )

    axis.set_xticks(
        np.arange(
            len(class_names)
        )
    )

    axis.set_yticks(
        np.arange(
            len(class_names)
        )
    )

    axis.set_xticklabels(
        class_names,
        rotation=45,
        ha="right"
    )

    axis.set_yticklabels(
        class_names
    )

    axis.set_xlabel(
        "Predicted label"
    )

    axis.set_ylabel(
        "True label"
    )

    axis.set_title(
        "Final held-out test confusion matrix"
    )

    threshold = (

        cm.max() / 2

        if cm.size
        and cm.max() > 0

        else 0
    )

    for i in range(
        cm.shape[0]
    ):

        for j in range(
            cm.shape[1]
        ):

            axis.text(

                j,
                i,

                str(
                    cm[i, j]
                ),

                ha="center",

                va="center",

                color=(
                    "white"

                    if cm[i, j]
                    > threshold

                    else "black"
                )
            )

    figure.tight_layout()

    figure.savefig(

        output_dir
        / "confusion_matrix.png",

        dpi=300,

        bbox_inches="tight"
    )

    figure.savefig(

        output_dir
        / "confusion_matrix.pdf",

        bbox_inches="tight"
    )

    plt.close(
        figure
    )


############################################################
# ROC + PR
############################################################

def save_roc_pr(
    y_true,
    y_prob,
    class_names,
    output_dir
):

    y_true = np.asarray(
        y_true,
        dtype=int
    )

    n_classes = len(
        class_names
    )

    labels = np.arange(
        n_classes
    )

    roc_rows = []

    pr_rows = []

    fig_roc, ax_roc = plt.subplots(
        figsize=(7, 6)
    )

    fig_pr, ax_pr = plt.subplots(
        figsize=(7, 6)
    )

    ########################################################
    # Binary
    ########################################################

    if n_classes == 2:

        if len(
            np.unique(
                y_true
            )
        ) == 2:

            fpr, tpr, thresholds = roc_curve(

                y_true,

                y_prob[:, 1]
            )

            auc_value = roc_auc_score(

                y_true,

                y_prob[:, 1]
            )

            ax_roc.plot(

                fpr,

                tpr,

                label=(
                    f"AUC = "
                    f"{auc_value:.3f}"
                )
            )

            for a, b, c in zip(
                fpr,
                tpr,
                thresholds
            ):

                roc_rows.append({

                    "Class":
                        class_names[1],

                    "FPR":
                        a,

                    "TPR":
                        b,

                    "Threshold":
                        c
                })

            precision, recall, threshold_pr = (
                precision_recall_curve(

                    y_true,

                    y_prob[:, 1]
                )
            )

            ap_value = average_precision_score(

                y_true,

                y_prob[:, 1]
            )

            ax_pr.plot(

                recall,

                precision,

                label=(
                    f"AP = "
                    f"{ap_value:.3f}"
                )
            )

            threshold_pr = np.append(
                threshold_pr,
                np.nan
            )

            for a, b, c in zip(
                recall,
                precision,
                threshold_pr
            ):

                pr_rows.append({

                    "Class":
                        class_names[1],

                    "Recall":
                        a,

                    "Precision":
                        b,

                    "Threshold":
                        c
                })

    ########################################################
    # Multiclass
    ########################################################

    else:

        y_bin = label_binarize(

            y_true,

            classes=labels
        )

        for class_id, class_name in enumerate(
            class_names
        ):

            target = y_bin[
                :,
                class_id
            ]

            if len(
                np.unique(
                    target
                )
            ) < 2:

                continue

            fpr, tpr, thresholds = roc_curve(

                target,

                y_prob[
                    :,
                    class_id
                ]
            )

            auc_value = roc_auc_score(

                target,

                y_prob[
                    :,
                    class_id
                ]
            )

            ax_roc.plot(

                fpr,

                tpr,

                label=(
                    f"{class_name}: "
                    f"{auc_value:.3f}"
                )
            )

            for a, b, c in zip(
                fpr,
                tpr,
                thresholds
            ):

                roc_rows.append({

                    "Class":
                        class_name,

                    "FPR":
                        a,

                    "TPR":
                        b,

                    "Threshold":
                        c
                })

            precision, recall, threshold_pr = (
                precision_recall_curve(

                    target,

                    y_prob[
                        :,
                        class_id
                    ]
                )
            )

            ap_value = average_precision_score(

                target,

                y_prob[
                    :,
                    class_id
                ]
            )

            ax_pr.plot(

                recall,

                precision,

                label=(
                    f"{class_name}: "
                    f"{ap_value:.3f}"
                )
            )

            threshold_pr = np.append(
                threshold_pr,
                np.nan
            )

            for a, b, c in zip(
                recall,
                precision,
                threshold_pr
            ):

                pr_rows.append({

                    "Class":
                        class_name,

                    "Recall":
                        a,

                    "Precision":
                        b,

                    "Threshold":
                        c
                })

    ########################################################
    # ROC plot
    ########################################################

    ax_roc.plot(
        [0, 1],
        [0, 1],
        linestyle="--"
    )

    ax_roc.set_xlabel(
        "False positive rate"
    )

    ax_roc.set_ylabel(
        "True positive rate"
    )

    ax_roc.set_title(
        "Final held-out test ROC"
    )

    ax_roc.legend(
        frameon=False
    )

    fig_roc.tight_layout()

    fig_roc.savefig(

        output_dir
        / "roc_curve.png",

        dpi=300,

        bbox_inches="tight"
    )

    fig_roc.savefig(

        output_dir
        / "roc_curve.pdf",

        bbox_inches="tight"
    )

    plt.close(
        fig_roc
    )

    ########################################################
    # PR plot
    ########################################################

    ax_pr.set_xlabel(
        "Recall"
    )

    ax_pr.set_ylabel(
        "Precision"
    )

    ax_pr.set_title(
        "Final held-out test precision-recall curve"
    )

    ax_pr.legend(
        frameon=False
    )

    fig_pr.tight_layout()

    fig_pr.savefig(

        output_dir
        / "pr_curve.png",

        dpi=300,

        bbox_inches="tight"
    )

    fig_pr.savefig(

        output_dir
        / "pr_curve.pdf",

        bbox_inches="tight"
    )

    plt.close(
        fig_pr
    )

    pd.DataFrame(

        roc_rows,

        columns=[
            "Class",
            "FPR",
            "TPR",
            "Threshold"
        ]

    ).to_csv(

        output_dir
        / "roc_curve.tsv",

        sep="\t",

        index=False
    )

    pd.DataFrame(

        pr_rows,

        columns=[
            "Class",
            "Recall",
            "Precision",
            "Threshold"
        ]

    ).to_csv(

        output_dir
        / "pr_curve.tsv",

        sep="\t",

        index=False
    )


############################################################
# History
############################################################

def save_history(
    history,
    output_dir
):

    history_df = pd.DataFrame(
        history
    )

    history_df.insert(

        0,

        "Epoch",

        np.arange(
            1,
            len(history_df) + 1
        )
    )

    history_df.to_csv(

        output_dir
        / "training_history.tsv",

        sep="\t",

        index=False
    )

    figure, axis = plt.subplots(
        figsize=(8, 6)
    )

    axis.plot(

        history_df[
            "Epoch"
        ],

        history_df[
            "train_auc"
        ],

        label="Train ROC-AUC"
    )

    axis.plot(

        history_df[
            "Epoch"
        ],

        history_df[
            "valid_auc"
        ],

        label="Validation ROC-AUC"
    )

    axis.set_xlabel(
        "Epoch"
    )

    axis.set_ylabel(
        "ROC-AUC"
    )

    axis.set_title(
        "Final DL training history"
    )

    axis.legend(
        frameon=False
    )

    figure.tight_layout()

    figure.savefig(

        output_dir
        / "training_history.png",

        dpi=300,

        bbox_inches="tight"
    )

    figure.savefig(

        output_dir
        / "training_history.pdf",

        bbox_inches="tight"
    )

    plt.close(
        figure
    )



############################################################
# Study-aware final validation split
############################################################

def study_aware_validation_split(
    X,
    y,
    groups,
    validation_fraction,
    seed,
    n_candidates=500
):

    if not (
        0.0
        <
        validation_fraction
        <
        1.0
    ):

        raise ValueError(
            "validation_fraction must be between 0 and 1."
        )


    if not (
        X.index.equals(y.index)
        and
        X.index.equals(groups.index)
    ):

        raise ValueError(
            "X, y and groups are not aligned."
        )


    all_classes = set(
        y.unique()
    )


    splitter = GroupShuffleSplit(

        n_splits=n_candidates,

        test_size=
            validation_fraction,

        random_state=seed
    )


    best_split = None


    for (
        train_idx,
        valid_idx
    ) in splitter.split(

        X,

        y,

        groups=groups
    ):

        train_classes = set(
            y.iloc[
                train_idx
            ].unique()
        )

        valid_classes = set(
            y.iloc[
                valid_idx
            ].unique()
        )


        if (
            train_classes != all_classes
            or
            valid_classes != all_classes
        ):

            continue


        train_groups = set(
            groups.iloc[
                train_idx
            ].unique()
        )

        valid_groups = set(
            groups.iloc[
                valid_idx
            ].unique()
        )


        overlap = (
            train_groups
            &
            valid_groups
        )


        if overlap:

            raise RuntimeError(
                "Study leakage detected in "
                "final validation split."
            )


        achieved_fraction = (

            len(valid_idx)
            /
            len(X)
        )


        fraction_error = abs(

            achieved_fraction
            -
            validation_fraction
        )


        if (
            best_split is None
            or
            fraction_error
            <
            best_split[0]
        ):

            best_split = (

                fraction_error,

                train_idx,

                valid_idx,

                achieved_fraction
            )


    if best_split is None:

        raise ValueError(
            "Could not construct a study-aware "
            "validation split containing all "
            "classes in both training and "
            "validation partitions."
        )


    (
        _,
        train_idx,
        valid_idx,
        achieved_fraction
    ) = best_split


    return (
        train_idx,
        valid_idx,
        achieved_fraction
    )


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
    # Metadata columns
    ########################################################

    metadata = pd.read_csv(

        args.metadata,

        sep="\t"
    )

    metadata_columns = set(
        metadata.columns
    )


    required_metadata_columns = {
        "SampleID",
        args.group
    }


    missing_metadata_columns = (

        required_metadata_columns
        -
        set(metadata.columns)
    )


    if missing_metadata_columns:

        raise ValueError(
            "Missing metadata columns required for "
            "study-aware final evaluation: "
            f"{sorted(missing_metadata_columns)}"
        )


    if metadata["SampleID"].duplicated().any():

        raise ValueError(
            "Duplicated SampleID values in metadata."
        )


    metadata_indexed = (
        metadata
        .set_index("SampleID")
    )




    ########################################################
    # Load train/test
    ########################################################

    X_train, y_train_raw = extract_xy(

        args.train,

        metadata_columns,

        args.label
    )

    X_test, y_test_raw = extract_xy(

        args.test,

        metadata_columns,

        args.label
    )

    ########################################################
    # Exact same features
    ########################################################

    if list(
        X_train.columns
    ) != list(
        X_test.columns
    ):

        raise ValueError(
            "Train and test feature columns "
            "are not identical."
        )














########################################################
# No sample overlap
########################################################

    overlap = set(
        X_train.index
    ).intersection(
        set(
            X_test.index
        )
    )

    if overlap:

        raise ValueError(
            "Train and held-out test contain "
            "overlapping SampleID values."
        )


########################################################
# Study / group metadata
########################################################

    if args.group not in metadata.columns:

        raise ValueError(
            f"Group column '{args.group}' "
            "not found in metadata."
        )


    if metadata["SampleID"].duplicated().any():

        raise ValueError(
            "Duplicated SampleID values in metadata."
        )


    metadata_indexed = (
        metadata
        .set_index("SampleID")
    )


    missing_train_metadata = (
        set(X_train.index)
        -
        set(metadata_indexed.index)
    )

    missing_test_metadata = (
        set(X_test.index)
        -
        set(metadata_indexed.index)
    )


    if (
        missing_train_metadata
        or
        missing_test_metadata
    ):

        raise ValueError(
            "Some train/test samples are missing "
            "from metadata."
        )




    groups_train = (
        metadata_indexed
        .loc[
            X_train.index,
            args.group
        ]
        .copy()
    )

    groups_test = (
        metadata_indexed
        .loc[
            X_test.index,
            args.group
        ]
        .copy()
    )


    if groups_train.isna().any():

        raise ValueError(
            f"Missing values in training "
            f"group column '{args.group}'."
        )


    if groups_test.isna().any():

        raise ValueError(
            f"Missing values in test "
            f"group column '{args.group}'."
        )


    groups_train = (
        groups_train
        .astype(str)
    )


    groups_test = (
        groups_test
        .astype(str)
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


########################################################
# Encode labels using TRAIN only
########################################################

    encoder = LabelEncoder()









    y_train = pd.Series(

        encoder.fit_transform(
            y_train_raw
        ),

        index=y_train_raw.index
    )

    unknown_test_labels = sorted(

        set(
            y_test_raw
        )

        -

        set(
            encoder.classes_
        )
    )

    if unknown_test_labels:

        raise ValueError(

            "Held-out test contains unseen labels: "

            f"{unknown_test_labels}"
        )

    class_to_id = {

        label: index

        for index, label in enumerate(
            encoder.classes_
        )
    }

    y_test = pd.Series(

        [
            class_to_id[label]

            for label in y_test_raw
        ],

        index=y_test_raw.index,

        dtype=int
    )

    n_classes = len(
        encoder.classes_
    )

    if n_classes < 2:

        raise ValueError(
            "At least two classes are required."
        )

########################################################
# Validate study-aware inner CV
########################################################

    group_class_table = pd.DataFrame({

        "Class":
            y_train.to_numpy(),

        "Study":
            groups_train.to_numpy()
    })


    studies_per_class = (

        group_class_table

        .groupby(
            "Class"
        )[
            "Study"
        ]

        .nunique()
    )


    minimum_studies_per_class = int(
        studies_per_class.min()
    )


    total_training_studies = int(
        groups_train.nunique()
    )


    effective_inner_folds = min(

        args.inner_folds,

        total_training_studies,

        minimum_studies_per_class
    )


    if effective_inner_folds < 2:

        raise ValueError(

            "Study-aware inner CV is impossible. "
            "Each class must occur in at least "
            "two independent studies. "

            f"Studies per class: "
            f"{studies_per_class.to_dict()}"
        )
    ########################################################
    # Label mapping
    ########################################################

    pd.DataFrame({

        "EncodedClass":
            np.arange(
                n_classes
            ),

        "Label":
            encoder.classes_

    }).to_csv(

        output_dir
        / "label_mapping.tsv",

        sep="\t",

        index=False
    )

    ########################################################
    # Device
    ########################################################

    device = get_device()

    ########################################################
    # FINAL hyperparameter optimization
    #
    # IMPORTANT:
    # uses TRAIN only
    ########################################################

    study = optuna.create_study(

        study_name=
            "Final_Heldout_DL_Tuning",

        direction=
            "maximize",

        sampler=
            optuna.samplers.TPESampler(

                seed=args.seed,

                multivariate=True
            ),

        pruner=
            optuna.pruners.MedianPruner(

                n_startup_trials=10,

                n_warmup_steps=1
            )
    )

    study.optimize(

        lambda trial:
            inner_cv_objective(

                trial=trial,

                X_train=X_train,

                y_train=y_train,

                inner_folds=
                    effective_inner_folds,

                device=device,

                seed=
                    args.seed
                    + 50000,

                min_count=
                    args.min_count,

                prevalence=
                    args.prevalence,

                zero_fraction=
                    args.zero_fraction,

                groups_train=groups_train
            ),




        n_trials=
            args.trials,

        gc_after_trial=True
    )

    ########################################################
    # Best params
    ########################################################

    best_params = (
        study.best_params
    )

    best_info = {

        "best_value":
            float(
                study.best_value
            ),

        "best_trial":
            int(
                study.best_trial.number
            ),

        "best_parameters":
            best_params,

        "selection_data":
            "training_partition_only"
    }

    with open(

        output_dir
        / "best_parameters.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            best_info,
            handle,
            indent=2,
            default=float
        )

    ########################################################
    # All Optuna trials
    ########################################################

    study.trials_dataframe().to_csv(

        output_dir
        / "optuna_trials.tsv",

        sep="\t",

        index=False
    )

    ########################################################
    # Internal final validation split
    #
    # still TRAIN only
    ########################################################

    (
        final_train_idx,
        final_valid_idx,
        achieved_validation_fraction

    ) = study_aware_validation_split(

        X=X_train,

        y=y_train,

        groups=groups_train,

        validation_fraction=
            args.validation_fraction,

        seed=
            args.seed
            + 60000
    )


    X_final_train = (

        X_train
        .iloc[
            final_train_idx
        ]
        .copy()
    )


    X_final_valid = (

        X_train
        .iloc[
            final_valid_idx
        ]
        .copy()
    )


    y_final_train = (

        y_train
        .iloc[
            final_train_idx
        ]
        .copy()
    )


    y_final_valid = (

        y_train
        .iloc[
            final_valid_idx
        ]
        .copy()
    )


    groups_final_train = (

        groups_train
        .iloc[
            final_train_idx
        ]
    )


    groups_final_valid = (

        groups_train
        .iloc[
            final_valid_idx
        ]
    )


    final_study_overlap = (

        set(
            groups_final_train.unique()
        )

        &

        set(
            groups_final_valid.unique()
        )
    )


    if final_study_overlap:

        raise RuntimeError(
            "Study leakage detected between "
            "final training and validation sets: "
            f"{sorted(final_study_overlap)}"
        )

########################################################
# Leakage-safe microbiome preprocessing
#
# FIT ONLY on final training subset
########################################################

    microbiome_preprocessor = MicrobiomeCLRPreprocessor(

        min_count=
            args.min_count,

        prevalence=
            args.prevalence,

        zero_fraction=
            args.zero_fraction
    )


    X_final_train = (
        microbiome_preprocessor
        .fit_transform(
            X_final_train
        )
    )


    X_final_valid = (
        microbiome_preprocessor
        .transform(
            X_final_valid
        )
    )


########################################################
# Held-out test:
# APPLY ONLY — NEVER FIT
########################################################

    X_test = (
        microbiome_preprocessor
        .transform(
            X_test
        )
    )


    joblib.dump(

        microbiome_preprocessor,

        output_dir
        / "microbiome_preprocessor.joblib"
    )

    ########################################################
    # Scaling
    #
    # Fit ONLY final training subset
    ########################################################

    scaler = StandardScaler()

    X_final_train_scaled = (
        scaler.fit_transform(
            X_final_train
        )
    )

    X_final_valid_scaled = (
        scaler.transform(
            X_final_valid
        )
    )

    ########################################################
    # TEST only transformed here
    ########################################################

    X_test_scaled = (
        scaler.transform(
            X_test
        )
    )

    joblib.dump(

        scaler,

        output_dir
        / "scaler.joblib"
    )

    ########################################################
    # Dataset
    ########################################################

    train_dataset = MicrobiomeDataset(

        X_final_train_scaled,

        y_final_train
    )

    valid_dataset = MicrobiomeDataset(

        X_final_valid_scaled,

        y_final_valid
    )

    test_dataset = MicrobiomeDataset(

        X_test_scaled,

        y_test
    )

    ########################################################
    # Loaders
    ########################################################

    train_loader = DataLoader(

        train_dataset,

        batch_size=
            best_params[
                "batch_size"
            ],

        shuffle=True,

        drop_last=False
    )

    valid_loader = DataLoader(

        valid_dataset,

        batch_size=
            best_params[
                "batch_size"
            ],

        shuffle=False,

        drop_last=False
    )

    test_loader = DataLoader(

        test_dataset,

        batch_size=
            best_params[
                "batch_size"
            ],

        shuffle=False,

        drop_last=False
    )

    ########################################################
    # Final Model
    ########################################################

    model = build_mlp(

        params=
            best_params,

        input_dim=
            X_final_train.shape[1],

        output_dim=
            n_classes
    )

    model.to(
        device
    )

    criterion = (
        nn.CrossEntropyLoss()
    )

    optimizer = build_optimizer(

        model,

        best_params
    )

    scheduler = build_scheduler(

        optimizer,

        best_params
    )

    early_stopping = EarlyStopping(

        patience=
            best_params[
                "patience"
            ],

        min_delta=
            1e-4,

        mode=
            "max"
    )

    ########################################################
    # Train final model
    ########################################################

    model, history = fit(

        model=model,

        train_loader=
            train_loader,

        valid_loader=
            valid_loader,

        criterion=
            criterion,

        optimizer=
            optimizer,

        scheduler=
            scheduler,

        early_stopping=
            early_stopping,

        device=
            device,

        epochs=
            args.max_epochs,

        checkpoint_path=
            str(
                output_dir
                / "final_model.pt"
            ),

        gradient_clip=
            best_params[
                "gradient_clip"
            ]
    )

    ########################################################
    # HELD-OUT TEST
    #
    # First and only evaluation
    ########################################################

    prediction = predict(

        model=model,

        dataloader=
            test_loader,

        device=device
    )

    probability = predict_proba(

        model=model,

        dataloader=
            test_loader,

        device=device
    )

    ########################################################
    # Metrics
    ########################################################

    metrics, cm = calculate_metrics(

        y_true=
            y_test.to_numpy(),

        y_pred=
            prediction,

        y_prob=
            probability,

        n_classes=
            n_classes
    )

    ########################################################
    # Metrics TSV / JSON
    ########################################################

    pd.DataFrame(
        [metrics]
    ).to_csv(

        output_dir
        / "final_test_metrics.tsv",

        sep="\t",

        index=False
    )

    with open(

        output_dir
        / "final_test_metrics.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            metrics,
            handle,
            indent=2,
            default=float
        )

    ########################################################
    # Predictions
    ########################################################

    prediction_df = pd.DataFrame({

        "SampleID":
            X_test.index,

        "TrueEncoded":
            y_test.to_numpy(),

        "PredictedEncoded":
            prediction,

        "TrueLabel":
            encoder.inverse_transform(
                y_test.to_numpy()
            ),

        "PredictedLabel":
            encoder.inverse_transform(
                np.asarray(
                    prediction,
                    dtype=int
                )
            )
    })

    for (
        class_id,
        class_name
    ) in enumerate(
        encoder.classes_
    ):

        safe_name = (
            str(
                class_name
            )
            .replace(
                " ",
                "_"
            )
        )

        prediction_df[
            f"Probability_{safe_name}"
        ] = probability[
            :,
            class_id
        ]

    prediction_df.to_csv(

        output_dir
        / "final_test_predictions.tsv",

        sep="\t",

        index=False
    )

    ########################################################
    # Figures
    ########################################################

    save_confusion_matrix(

        cm,

        encoder.classes_.tolist(),

        output_dir
    )

    save_roc_pr(

        y_test.to_numpy(),

        probability,

        encoder.classes_.tolist(),

        output_dir
    )

    save_history(

        history,

        output_dir
    )

    is_transductive = (
        args.analysis_mode
        == "transductive_sensitivity"
    )

    ########################################################
    # Final summary
    ########################################################

    summary = {

        "training_samples_total":
            int(
                len(X_train)
            ),

        "final_training_samples":
            int(
                len(
                    X_final_train
                )
            ),

        "final_validation_samples":
            int(
                len(
                    X_final_valid
                )
            ),

        "heldout_test_samples":
            int(
                len(X_test)
            ),

        "raw_features":
            int(
                microbiome_preprocessor
                .n_features_in_
            ),

        "features_after_abundance_prevalence_filter":
            int(
                microbiome_preprocessor
                .n_features_out_
            ),

        "classes":
            encoder.classes_.tolist(),

        "requested_inner_folds":
            int(
                args.inner_folds
            ),

        "effective_inner_folds":
            int(
                effective_inner_folds
            ),

        "training_studies":
            int(
                groups_train.nunique()
            ),

        "final_training_studies":
            int(
                groups_final_train.nunique()
            ),

        "final_validation_studies":
            int(
                groups_final_valid.nunique()
            ),

        "heldout_test_studies":
            int(
                groups_test.nunique()
            ),

        "achieved_validation_fraction":
            float(
                achieved_validation_fraction
            ),

        "analysis_mode":
            args.analysis_mode,

        "primary_analysis":
            not is_transductive,

        "strict_unseen_study_inductive":
            not is_transductive,

        "upstream_batch_correction":
            (
                "MMUPHin_global"
                if is_transductive
                else "none"
            ),

        "test_labels_used_for_upstream_harmonization":
            False,

        "test_feature_distribution_seen_during_upstream_harmonization":
            bool(
                is_transductive
            ),


        "optuna_trials":
            int(
                args.trials
            ),

        "best_inner_cv_roc_auc":
            float(
                study.best_value
            ),

        "heldout_metrics": {

            key:
                (
                    None

                    if not np.isfinite(
                        value
                    )

                    else float(
                        value
                    )
                )

            for key, value
            in metrics.items()
        },

        "test_usage":
            (
                (
                    "Test labels were not used during "
                    "model selection or training. "
                    "However, the test feature distribution "
                    "participated in the upstream global "
                    "MMUPHin harmonization. Therefore this "
                    "result is a transductive sensitivity "
                    "analysis and must not be interpreted "
                    "as strict unseen-study inductive "
                    "performance."
                )

                if is_transductive

                else

                (
                    "Held-out test was used only once "
                    "after all model selection and "
                    "training decisions."
                )
            )
    }

    with open(

        output_dir
        / "final_summary.json",

        "w",

        encoding="utf-8"

    ) as handle:

        json.dump(
            summary,
            handle,
            indent=2
        )

    print(
        "Final held-out DL evaluation "
        "completed successfully."
    )

    for key, value in metrics.items():

        print(
            f"{key:20s}: {value}"
        )


if __name__ == "__main__":

    main()