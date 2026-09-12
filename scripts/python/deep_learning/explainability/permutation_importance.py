#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
permutation_importance.py

Permutation Feature Importance
for PyTorch Models
"""

############################################################
# Standard Library
############################################################



import os

############################################################
# Scientific Computing
############################################################

import numpy as np

import pandas as pd



############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################

from deep_learning.train import predict





############################################################
# Baseline Score
############################################################

def compute_baseline_score(

    model,

    dataloader,

    y_true,

    device

):
    """
    Compute baseline performance before permutation.

    Parameters
    ----------
    model : torch.nn.Module

    dataloader : DataLoader

    y_true : numpy.ndarray

    device : torch.device

    Returns
    -------
    baseline_metrics : dict

    baseline_score : float
    """

    ########################################################
    # Prediction
    ########################################################

    prediction = predict(

        model=model,

        dataloader=dataloader,

        device=device

    )

    ########################################################
    # Evaluation
    ########################################################

    baseline_metrics = evaluate(

        y_true=y_true,

        y_pred=prediction,

        y_prob=None

    )

    ########################################################
    # Main Score
    ########################################################

    baseline_score = baseline_metrics[

        "Accuracy"

    ]

    ########################################################

    return (

        baseline_metrics,

        baseline_score

    )



############################################################
# Permutation Loop
############################################################

def permutation_importance(

    model,

    X,

    y,

    dataloader_builder,

    device,

    baseline_score,

    random_seed=2026

):
    """
    Compute permutation feature importance.

    Parameters
    ----------
    model : torch.nn.Module

    X : pandas.DataFrame

    y : pandas.Series

    dataloader_builder : callable
        Function that builds DataLoader
        from X and y.

    device : torch.device

    baseline_score : float

    random_seed : int

    Returns
    -------
    importance : dict
    """

    ########################################################
    # Random Seed
    ########################################################

    np.random.seed(

        random_seed

    )

    ########################################################
    # Output
    ########################################################

    importance = {}

    ########################################################
    # Loop Features
    ########################################################

    for feature in X.columns:

        ####################################################
        # Copy Dataset
        ####################################################

        X_perm = X.copy(

            deep=True

        )

        ####################################################
        # Shuffle Feature
        ####################################################

        X_perm[feature] = np.random.permutation(

            X_perm[feature].values

        )

        ####################################################
        # Build DataLoader
        ####################################################

        perm_loader = dataloader_builder(

            X_perm,

            y

        )

        ####################################################
        # Predict
        ####################################################

        prediction = predict(

            model=model,

            dataloader=perm_loader,

            device=device

        )

        ####################################################
        # Evaluate
        ####################################################

        metrics = evaluate(

            y_true=y.values,

            y_pred=prediction,

            y_prob=None

        )

        ####################################################
        # Importance
        ####################################################

        importance[feature] = (

            baseline_score

            -

            metrics["Accuracy"]

        )

    ########################################################

    return importance



############################################################
# Importance DataFrame
############################################################

def importance_dataframe(

    importance_dict

):
    """
    Convert permutation importance dictionary
    to pandas DataFrame.

    Parameters
    ----------
    importance_dict : dict

    Returns
    -------
    importance_df : pandas.DataFrame
    """

    ########################################################
    # Dictionary -> DataFrame
    ########################################################

    importance_df = pd.DataFrame(

        {

            "Feature": list(

                importance_dict.keys()

            ),

            "Importance": list(

                importance_dict.values()

            )

        }

    )

    ########################################################
    # Sort
    ########################################################

    importance_df = importance_df.sort_values(

        by="Importance",

        ascending=False

    )

    ########################################################
    # Reset Index
    ########################################################

    importance_df = importance_df.reset_index(

        drop=True

    )

    ########################################################
    # Ranking
    ########################################################

    importance_df.insert(

        0,

        "Rank",

        np.arange(

            1,

            len(

                importance_df

            ) + 1

        )

    )

    ########################################################

    return importance_df





############################################################
# Save Results
############################################################

def save_results(

    importance_df,

    output_dir,

    file_name="permutation_importance.tsv"

):
    """
    Save permutation feature importance.

    Parameters
    ----------
    importance_df : pandas.DataFrame

    output_dir : str

    file_name : str
    """

    ########################################################
    # Output Directory
    ########################################################

    os.makedirs(

        output_dir,

        exist_ok=True

    )

    ########################################################
    # Output File
    ########################################################

    output_file = os.path.join(

        output_dir,

        file_name

    )

    ########################################################
    # Save
    ########################################################

    importance_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )

    ########################################################

    print(

        f"Permutation importance saved to:\n{output_file}"

    )

    ########################################################

    return output_file





############################################################
# Bar Plot
############################################################

def plot_feature_importance(

    importance_df,

    output_file,

    top_k=20

):

    plot_df = importance_df.head(

        top_k

    )

    plt.figure(

        figsize=(10,8)

    )

    plt.barh(

        plot_df["Feature"],

        plot_df["Importance"]

    )

    plt.gca().invert_yaxis()

    plt.xlabel(

        "Permutation Importance"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Ranking Plot
############################################################

def plot_ranking(

    importance_df,

    output_file,

    top_k=30

):

    plot_df = importance_df.head(

        top_k

    )

    plt.figure(

        figsize=(12,10)

    )

    plt.barh(

        plot_df["Feature"],

        plot_df["Importance"]

    )

    plt.gca().invert_yaxis()

    plt.ylabel(

        "Features"

    )

    plt.xlabel(

        "Importance"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Distribution
############################################################

def plot_distribution(

    importance_df,

    output_file

):

    plt.figure(

        figsize=(8,6)

    )

    plt.hist(

        importance_df["Importance"],

        bins=40

    )

    plt.xlabel(

        "Permutation Importance"

    )

    plt.ylabel(

        "Frequency"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Cumulative Importance
############################################################

def plot_cumulative(

    importance_df,

    output_file

):

    cumulative = importance_df["Importance"].cumsum()


    if cumulative.iloc[-1] != 0:
        cumulative /= cumulative.iloc[-1]

    plt.figure(

        figsize=(8,6)

    )

    plt.plot(

        cumulative.values

    )

    plt.xlabel(

        "Number of Features"

    )

    plt.ylabel(

        "Cumulative Importance"

    )

    plt.grid(

        True

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



