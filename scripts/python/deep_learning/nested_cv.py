"""
nested_cv.py

Nested cross-validation framework for hyperparameter
optimization and unbiased performance estimation.

Workflow
--------
Outer CV
    ├── Train/Test split
    ├── Inner Optuna optimization
    ├── Model retraining
    ├── Test evaluation
    └── Result aggregation

Author : Matin Fathollahi
Project: Microbiome Meta-analysis
License: 
"""

############################################################
# Imports
############################################################

import os
import json
import argparse
import tarfile

import numpy as np
import pandas as pd
import random
import joblib

import torch
import optuna

import torch.nn as nn

from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler
)

from torch.utils.data import DataLoader
from microbiome_preprocessing import (
    MicrobiomeCLRPreprocessor
)



from sklearn.model_selection import (
    StratifiedKFold,
    StratifiedGroupKFold,
    LeaveOneGroupOut,
    train_test_split
)

############################################################
# Local Modules
############################################################

from deep_learning.train import get_device, fit, predict, predict_proba

from deep_learning.optuna.objective import objective

from deep_learning.models.mlp import build_mlp

from deep_learning.dataset import MicrobiomeDataset


from deep_learning.early_stopping import EarlyStopping

from deep_learning.metrics import evaluate

############################################################
# Argument Parser
############################################################

def parse_args():

    parser = argparse.ArgumentParser(

        description="Nested Cross Validation for Deep Learning"

    )

    parser.add_argument(

        "--input",

        required=True,

        help="Unscaled feature matrix (.tsv)"

    )

    parser.add_argument(

        "--labels",

        required=True,

        help="Labels (.tsv)"

    )

    parser.add_argument(

        "--output",

        required=True,

        help="Output directory"

    )

    parser.add_argument(
        "--groups",
        required=True
    )

    parser.add_argument(
        "--fallback_folds",
        type=int,
        default=5
    )


    parser.add_argument(
        "--inner_folds",
        type=int,
        default=5,
        help="Number of folds for inner cross-validation"
    )

    parser.add_argument(

        "--inner_trials",

        type=int,

        default=100

    )

    parser.add_argument(

        "--seed",

        type=int,

        default=2026

    )

    parser.add_argument(

        "--min_count",

        type=float,

        required=True

    )

    parser.add_argument(

        "--prevalence",

        type=float,

        required=True

    )

    parser.add_argument(

        "--zero_fraction",

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
            "Interpretation of the analysis. "
            "Raw DL should use primary_inductive; "
            "globally MMUPHin-harmonized DL should use "
            "transductive_sensitivity."
        )
    )

    return parser.parse_args()

############################################################
# Load Dataset
############################################################

def load_dataset(
    feature_file,
    label_file,
    group_file
):

    X = pd.read_csv(

        feature_file,

        sep="\t",

        index_col=0

    )

    y = pd.read_csv(

        label_file,

        sep="\t",

        index_col=0

    )



    groups = pd.read_csv(
        group_file,
        sep="\t",
        index_col=0
    )




    if groups.shape[1] != 1:

        raise ValueError(
            "Groups file must contain "
            "exactly one group column."
        )


    ########################################################
    # Validate labels
    ########################################################

    if y.shape[1] != 1:

        raise ValueError(
            "Labels file must contain "
            "exactly one label column."
        )


    y = y.iloc[:, 0]


    if y.isna().any():

        raise ValueError(
            "Label column contains "
            "missing values."
        )


    y = (
        y
        .astype(str)
        .str.strip()
    )


    if (y == "").any():

        raise ValueError(
            "Label column contains "
            "empty values."
        )


    ########################################################
    # Validate groups
    ########################################################

    groups = groups.iloc[:, 0]


    if groups.isna().any():

        raise ValueError(
            "Group column contains "
            "missing values."
        )


    groups = (
        groups
        .astype(str)
        .str.strip()
    )


    if (groups == "").any():

        raise ValueError(
            "Group column contains "
            "empty values."
        )


    ########################################################
    # Validate sample alignment
    ########################################################

    if not X.index.equals(y.index):

        raise ValueError(
            "Feature and label sample IDs "
            "do not match."
        )


    if not X.index.equals(groups.index):

        raise ValueError(
            "Feature and group sample IDs "
            "do not match."
        )


    return X, y, groups


def inner_cv_objective(
    trial,
    X_train,
    y_train,
    inner_folds,
    device,
    seed,
    min_count,
    prevalence,
    zero_fraction,
    groups_train=None
):
    """
    Evaluate one Optuna hyperparameter trial by
    stratified inner cross-validation.

    Hyperparameters are identical across all inner folds.
    The returned objective value is the mean ROC-AUC
    across inner validation folds.
    """

    if y_train.nunique() < 2:

        raise ValueError(
            "Inner CV training data "
            "must contain at least "
            "two classes."
        )






    if (
        groups_train is not None
        and groups_train.nunique() >= 2
    ):

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


        if min_groups_per_class < 2:

            raise ValueError(
                "Study-aware inner CV is "
                "not possible because at "
                "least one class occurs "
                "in fewer than two studies. "
                f"Groups per class: "
                f"{groups_per_class.to_dict()}"
            )


        effective_inner_folds = min(
            inner_folds,
            groups_train.nunique(),
            min_groups_per_class
        )

        inner_cv = StratifiedGroupKFold(
            n_splits=
                effective_inner_folds,

            shuffle=True,

            random_state=seed
        )

        inner_splits = list(
            inner_cv.split(
                X_train,
                y_train,
                groups=groups_train
            )
        )

        inner_strategy = (
            "StratifiedGroupKFold"
        )

    else:

        minimum_class_size = int(
            y_train
            .value_counts()
            .min()
        )

        effective_inner_folds = min(
            inner_folds,
            minimum_class_size
        )

        if effective_inner_folds < 2:

            raise ValueError(
                "Not enough samples "
                "for inner CV."
            )

        inner_cv = StratifiedKFold(
            n_splits=
                effective_inner_folds,

            shuffle=True,

            random_state=seed
        )

        inner_splits = list(
            inner_cv.split(
                X_train,
                y_train
            )
        )

        inner_strategy = (
            "StratifiedKFold fallback"
        )






    ########################################################
    # Validate inner splits
    ########################################################

    all_classes = set(
        y_train.unique()
    )


    for (
        check_fold,
        (
            check_train_idx,
            check_valid_idx
        )
    ) in enumerate(
        inner_splits,
        start=1
    ):

        train_classes = set(
            y_train
            .iloc[check_train_idx]
            .unique()
        )

        valid_classes = set(
            y_train
            .iloc[check_valid_idx]
            .unique()
        )


        if train_classes != all_classes:

            raise ValueError(
                f"Inner fold {check_fold}: "
                "training split does not "
                "contain all classes."
            )


        if valid_classes != all_classes:

            raise ValueError(
                f"Inner fold {check_fold}: "
                "validation split does not "
                "contain all classes. "
                "ROC-AUC cannot be computed "
                "reliably with this "
                "study distribution."
            )


        if (
            groups_train is not None
            and groups_train.nunique() >= 2
        ):

            train_groups = set(
                groups_train
                .iloc[check_train_idx]
                .unique()
            )

            valid_groups = set(
                groups_train
                .iloc[check_valid_idx]
                .unique()
            )

            overlap = (
                train_groups
                &
                valid_groups
            )

            if overlap:

                raise RuntimeError(
                    "Study leakage detected "
                    f"in inner fold "
                    f"{check_fold}: "
                    f"{sorted(overlap)}"
                )








    fold_scores = []

    for inner_fold, (
        inner_train_idx,
        inner_valid_idx
    ) in enumerate(
        inner_splits,
        start=1
    ):

        X_inner_train = (
            X_train
            .iloc[inner_train_idx]
            .copy()
        )

        X_inner_valid = (
            X_train
            .iloc[inner_valid_idx]
            .copy()
        )

        y_inner_train = (
            y_train
            .iloc[inner_train_idx]
            .copy()
        )

        y_inner_valid = (
            y_train
            .iloc[inner_valid_idx]
            .copy()
        )


########################################################
# Leakage-safe microbiome preprocessing
#
# FIT ONLY on inner training fold
########################################################

        microbiome_preprocessor = MicrobiomeCLRPreprocessor(

            min_count=min_count,

            prevalence=prevalence,

            zero_fraction=zero_fraction
        )


        X_inner_train = (
            microbiome_preprocessor
            .fit_transform(
                X_inner_train
            )
        )


        X_inner_valid = (
            microbiome_preprocessor
            .transform(
                X_inner_valid
            )
        )

        fold_seed = (
            seed
            + inner_fold
        )

        score = objective(
            trial=trial,
            X_train=X_inner_train,
            y_train=y_inner_train,
            X_valid=X_inner_valid,
            y_valid=y_inner_valid,
            device=device,
            seed=fold_seed,
            enable_pruning=False
        )

        if not np.isfinite(score):
            raise optuna.TrialPruned(
                f"Non-finite ROC-AUC in inner fold {inner_fold}"
            )

        fold_scores.append(
            float(score)
        )

        mean_so_far = float(
            np.mean(fold_scores)
        )

        trial.report(
            mean_so_far,
            step=inner_fold
        )

        if trial.should_prune():
            raise optuna.TrialPruned()

    trial.set_user_attr(
        "inner_fold_scores",
        fold_scores
    )

    return float(
        np.mean(fold_scores)
    )

############################################################
# Main
############################################################

def main():

    ########################################################
    # Arguments
    ########################################################

    args = parse_args()

    ########################################################
    # Output Folder
    ########################################################

    os.makedirs(

        args.output,

        exist_ok=True

    )

########################################################
# Random Seed
########################################################

    random.seed(args.seed)

    np.random.seed(args.seed)

    torch.manual_seed(args.seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    ########################################################
    # Device
    ########################################################

    device = get_device()

    ########################################################
    # Dataset
    ########################################################

    X, y, groups = load_dataset(
        args.input,
        args.labels,
        args.groups
    )



    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(
        y.astype(str)
    )

    y = pd.Series(
        y_encoded,
        index=y.index
    )

    ########################################################

    print(

        f"Samples : {X.shape[0]}"

    )

    print(

        f"Features : {X.shape[1]}"

    )

    print(

        f"Classes : {len(np.unique(y))}"

    )

    ########################################################
    # Continue in Part 2
    ########################################################






    ########################################################
    # Dynamic study-aware Outer CV
    ########################################################

    n_groups = groups.nunique()


    if n_groups >= 2:

        outer_strategy = (
            "LeaveOneGroupOut"
        )

        outer_cv = LeaveOneGroupOut()

        outer_splits = list(
            outer_cv.split(
                X,
                y,
                groups=groups
            )
        )

    else:

        outer_strategy = (
            "StratifiedKFold fallback"
        )

        minimum_class_size = int(
            y.value_counts().min()
        )

        effective_outer_folds = min(
            args.fallback_folds,
            minimum_class_size
        )

        if effective_outer_folds < 2:

            raise ValueError(
                "Not enough samples "
                "for outer CV."
            )

        outer_cv = StratifiedKFold(
            n_splits=
                effective_outer_folds,

            shuffle=True,

            random_state=args.seed
        )

        outer_splits = list(
            outer_cv.split(
                X,
                y
            )
        )


    outer_fold_count = len(
        outer_splits
    )


    print(
        "Outer strategy:",
        outer_strategy
    )

    print(
        "Detected studies:",
        n_groups
    )

    print(
        "Outer folds:",
        outer_fold_count
    )

    ########################################################
    # Containers
    ########################################################

    outer_scores = []

    best_parameters = []

    ########################################################
    # Outer Loop
    ########################################################

    for fold, (
        train_idx,
        test_idx
    ) in enumerate(

        outer_splits,

        start=1
    ):

        print("\n")

        print("=" * 70)

        print(

            f"Outer Fold {fold}/{outer_fold_count}"

        )

        print("=" * 70)

        ####################################################
        # Split Dataset
        ####################################################

        X_train = X.iloc[

            train_idx

        ].copy()

        X_test = X.iloc[

            test_idx

        ].copy()

        y_train = y.iloc[

            train_idx

        ].copy()

        y_test = y.iloc[

            test_idx

        ].copy()



        groups_train = (
            groups
            .iloc[train_idx]
            .copy()
        )

        groups_test = (
            groups
            .iloc[test_idx]
            .copy()
        )



        ####################################################
        # Check class availability
        ####################################################

        all_classes = set(
            y.unique()
        )


        outer_train_classes = set(
            y_train.unique()
        )

        outer_test_classes = set(
            y_test.unique()
        )


        if outer_train_classes != all_classes:

            raise ValueError(
                f"Outer fold {fold}: "
                "training studies do not "
                "contain all classes."
            )


        if outer_test_classes != all_classes:

            print(
                f"WARNING: Outer fold "
                f"{fold} test study does "
                "not contain all classes. "
                "ROC-AUC will not be "
                "available for this fold."
            )


        train_studies = set(
            groups_train.unique()
        )

        test_studies = set(
            groups_test.unique()
        )


        if n_groups >= 2:

            overlap = (
                train_studies
                &
                test_studies
            )

            if overlap:

                raise RuntimeError(
                    "Study leakage detected "
                    f"in outer fold {fold}: "
                    f"{sorted(overlap)}"
                )


        print(
            "Train studies:",
            sorted(train_studies)
        )

        print(
            "Test studies:",
            sorted(test_studies)
        )








        ####################################################
        # Fold Information
        ####################################################

        print(

            f"Train Samples : {len(X_train)}"

        )

        print(

            f"Test Samples  : {len(X_test)}"

        )

        ####################################################
        # Continue in Part 3
        ####################################################




        ####################################################
        # Create Optuna Study
        ####################################################

        study = optuna.create_study(

            study_name=f"Fold_{fold}",

            direction="maximize",

            sampler=optuna.samplers.TPESampler(

                seed=args.seed,

                multivariate=True

            ),

            pruner=optuna.pruners.MedianPruner(

                n_startup_trials=10,

                n_warmup_steps=1

            )

        )

        ####################################################
        # Run Optuna
        ####################################################

        study.optimize(

            lambda trial: inner_cv_objective(

                trial=trial,

                X_train=X_train,

                y_train=y_train,
                groups_train=groups_train,

                inner_folds=args.inner_folds,

                device=device,

                seed=args.seed + fold * 1000,

                min_count=args.min_count,

                prevalence=args.prevalence,

                zero_fraction=args.zero_fraction
            ),

            n_trials=args.inner_trials,

            gc_after_trial=True
        )

        ####################################################
        # Best Parameters
        ####################################################

        best_params = study.best_params
        best_info = {
            "best_value": study.best_value,
            "best_trial": study.best_trial.number,
            "best_parameters": study.best_params
        }

        best_parameters.append(

            best_params

        )

        ####################################################
        # Final train/validation split
        # Study-aware whenever possible
        ####################################################

        if groups_train.nunique() >= 2:

            final_groups_per_class = (

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


            final_min_groups_per_class = int(
                final_groups_per_class.min()
            )


            if final_min_groups_per_class < 2:

                raise ValueError(
                    f"Outer fold {fold}: "
                    "study-aware final "
                    "train/validation split "
                    "is impossible because "
                    "at least one class occurs "
                    "in fewer than two studies. "
                    f"Groups per class: "
                    f"{final_groups_per_class.to_dict()}"
                )


            final_folds = min(
                args.inner_folds,
                groups_train.nunique(),
                final_min_groups_per_class
            )











            final_splitter = StratifiedGroupKFold(

                n_splits=final_folds,

                shuffle=True,

                random_state=
                    args.seed
                    + fold
                    + 100
            )


            final_splits = list(

                final_splitter.split(
                    X_train,
                    y_train,
                    groups=groups_train
                )
            )


            required_classes = set(
                y_train.unique()
            )


            selected_final_split = None


            for (
                candidate_train_idx,
                candidate_valid_idx
            ) in final_splits:

                candidate_train_classes = set(
                    y_train
                    .iloc[candidate_train_idx]
                    .unique()
                )

                candidate_valid_classes = set(
                    y_train
                    .iloc[candidate_valid_idx]
                    .unique()
                )


                if (
                    candidate_train_classes
                    == required_classes
                    and
                    candidate_valid_classes
                    == required_classes
                ):

                    selected_final_split = (
                        candidate_train_idx,
                        candidate_valid_idx
                    )

                    break


            if selected_final_split is None:

                raise ValueError(
                    f"Outer fold {fold}: "
                    "Could not create a "
                    "study-separated final "
                    "train/validation split "
                    "containing all classes "
                    "in both subsets."
                )


            (
                final_train_idx,
                final_valid_idx
            ) = selected_final_split


            X_final_train = (
                X_train
                .iloc[final_train_idx]
                .copy()
            )

            X_final_valid = (
                X_train
                .iloc[final_valid_idx]
                .copy()
            )


            y_final_train = (
                y_train
                .iloc[final_train_idx]
                .copy()
            )

            y_final_valid = (
                y_train
                .iloc[final_valid_idx]
                .copy()
            )


            final_groups_train = set(
                groups_train
                .iloc[final_train_idx]
                .unique()
            )

            final_groups_valid = set(
                groups_train
                .iloc[final_valid_idx]
                .unique()
            )


            overlap = (
                final_groups_train
                &
                final_groups_valid
            )


            if overlap:

                raise RuntimeError(
                    "Study leakage detected "
                    "in final train/validation "
                    f"split: {sorted(overlap)}"
                )


        else:

            (
                X_final_train,
                X_final_valid,
                y_final_train,
                y_final_valid
            ) = train_test_split(

                X_train,

                y_train,

                test_size=0.1,

                stratify=y_train,

                random_state=
                    args.seed
                    + fold
                    + 100
            )



####################################################
# Leakage-safe microbiome preprocessing
#
# FIT ONLY on final outer-training subset
####################################################

        microbiome_preprocessor = MicrobiomeCLRPreprocessor(

            min_count=args.min_count,

            prevalence=args.prevalence,

            zero_fraction=args.zero_fraction
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


####################################################
# Outer test is NEVER used during fit
####################################################

        X_test = (
            microbiome_preprocessor
            .transform(
                X_test
            )
        )


        ####################################################
        # Fold-specific Standard Scaling
        # Fit ONLY on final training subset
        ####################################################

        scaler = StandardScaler()

        X_final_train_scaled = scaler.fit_transform(
            X_final_train
        )

        X_final_valid_scaled = scaler.transform(
            X_final_valid
        )

        X_test_scaled = scaler.transform(
            X_test
        )

        ####################################################
        # Best Score
        ####################################################

        print(

            f"Best Validation ROC-AUC : "

            f"{study.best_value:.6f}"

        )

        print(

            "Best Parameters"

        )

        for key, value in best_params.items():

            print(

                f"{key:20s} : {value}"

            )

        ####################################################
        # Continue in Part 4
        ####################################################


####################################################
# Final Train / Validation Split
####################################################

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

        ####################################################
        # Dataset
        ####################################################


####################################################
# DataLoader
####################################################

        train_loader = DataLoader(

            train_dataset,

            batch_size=best_params["batch_size"],

            shuffle=True,

            drop_last=False

        )

        valid_loader = DataLoader(
            valid_dataset,
            batch_size=best_params["batch_size"],
            shuffle=False,
            drop_last=False
        )

        test_loader = DataLoader(

            test_dataset,

            batch_size=best_params["batch_size"],

            shuffle=False,

            drop_last=False

        )

        ####################################################
        # Build Model
        ####################################################

        model = build_mlp(

            params=best_params,

            input_dim=X_final_train.shape[1],

            output_dim=len(

                np.unique(y)

            )

        )

        ####################################################
        # Device
        ####################################################

        model.to(

            device

        )

        ####################################################
        # Loss Function
        ####################################################

        criterion = nn.CrossEntropyLoss()

        ####################################################
        # Optimizer
        ####################################################

        if best_params["optimizer"] == "Adam":

            optimizer = torch.optim.Adam(

                model.parameters(),

                lr=best_params["learning_rate"],

                weight_decay=best_params["weight_decay"]

            )

        elif best_params["optimizer"] == "AdamW":

            optimizer = torch.optim.AdamW(

                model.parameters(),

                lr=best_params["learning_rate"],

                weight_decay=best_params["weight_decay"]

            )

        else:

            optimizer = torch.optim.RMSprop(

                model.parameters(),

                lr=best_params["learning_rate"],

                weight_decay=best_params["weight_decay"]

            )

        ####################################################
        # Scheduler
        ####################################################

        scheduler = None

        if best_params["scheduler"] == "Plateau":

            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(

                optimizer,

                mode="min",

                patience=5

            )

        elif best_params["scheduler"] == "Cosine":

            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(

                optimizer,

                T_max=200

            )

        elif best_params["scheduler"] == "Step":

            scheduler = torch.optim.lr_scheduler.StepLR(

                optimizer,

                step_size=best_params["step_size"],

                gamma=best_params["gamma"]

            )

        ####################################################
        # Early Stopping
        ####################################################

        early_stopping = EarlyStopping(

            patience=best_params["patience"],

            min_delta=1e-4,

            mode="max"

        )

        ####################################################
        # Checkpoint
        ####################################################

        checkpoint_path = os.path.join(

            args.output,

            f"fold_{fold}",

            "best_model.pt"

        )

        os.makedirs(

            os.path.dirname(

                checkpoint_path

            ),

            exist_ok=True

        )

        ####################################################
        # Train
        ####################################################

        model, history = fit(

            model=model,

            train_loader=train_loader,

            valid_loader=valid_loader,

            criterion=criterion,

            optimizer=optimizer,

            scheduler=scheduler,

            early_stopping=early_stopping,

            device=device,

            epochs=200,

            checkpoint_path=checkpoint_path,

            gradient_clip=best_params["gradient_clip"]

        )

        ####################################################
        # Continue in Part 5
        ####################################################




        ####################################################
        # Predict Labels
        ####################################################

        prediction = predict(

            model=model,

            dataloader=test_loader,

            device=device

        )

        ####################################################
        # Predict Probabilities
        ####################################################

        probability = predict_proba(

            model=model,

            dataloader=test_loader,

            device=device

        )

        ####################################################
        # Evaluate
        ####################################################

        metrics = evaluate(

            y_true=np.asarray(

                y_test

            ),

            y_pred=prediction,

            y_prob=probability

        )

        ####################################################
        # Save Fold Result
        ####################################################

        outer_scores.append(

            metrics

        )

        ####################################################
        # Print Fold Metrics
        ####################################################

        print("\n")

        print(

            "=" * 60

        )

        print(

            f"Fold {fold} Results"

        )

        print(

            "=" * 60

        )

        print(

            f"Accuracy          : {metrics['Accuracy']:.4f}"

        )

        print(

            f"Balanced Accuracy : {metrics['BalancedAccuracy']:.4f}"

        )

        print(

            f"Precision         : {metrics['Precision']:.4f}"

        )

        print(

            f"Recall            : {metrics['Recall']:.4f}"

        )

        print(

            f"F1 Score          : {metrics['F1']:.4f}"

        )

        print(

            f"MCC               : {metrics['MCC']:.4f}"

        )

        print(

            f"ROC-AUC           : {metrics['ROC_AUC']:.4f}"

        )

        print(

            "=" * 60

        )

        ####################################################
        # Continue in Part 6
        ####################################################



        ####################################################
        # Fold Output Directory
        ####################################################

        fold_dir = os.path.join(

            args.output,

            f"fold_{fold}"

        )


        os.makedirs(

            fold_dir,

            exist_ok=True

        )


        joblib.dump(
            scaler,
            os.path.join(
                fold_dir,
                "scaler.joblib"
            )
        )


        joblib.dump(

            microbiome_preprocessor,

            os.path.join(

                fold_dir,

                "microbiome_preprocessor.joblib"
            )
        )


        ####################################################
        # Save Predictions
        ####################################################

        prediction_df = pd.DataFrame({

            "Sample": y_test.index,

            "True_Label": y_test.values,

            "Prediction": prediction

        })

        prediction_df.to_csv(

            os.path.join(

                fold_dir,

                "predictions.tsv"

            ),

            sep="\t",

            index=False

        )

        ####################################################
        # Save Probabilities
        ####################################################

        probability_df = pd.DataFrame(

            probability,

            index=y_test.index

        )

        probability_df.columns = [

            f"Class_{i}"

            for i in range(

                probability.shape[1]

            )

        ]

        probability_df.to_csv(

            os.path.join(

                fold_dir,

                "probabilities.tsv"

            ),

            sep="\t"

        )

        ####################################################
        # Save Metrics
        ####################################################

        with open(

            os.path.join(

                fold_dir,

                "metrics.json"

            ),

            "w"

        ) as f:

            json.dump(

                metrics,

                f,

                indent=4, 
                default=float

            )

        ####################################################
        # Save Best Parameters
        ####################################################

        with open(
            os.path.join(
                fold_dir,
                "best_parameters.json"
            ),
            "w"
        ) as f:

            json.dump(
                best_info,
                f,
                indent=4,
                default=float
                
            )

        ####################################################
        # Save Training History
        ####################################################

        history_df = pd.DataFrame(

            history

        )

        history_df.to_csv(

            os.path.join(

                fold_dir,

                "history.tsv"

            ),

            sep="\t",

            index=False

        )

        ####################################################
        # Save Fold Summary
        ####################################################

        summary = {

            "Fold": fold,

            "Accuracy": metrics["Accuracy"],

            "BalancedAccuracy": metrics["BalancedAccuracy"],

            "Precision": metrics["Precision"],

            "Recall": metrics["Recall"],

            "F1": metrics["F1"],

            "MCC": metrics["MCC"],

            "ROC_AUC": metrics["ROC_AUC"]

        }

        with open(

            os.path.join(

                fold_dir,

                "summary.json"

            ),

            "w"

        ) as f:

            json.dump(

                summary,

                f,

                indent=4,
                default=float

            )

        ####################################################
        # Save Fold Model
        ####################################################

        torch.save(

            model.state_dict(),

            os.path.join(

                fold_dir,

                "final_model.pt"

            )

        )



    results = pd.DataFrame(outer_scores)

    mean_scores = results.mean(numeric_only=True)


    std_scores = results.std(numeric_only=True)


    is_transductive = (
        args.analysis_mode
        == "transductive_sensitivity"
    )


    summary = {

        "Mean":
            mean_scores.to_dict(),

        "STD":
            std_scores.to_dict(),

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

        "validation_distribution_seen_during_upstream_harmonization":
            bool(
                is_transductive
            ),

        "interpretation":
            (
                "Transductive sensitivity analysis. "
                "Outer/inner CV splitting and model fitting "
                "remain fold-aware, but upstream global "
                "MMUPHin harmonization was performed before "
                "the CV split."
                if is_transductive
                else
                "Primary strict inductive deep-learning "
                "analysis with fold-fitted microbiome "
                "preprocessing."
            )
    }


    with open(
        os.path.join(
            args.output,
            "nested_summary.json"
        ),
        "w"
    ) as f:

        json.dump(
            summary,
            f,
            indent=4,
            default=float
        )


    results.to_csv(
        os.path.join(
            args.output,
            "nested_scores.tsv"
        ),
        sep="\t",
        index=False
    )



    print("\n")
    print("=" * 70)
    print("FINAL NESTED CV RESULTS")
    print("=" * 70)

    for metric in mean_scores.index:

        print(

            f"{metric:20s}"

            f"{mean_scores[metric]:.4f}"

            f" ± "

            f"{std_scores[metric]:.4f}"

        )

    print("=" * 70)



    best_param_df = pd.DataFrame(best_parameters)
    best_param_df.insert(0, "Fold", range(1, len(best_parameters) + 1))

    best_param_df.to_csv(
        os.path.join(
            args.output,
            "best_parameters_all_folds.tsv"
        ),
        sep="\t",
        index=False
    )


    ########################################################
    # Validate and package fold artifacts
    ########################################################

    required_fold_files = [
        "best_model.pt",
        "final_model.pt",
        "scaler.joblib",
        "microbiome_preprocessor.joblib",
        "predictions.tsv",
        "probabilities.tsv",
        "metrics.json",
        "best_parameters.json",
        "history.tsv",
        "summary.json",
    ]

    ########################################################
    # Expected fold directories from THIS run
    ########################################################

    expected_fold_names = [
        f"fold_{fold}"
        for fold in range(
            1,
            outer_fold_count + 1
        )
    ]

    existing_fold_names = [
        name
        for name in os.listdir(args.output)
        if (
            name.startswith("fold_")
            and os.path.isdir(
                os.path.join(
                    args.output,
                    name
                )
            )
        )
    ]

    ########################################################
    # Detect missing / stale fold directories
    ########################################################

    missing_fold_dirs = sorted(
        set(expected_fold_names)
        - set(existing_fold_names)
    )

    unexpected_fold_dirs = sorted(
        set(existing_fold_names)
        - set(expected_fold_names)
    )

    if missing_fold_dirs:
        raise RuntimeError(
            "Missing expected fold directories: "
            + ", ".join(
                missing_fold_dirs
            )
        )

    if unexpected_fold_dirs:
        raise RuntimeError(
            "Unexpected/stale fold directories detected: "
            + ", ".join(
                unexpected_fold_dirs
            )
        )

    fold_dirs = [
        os.path.join(
            args.output,
            fold_name
        )
        for fold_name
        in expected_fold_names
    ]

    ########################################################
    # Validate required artifacts
    ########################################################

    for fold_dir in fold_dirs:

        missing_files = []
        empty_files = []

        for filename in required_fold_files:

            file_path = os.path.join(
                fold_dir,
                filename
            )

            if not os.path.isfile(
                file_path
            ):
                missing_files.append(
                    filename
                )

            elif os.path.getsize(
                file_path
            ) == 0:
                empty_files.append(
                    filename
                )

        if missing_files:
            raise RuntimeError(
                "Missing artifacts in "
                f"{fold_dir}: "
                + ", ".join(
                    missing_files
                )
            )

        if empty_files:
            raise RuntimeError(
                "Empty artifacts in "
                f"{fold_dir}: "
                + ", ".join(
                    empty_files
                )
            )

    ########################################################
    # Create archive atomically
    ########################################################

    archive_path = os.path.join(
        args.output,
        "fold_artifacts.tar.gz"
    )

    temporary_archive = (
        archive_path + ".tmp"
    )

    if os.path.exists(
        temporary_archive
    ):
        os.remove(
            temporary_archive
        )

    with tarfile.open(
        temporary_archive,
        "w:gz"
    ) as archive:

        for fold_dir in fold_dirs:

            archive.add(
                fold_dir,
                arcname=os.path.basename(
                    fold_dir
                )
            )

    ########################################################
    # Validate generated archive
    ########################################################

    if (
        not os.path.isfile(
            temporary_archive
        )
        or os.path.getsize(
            temporary_archive
        ) == 0
    ):
        raise RuntimeError(
            "Fold artifact archive "
            "was not created correctly."
        )

    with tarfile.open(
        temporary_archive,
        "r:gz"
    ) as archive:

        archived_files = {
            member.name
            for member
            in archive.getmembers()
            if member.isfile()
        }

    expected_archive_files = {
        f"{fold_name}/{filename}"
        for fold_name
        in expected_fold_names
        for filename
        in required_fold_files
    }

    missing_from_archive = sorted(
        expected_archive_files
        - archived_files
    )

    if missing_from_archive:
        raise RuntimeError(
            "Archive validation failed. "
            "Missing files: "
            + ", ".join(
                missing_from_archive
            )
        )

    ########################################################
    # Publish validated archive
    ########################################################

    os.replace(
        temporary_archive,
        archive_path
    )

    print(
        "Fold artifacts archived:",
        archive_path
    )



if __name__ == "__main__":

    main()