#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
base.py

Core utilities for Machine Learning / Deep Learning pipeline.

Author : Your Name
Project: Microbiome Meta-analysis + Machine Learning Pipeline
"""

############################################################
# Standard Library
############################################################

import os
import json
import random
import logging
from pathlib import Path
from sklearn.model_selection import cross_val_score

from optuna.samplers import TPESampler

############################################################
# Third-party
############################################################

import joblib
import numpy as np
import pandas as pd
import optuna

from sklearn.metrics import (

    accuracy_score,

    balanced_accuracy_score,

    precision_score,

    recall_score,

    f1_score,

    matthews_corrcoef,

    roc_auc_score,

    confusion_matrix

)



from sklearn.preprocessing import LabelBinarizer



############################################################
# Logging
############################################################

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s | %(levelname)s | %(message)s"

)

logger = logging.getLogger(__name__)

############################################################
# Global Constants
############################################################

DEFAULT_RANDOM_SEED = 2026

############################################################
# Utility Functions
############################################################

def ensure_dir(path):
    """
    Create directory if it does not exist.
    """

    Path(path).mkdir(

        parents=True,

        exist_ok=True

    )


############################################################

def set_seed(seed=DEFAULT_RANDOM_SEED):
    """
    Set all random seeds for reproducibility.
    """

    random.seed(seed)

    np.random.seed(seed)

    os.environ["PYTHONHASHSEED"] = str(seed)


############################################################

def save_json(obj, outfile):
    """
    Save Python object as JSON.
    """

    with open(outfile, "w") as f:

        json.dump(

            obj,

            f,

            indent=4,
            default=float

        )


############################################################

def load_json(infile):
    """
    Load JSON file.
    """

    with open(infile) as f:

        return json.load(f)


############################################################

def save_table(df, outfile):
    """
    Save dataframe as TSV.
    """

    df.to_csv(

        outfile,

        sep="\t",

        index=False

    )


############################################################

def load_table(infile):
    """
    Load TSV table.
    """

    return pd.read_csv(

        infile,

        sep="\t"

    )


############################################################

def save_pickle(obj, outfile):
    """
    Save object with joblib.
    """

    joblib.dump(

        obj,

        outfile

    )


############################################################

def load_pickle(infile):
    """
    Load object with joblib.
    """

    return joblib.load(

        infile

    )


############################################################

def print_header(title):
    """
    Pretty console header.
    """

    logger.info("=" * 60)

    logger.info(title)

    logger.info("=" * 60)


############################################################

############################################################
# Dataset Loader
############################################################

def load_dataset(

    input_file,

    label_column

):
    """
    Load machine learning dataset.

    Parameters
    ----------
    input_file : str
        TSV input file

    label_column : str
        Target column name

    Returns
    -------
    X : pandas.DataFrame

    y : pandas.Series
    """

    logger.info(

        f"Loading dataset: {input_file}"

    )

    ########################################################

    df = pd.read_csv(

        input_file,

        sep="\t"

    )

    ########################################################

    if label_column not in df.columns:

        raise ValueError(

            f"Target column '{label_column}' not found."

        )

    ########################################################
    # Remove duplicated samples
    ########################################################

    df = df.drop_duplicates()

    ########################################################
    # Remove missing labels
    ########################################################

    df = df.dropna(

        subset=[label_column]

    )

    ########################################################
    # Separate X / y
    ########################################################

    y = df[label_column].copy()

    X = df.drop(

        columns=[label_column]

    )

    ########################################################
    # Keep only numeric features
    ########################################################

    X = X.select_dtypes(

        include=[

            np.number

        ]

    )

    ########################################################
    # Remove constant features
    ########################################################

    constant = X.columns[

        X.nunique() <= 1

    ]

    if len(constant) > 0:

        logger.info(

            f"Removing {len(constant)} constant features"

        )

        X = X.drop(

            columns=constant

        )

    ########################################################
    # Remove columns with missing values
    ########################################################

    missing = X.columns[

        X.isna().any()

    ]

    if len(missing) > 0:

        logger.info(

            f"Removing {len(missing)} features containing NA"

        )

        X = X.drop(

            columns=missing

        )

    ########################################################
    # Remove remaining samples with NA
    ########################################################

    keep = X.notna().all(

        axis=1

    )

    X = X.loc[keep]

    y = y.loc[keep]

    ########################################################

    X = X.reset_index(

        drop=True

    )

    y = y.reset_index(

        drop=True

    )

    ########################################################

    logger.info(

        f"Samples : {X.shape[0]}"

    )

    logger.info(

        f"Features: {X.shape[1]}"

    )

    logger.info(

        f"Classes : {len(np.unique(y))}"

    )

    ########################################################

    return X, y



############################################################
# Model Evaluation
############################################################

############################################################

def evaluate(
    y_true,
    y_pred,
    y_prob
):
    """
    Evaluate classification model.

    Parameters
    ----------
    y_true : array-like

    y_pred : array-like

    y_prob : ndarray
        predict_proba() output

    Returns
    -------
    dict
    """

    ########################################################
    # Basic Metrics
    ########################################################

    accuracy = accuracy_score(

        y_true,

        y_pred

    )

    balanced_accuracy = balanced_accuracy_score(

        y_true,

        y_pred

    )

    precision = precision_score(

        y_true,

        y_pred,

        average="weighted",

        zero_division=0

    )

    recall = recall_score(

        y_true,

        y_pred,

        average="weighted",

        zero_division=0

    )

    f1 = f1_score(

        y_true,

        y_pred,

        average="weighted",

        zero_division=0

    )

    mcc = matthews_corrcoef(

        y_true,

        y_pred

    )

    ########################################################
    # ROC-AUC
    ########################################################

    classes = np.unique(y_true)

    try:

        if len(classes) == 2:

            roc = roc_auc_score(

                y_true,

                y_prob[:, 1]

            )

        else:

            lb = LabelBinarizer()

            y_bin = lb.fit_transform(

                y_true

            )

            roc = roc_auc_score(

                y_bin,

                y_prob,

                average="weighted",

                multi_class="ovr"

            )
 
    except ValueError as e:

        logger.warning(

            f"ROC-AUC could not be computed: {e}"

        )

        roc = np.nan

    ########################################################
    # Confusion Matrix
    ########################################################

    cm = confusion_matrix(

        y_true,

        y_pred

    )

    ########################################################

    return {

        "Accuracy":

            accuracy,

        "BalancedAccuracy":

            balanced_accuracy,

        "Precision":

            precision,

        "Recall":

            recall,

        "F1":

            f1,

        "MCC":

            mcc,

        "ROC_AUC":

            roc,

        "ConfusionMatrix":

            cm

    }




############################################################
# Saving Functions
############################################################



############################################################

def save_model(

    model,

    outfile

):
    """
    Save trained model.
    """

    joblib.dump(

        model,

        outfile

    )


############################################################

def load_model(

    infile

):
    """
    Load trained model.
    """

    return joblib.load(

        infile

    )


############################################################

def save_best_parameters(

    params,

    outfile

):
    """
    Save best hyperparameters.
    """

    with open(

        outfile,

        "w"

    ) as f:

        json.dump(

            params,

            f,

            indent=4,
            default=float

        )


############################################################

def save_trials(

    study,

    outfile

):
    """
    Save Optuna trials.
    """

    df = study.trials_dataframe()

    df.to_csv(

        outfile,

        sep="\t",

        index=False

    )


############################################################

def save_metrics(

    metrics,

    outfile

):
    """
    Save evaluation metrics.
    """

    metrics = metrics.copy()

    if "ConfusionMatrix" in metrics:

        del metrics["ConfusionMatrix"]

    df = pd.DataFrame(

        [metrics]

    )

    df.to_csv(

        outfile,

        sep="\t",

        index=False

    )


############################################################

def save_confusion_matrix(

    y_true,

    y_pred,

    outfile

):
    """
    Save confusion matrix.
    """

    cm = confusion_matrix(

        y_true,

        y_pred

    )

    df = pd.DataFrame(

        cm

    )

    df.to_csv(

        outfile,

        sep="\t",

        index=False

    )


############################################################

def save_feature_importance(

    feature_names,

    importance,

    outfile

):
    """
    Save feature importance.
    """
    if len(feature_names) != len(importance):
        raise ValueError(
            f"feature_names ({len(feature_names)}) and "
            f"importance ({len(importance)}) must have the same length."
        )

    df = pd.DataFrame(

        {

            "Feature": feature_names,

            "Importance": importance

        }

    )

    df = df.sort_values(

        "Importance",

        ascending=False

    )

    df.to_csv(

        outfile,

        sep="\t",

        index=False

    )


############################################################

def save_summary(

    results,

    outfile

):
    """
    Save Nested CV summary.
    """

    summary = results.mean(

        numeric_only=True

    )

    summary = pd.DataFrame(

        summary,

        columns=["Mean"]

    )

    summary.to_csv(

        outfile,

        sep="\t"

    )


############################################################

def save_predictions(

    sample_ids,

    y_true,

    y_pred,

    probability,

    outfile

):
    """
    Save predictions.
    """

    df = pd.DataFrame(

        {

            "SampleID":

                sample_ids,

            "True":

                y_true,

            "Predicted":

                y_pred

        }

    )

    if probability.ndim == 2:

        for i in range(

            probability.shape[1]

        ):

            df[f"Probability_Class{i}"] = probability[:, i]

    df.to_csv(

        outfile,

        sep="\t",

        index=False

    )


############################################################

def save_runtime(

    runtime,

    outfile

):
    """
    Save runtime.
    """

    pd.DataFrame(

        {

            "Runtime_seconds":

                [runtime]

        }

    ).to_csv(

        outfile,

        sep="\t",

        index=False

    )



############################################################
# Nested Cross Validation
############################################################

def run_nested_cv(

    X,

    y,

    builder,

    search_space,

    outer_cv,

    inner_cv,

    n_trials,

    timeout,

    random_seed

):

    outer_results = []

    best_parameters = []

    studies = []

    models = []

    ########################################################

    for fold, (train_idx, valid_idx) in enumerate(

        outer_cv.split(

            X,

            y

        )

    ):

        logger.info(f"Outer Fold {fold + 1}")

        ####################################################

        X_train = X.iloc[train_idx]

        X_valid = X.iloc[valid_idx]

        y_train = y.iloc[train_idx]

        y_valid = y.iloc[valid_idx]

        ####################################################
        # Objective
        ####################################################

        def objective(

            trial

        ):

            params = search_space(

                trial

            )

            model = builder(

                params,

                random_seed

            )


            if len(np.unique(y_train)) == 2:
                scoring = "roc_auc"
            else:
                scoring = "roc_auc_ovr_weighted"

            scores = cross_val_score(
                estimator=model,
                X=X_train,
                y=y_train,
                cv=inner_cv,
                scoring=scoring,
                n_jobs=-1
            )

            return np.mean(

                scores

            )

        ####################################################

        study = optuna.create_study(
            direction="maximize",
            sampler=TPESampler(seed=random_seed)
        )

        ####################################################

        study.optimize(

            objective,

            n_trials=n_trials,

            timeout=timeout,

            show_progress_bar=False

        )

        ####################################################

        params = study.best_params

        ####################################################

        model = builder(

            params,

            random_seed

        )

        ####################################################

        model.fit(

            X_train,

            y_train

        )

        ####################################################

        prediction = model.predict(

            X_valid

        )

        ####################################################

        probability = model.predict_proba(

            X_valid

        )

        ####################################################

        metrics = evaluate(

            y_valid,

            prediction,

            probability

        )

        metrics["Fold"] = fold + 1

        ####################################################

        outer_results.append(

            metrics

        )

        ####################################################

        best_parameters.append(

            params

        )

        ####################################################

        studies.append(

            study

        )

        ####################################################

        models.append(

            model

        )

    ########################################################

    results = pd.DataFrame(

        outer_results

    )

    ########################################################

    return {

        "results": results,

        "parameters": best_parameters,

        "studies": studies,

        "models": models

    }




############################################################
# Final Model Training
############################################################

def train_final_model(
    X,
    y,
    builder,
    best_params,
    random_seed
):
    """
    Train the final model on the complete dataset.

    Parameters
    ----------
    X : pandas.DataFrame
        Feature matrix

    y : pandas.Series
        Target labels

    builder : callable
        Model builder function
        (e.g. MODEL_BUILDERS["rf"])

    best_params : dict
        Final hyperparameters

    random_seed : int

    Returns
    -------
    model
        Trained model
    """

    logger.info(
        "Training final model on the complete dataset..."
    )

    ########################################################

    model = builder(
        best_params,
        random_seed
    )

    ########################################################

    model.fit(
        X,
        y
    )

    ########################################################

    logger.info(
        "Final model training completed."
    )

    return model



############################################################
# Main Helpers
############################################################

import time
import platform
import sys
from datetime import datetime

############################################################

def start_timer():
    """
    Start runtime timer.
    """

    return time.perf_counter()


############################################################

def stop_timer(start):
    """
    Stop timer.

    Returns
    -------
    seconds
    """

    return time.perf_counter() - start


############################################################

def system_information():
    """
    Return system information.
    """

    return {

        "Python":

            sys.version,

        "Platform":

            platform.platform(),

        "Processor":

            platform.processor(),

        "Time":

            datetime.now().strftime(

                "%Y-%m-%d %H:%M:%S"

            )

    }


############################################################

def log_system_information():
    """
    Print system information.
    """

    info = system_information()

    logger.info("System Information")

    for k, v in info.items():

        logger.info(

            f"{k}: {v}"

        )


############################################################

def log_dataset_information(

    X,

    y

):
    """
    Dataset summary.
    """

    logger.info(

        f"Samples : {X.shape[0]}"

    )

    logger.info(

        f"Features: {X.shape[1]}"

    )

    logger.info(

        f"Classes : {len(np.unique(y))}"

    )


############################################################

def log_fold_result(

    fold,

    metrics

):
    """
    Log one outer fold.
    """

    logger.info(

        f"Fold {fold}"

    )

    logger.info(

        f"Accuracy           : {metrics['Accuracy']:.4f}"

    )

    logger.info(

        f"Balanced Accuracy  : {metrics['BalancedAccuracy']:.4f}"

    )

    logger.info(

        f"Precision          : {metrics['Precision']:.4f}"

    )

    logger.info(

        f"Recall             : {metrics['Recall']:.4f}"

    )

    logger.info(

        f"F1                 : {metrics['F1']:.4f}"

    )

    logger.info(

        f"MCC                : {metrics['MCC']:.4f}"

    )

    logger.info(

        f"ROC-AUC            : {metrics['ROC_AUC']:.4f}"

    )


############################################################

def log_summary(

    summary

):
    """
    Print Nested CV summary.
    """

    logger.info("")

    logger.info("Nested CV Summary")

    logger.info("-----------------------------")

    for k, v in summary.items():

        if np.isscalar(v):

            logger.info(

                f"{k:<25}: {v:.4f}"

            )


############################################################

def banner(

    title

):
    """
    Pretty banner.
    """

    logger.info("")

    logger.info("=" * 70)

    logger.info(title)

    logger.info("=" * 70)

    logger.info("")


############################################################

def finish_pipeline(

    runtime

):
    """
    Finish message.
    """

    logger.info("")

    logger.info("=" * 70)

    logger.info("Pipeline Finished Successfully")

    logger.info(

        f"Runtime: {runtime:.2f} seconds"

    )

    logger.info("=" * 70)

    logger.info("")