#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
optimize.py

Run Optuna Optimization
for Deep Learning Models

Author : Your Name
Project: Microbiome Meta-analysis
"""

############################################################
# Imports
############################################################

import os
os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
import joblib
import json
import argparse
import random

import numpy as np
import pandas as pd

import optuna

import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler
############################################################
# Local Modules
############################################################

from deep_learning.train import get_device

from deep_learning.optuna.objective import objective




############################################################
# Argument Parser
############################################################

def parse_args():

    parser = argparse.ArgumentParser(

        description="Deep Learning Hyperparameter Optimization"

    )

    parser.add_argument(

        "--input",

        required=True,

        help="Raw feature matrix (.tsv)"

    )

    parser.add_argument(

        "--labels",

        required=True,

        help="Class labels (.tsv)"

    )

    parser.add_argument(

        "--output",

        required=True,

        help="Output directory"

    )

    parser.add_argument(

        "--trials",

        type=int,

        default=100,

        help="Number of Optuna trials"

    )

    parser.add_argument(

        "--seed",

        type=int,

        default=2026

    )

    return parser.parse_args()

############################################################
# Load Dataset
############################################################
def load_dataset(

    feature_file,

    label_file

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

    y = y.iloc[:, 0]


    encoder = LabelEncoder()

    y_encoded = encoder.fit_transform(y)


    y = pd.Series(
        y_encoded,
        index=y.index
    )


    print("\nLabel mapping:")

    for label, code in zip(
        encoder.classes_,
        encoder.transform(encoder.classes_)
    ):
        print(f"{label} -> {code}")


    return X, y, encoder

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
        torch.cuda.manual_seed(args.seed)
        torch.cuda.manual_seed_all(args.seed)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)

    ########################################################
    # Device
    ########################################################

    device = get_device()

    ########################################################
    # Dataset
    ########################################################

    X, y, encoder = load_dataset(

        args.input,

        args.labels

    )

    with open(
        os.path.join(args.output, "label_mapping.json"),
        "w"
    ) as f:

        json.dump(
            {
                str(code): str(label)
                for code, label in enumerate(encoder.classes_)
            },
            f,
            indent=4
        )


    print(

        f"Samples : {X.shape[0]}"

    )

    print(

        f"Features : {X.shape[1]}"

    )

    print(

        f"Classes : {len(np.unique(y))}"

    )

    if y.value_counts().min() < 2:
        raise ValueError(
            "Every class must contain at least 2 samples for stratified split."
        )

    X_train, X_valid, y_train, y_valid = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=args.seed
    )

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train).astype(np.float32)

    X_valid = scaler.transform(X_valid).astype(np.float32)

    joblib.dump(
        scaler,
        os.path.join(args.output, "scaler.pkl")
    )

    print("\nDataset split:")
    print(f"Train samples: {X_train.shape[0]}")
    print(f"Valid samples: {X_valid.shape[0]}")

    print("\nTrain class distribution:")
    print(y_train.value_counts())

    print("\nValid class distribution:")
    print(y_valid.value_counts())

    ########################################################
    # Continue in Part 2
    ########################################################






    ########################################################
    # Create Study
    ########################################################

    study = optuna.create_study(

        study_name="MLP_Optimization",

        storage=f"sqlite:///{os.path.join(args.output,'optuna_mlp.db')}",

        load_if_exists=True,

        direction="maximize",

        sampler=optuna.samplers.TPESampler(

            seed=args.seed,

            multivariate=True

        ),

        pruner=optuna.pruners.MedianPruner(

            n_startup_trials=10,

            n_warmup_steps=5

        )

    )

    ########################################################
    # Run Optimization
    ########################################################

    print("\nTensor check:")
    print("X_train:", X_train.shape, X_train.dtype)
    print("X_valid:", X_valid.shape, X_valid.dtype)
    print("y_train:", y_train.shape)
    print("y_valid:", y_valid.shape)



    study.optimize(

        lambda trial: objective(

            trial=trial,

            X_train=X_train,

            y_train=y_train,

            X_valid=X_valid,

            y_valid=y_valid,

            device=device,
            seed=args.seed

        ),

        n_trials=args.trials,

        gc_after_trial=True,

        show_progress_bar=True

    )
    ########################################################
    # Continue in Part 3
    ########################################################




    ########################################################
    # Best Trial
    ########################################################

    print("\n")

    print("=" * 70)

    print("OPTIMIZATION FINISHED")

    print("=" * 70)

    print(

        f"Best ROC-AUC : {study.best_value:.6f}"

    )

    print("\nBest Parameters:")

    for key, value in study.best_params.items():

        print(

            f"{key:20s} : {value}"

        )

    ########################################################
    # Save Best Parameters
    ########################################################

    best_param_file = os.path.join(

        args.output,

        "best_parameters.json"

    )

    with open(

        best_param_file,

        "w"

    ) as f:

        json.dump(

            study.best_params,

            f,

            indent=4

        )

    ########################################################
    # Save Study Table
    ########################################################

    trials = study.trials_dataframe()

    trials.to_csv(

        os.path.join(

            args.output,

            "optuna_trials.tsv"

        ),

        sep="\t",

        index=False

    )

    ########################################################
    # Save Study Object
    ########################################################

    

    joblib.dump(

        study,

        os.path.join(

            args.output,

            "study.pkl"

        )

    )

    ########################################################
    # Save Summary
    ########################################################

    summary = {

        "best_score": float(

            study.best_value

        ),

        "best_trial": int(

            study.best_trial.number

        ),

        "n_trials": len(

            study.trials

        ),

        "optimization_direction": "maximize",

        "model": "MLP"

    }

    with open(

        os.path.join(

            args.output,

            "summary.json"

        ),

        "w"

    ) as f:

        json.dump(

            summary,

            f,

            indent=4

        )

    ########################################################
    # Finished
    ########################################################

    print("\n")

    print("=" * 70)

    print("FILES SAVED")

    print("=" * 70)

    print(

        f"Best Parameters : {best_param_file}"

    )

    print(

        f"Trials          : "

        f"{os.path.join(args.output,'optuna_trials.tsv')}"

    )

    print(

        f"Study           : "

        f"{os.path.join(args.output,'study.pkl')}"

    )

    print(

        f"Summary         : "

        f"{os.path.join(args.output,'summary.json')}"

    )

    print("=" * 70)


if __name__ == "__main__":

    main()