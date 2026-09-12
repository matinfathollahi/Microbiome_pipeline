#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
integrated_gradients.py

Integrated Gradients Explainability
using Captum
"""

############################################################
# Standard Library
############################################################

import os
import json

############################################################
# Scientific Computing
############################################################

import numpy as np
import pandas as pd

############################################################
# Deep Learning
############################################################

import torch

############################################################
# Captum
############################################################

from captum.attr import IntegratedGradients

############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################

from deep_learning.models.mlp import build_mlp

from deep_learning.train import get_device




############################################################
# Load Trained Model
############################################################

def load_model(

    model_path,

    parameter_file,

    input_dim,

    output_dim,

    device

):
    """
    Load trained MLP model.

    Parameters
    ----------
    model_path : str
        Path to best_model.pt

    parameter_file : str
        Path to best_parameters.json

    input_dim : int
        Number of input features

    output_dim : int
        Number of output classes

    device : torch.device

    Returns
    -------
    model : torch.nn.Module
    """

    ########################################################
    # Load Hyperparameters
    ########################################################

    with open(
        parameter_file,
        "r"
    ) as f:

        params = json.load(
            f
        )

    
    if "best_parameters" in params:
        params = params["best_parameters"]

    ########################################################
    # Build Model
    ########################################################

    model = build_mlp(

        params=params,

        input_dim=input_dim,

        output_dim=output_dim

    )

    ########################################################
    # Load Weights
    ########################################################

    state_dict = torch.load(
        model_path,
        map_location=device
    )

    if "model_state_dict" in state_dict:

        model.load_state_dict(
            state_dict["model_state_dict"]
        )

    else:

        model.load_state_dict(
            state_dict
        )

    ########################################################
    # Move Model
    ########################################################

    model.to(

        device

    )

    ########################################################
    # Evaluation Mode
    ########################################################

    model.eval()

    ########################################################

    return model





############################################################
# Compute Integrated Gradients
############################################################

def compute_integrated_gradients(

    model,

    X,

    device,

    target,

    baseline=None,

    internal_batch_size=64

):
    """
    Compute Integrated Gradients.

    Parameters
    ----------
    model : torch.nn.Module

    X : pandas.DataFrame

    device : torch.device

    target : int or None
        Target class.

    baseline : torch.Tensor or None

    internal_batch_size : int

    Returns
    -------
    attributions : numpy.ndarray

    delta : numpy.ndarray
    """

    ########################################################
    # Convert Samples
    ########################################################

    inputs = torch.tensor(

        X.values,

        dtype=torch.float32

    ).to(

        device

    )

    ########################################################
    # Baseline
    ########################################################

    if baseline is None:

        baseline = torch.zeros_like(

            inputs

        ).to(

            device

        )

    else:

        baseline = baseline.to(

            device

        )




    ########################################################
    # Integrated Gradients
    ########################################################

    ig = IntegratedGradients(

        model

    )

    ########################################################
    # Compute Attribution
    ########################################################

    attributions, delta = ig.attribute(

        inputs,

        baselines=baseline,

        target=target,

        return_convergence_delta=True,

        internal_batch_size=internal_batch_size

    )

    ########################################################
    # Convert to NumPy
    ########################################################

    attributions = (

        attributions

        .detach()

        .cpu()

        .numpy()

    )

    delta = (

        delta

        .detach()

        .cpu()

        .numpy()

    )

    ########################################################

    return (

        attributions,

        delta

    )



############################################################
# Compute Multiclass Integrated Gradients
############################################################

def compute_multiclass_ig(
    model,
    X,
    device,
    n_classes
):

    """
    Compute Integrated Gradients for every class.

    Returns
    -------
    results : dict
        {
            class_id:
            {
                "attributions": ndarray,
                "delta": ndarray
            }
        }
"""

    model.eval()

    results = {}

    for class_id in range(n_classes):

        print(
            f"Computing Integrated Gradients for class {class_id}"
        )

        attr, delta = compute_integrated_gradients(
            model=model,
            X=X,
            device=device,
            target=class_id
        )

        results[class_id] = {

            "attributions": attr,

            "delta": delta

        }


    return aggregate_multiclass_ig(
        results,
        X.columns
    )



def aggregate_multiclass_ig(
    results,
    feature_names
):
    """
    Convert multiclass IG into global importance.
    """

    all_importance = []

    for class_id, values in results.items():

        attr = values["attributions"]

        importance = np.abs(attr).mean(axis=0)

        df = pd.DataFrame({

            "Feature": feature_names,

            "Importance": importance,

            "Class": class_id

        })

        all_importance.append(df)


    class_df = pd.concat(
        all_importance,
        ignore_index=True
    )


    # Average across classes

    global_df = (
        class_df
        .groupby("Feature")
        ["Importance"]
        .mean()
        .reset_index()
    )


    return global_df
############################################################
# Attribution DataFrame
############################################################

def attribution_dataframe(

    attributions,

    X

):
    """
    Convert Integrated Gradients attributions
    to pandas DataFrame.

    Parameters
    ----------
    attributions : numpy.ndarray
        Integrated Gradients values
        (samples × features)

    X : pandas.DataFrame
        Original feature matrix

    Returns
    -------
    attribution_df : pandas.DataFrame
    """

    ########################################################
    # Build DataFrame
    ########################################################

    attribution_df = pd.DataFrame(

        attributions,

        columns=X.columns,

        index=X.index

    )

    ########################################################

    return attribution_df


############################################################
# Save Attribution Table
############################################################

def save_attributions(

    attribution_df,

    output_file

):
    """
    Save Integrated Gradients values.

    Parameters
    ----------
    attribution_df : pandas.DataFrame

    output_file : str
    """

    attribution_df.to_csv(

        output_file,

        sep="\t"

    )



############################################################
# Feature Importance
############################################################

def feature_importance(

    attribution_df

):
    """
    Compute global feature importance from
    Integrated Gradients.

    Parameters
    ----------
    attribution_df : pandas.DataFrame

    Returns
    -------
    importance_df : pandas.DataFrame
    """

    ########################################################
    # Mean Absolute Attribution
    ########################################################

    importance = attribution_df.abs().mean(

        axis=0

    )

    ########################################################
    # DataFrame
    ########################################################

    importance_df = pd.DataFrame({

        "Feature": importance.index,

        "Importance": importance.values

    })

    ########################################################
    # Sort
    ########################################################

    importance_df = importance_df.sort_values(

        by="Importance",

        ascending=False

    ).reset_index(

        drop=True

    )

    ########################################################

    return importance_df



############################################################
# Save Feature Importance
############################################################

def save_feature_importance(

    importance_df,

    output_file

):
    """
    Save feature importance table.
    """

    importance_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )


############################################################
# Feature Importance Bar Plot
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

        "Integrated Gradient Importance"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Attribution Heatmap
############################################################

def plot_heatmap(

    attribution_df,

    output_file,

    max_samples=50

):

    plt.figure(

        figsize=(14,8)

    )

    plt.imshow(

        attribution_df.iloc[:max_samples],

        aspect="auto",

        cmap="coolwarm"

    )

    plt.colorbar(

        label="Integrated Gradient"

    )

    plt.xlabel(

        "Features"

    )

    plt.ylabel(

        "Samples"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Mean Attribution Plot
############################################################

def plot_mean_attribution(

    attribution_df,

    output_file,

    top_k=20

):

    mean_attr = attribution_df.mean(

        axis=0

    )

    mean_attr = mean_attr.reindex(

        mean_attr.abs()

        .sort_values(

            ascending=False

        )

        .index

    )

    mean_attr = mean_attr.head(

        top_k

    )

    plt.figure(

        figsize=(10,8)

    )

    plt.barh(

        mean_attr.index,

        mean_attr.values

    )

    plt.gca().invert_yaxis()

    plt.xlabel(

        "Mean Attribution"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()




############################################################
# Attribution Distribution
############################################################

def plot_distribution(

    attribution_df,

    output_file

):

    plt.figure(

        figsize=(8,6)

    )

    plt.hist(

        attribution_df.values.ravel(),

        bins=100

    )

    plt.xlabel(

        "Integrated Gradient"

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




