#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
local_explanation.py

Local explanation for individual samples using
SHAP and Integrated Gradients.
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
# PyTorch
############################################################

import torch

############################################################
# Explainability
############################################################

import shap

from captum.attr import IntegratedGradients

############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################

from deep_learning.models.mlp import MLP




############################################################
# Load Model
############################################################

def load_model(

    checkpoint_path,

    input_dim,

    hidden_dims,

    output_dim,

    device

):
    """
    Load trained MLP model.

    Parameters
    ----------
    checkpoint_path : str

    input_dim : int

    hidden_dims : list[int]

    output_dim : int

    device : torch.device

    Returns
    -------
    model : torch.nn.Module
    """

    ########################################################
    # Build Model
    ########################################################

    model = MLP(

        input_dim=input_dim,

        hidden_dims=hidden_dims,

        output_dim=output_dim

    )

    ########################################################
    # Load Checkpoint
    ########################################################

    checkpoint = torch.load(

        checkpoint_path,

        map_location=device

    )

    ########################################################
    # Load Weights
    ########################################################

    if "model_state_dict" in checkpoint:

        model.load_state_dict(

            checkpoint["model_state_dict"]

        )

    else:

        model.load_state_dict(

            checkpoint

        )

    ########################################################
    # Device
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
# Load Sample
############################################################

def load_sample(

    data_df,

    sample_index,

    feature_columns,

    device

):
    """
    Load a single sample for local explanation.

    Parameters
    ----------
    data_df : pandas.DataFrame

    sample_index : int

    feature_columns : list[str]

    device : torch.device

    Returns
    -------
    sample_tensor : torch.Tensor

    sample_df : pandas.DataFrame
    """

    ########################################################
    # Select Sample
    ########################################################

    sample_df = data_df.iloc[

        [sample_index]

    ]

    ########################################################
    # Feature Matrix
    ########################################################

    X = sample_df[

        feature_columns

    ].values.astype(

        np.float32

    )

    ########################################################
    # Tensor
    ########################################################

    sample_tensor = torch.tensor(

        X,

        dtype=torch.float32,

        device=device

    )

    ########################################################

    return (

        sample_tensor,

        sample_df

    )



############################################################
# SHAP Local Values
############################################################

def compute_shap_local(

    model,

    background_tensor,

    sample_tensor

):
    """
    Compute SHAP values for a single sample.

    Parameters
    ----------
    model : torch.nn.Module

    background_tensor : torch.Tensor

    sample_tensor : torch.Tensor

    Returns
    -------
    shap_values : numpy.ndarray
    """

    background_tensor = background_tensor.to(
        device=sample_tensor.device,
        dtype=sample_tensor.dtype
    )
    ########################################################
    # SHAP Explainer
    ########################################################

    try:
        explainer = shap.DeepExplainer(
            model,
            background_tensor
        )
    except Exception:
        explainer = shap.GradientExplainer(
            model,
            background_tensor
        )

    ########################################################
    # SHAP Values
    ########################################################

    shap_values = explainer.shap_values(

        sample_tensor

    )

    ########################################################
    # Binary Classification
    ########################################################

    if isinstance(shap_values, list):
        shap_values = shap_values[-1]

    elif isinstance(shap_values, np.ndarray):
        if shap_values.ndim == 3:
            shap_values = shap_values[:, :, -1]
        elif shap_values.ndim != 2:
            raise ValueError(
                f"Unexpected SHAP output shape: {shap_values.shape}"
            )
    ########################################################

    return shap_values



############################################################
# Integrated Gradients Local
############################################################

def compute_integrated_gradients_local(

    model,

    sample_tensor,

    target=None,

    n_steps=100

):
    """
    Compute Integrated Gradients for a single sample.

    Parameters
    ----------
    model : torch.nn.Module

    sample_tensor : torch.Tensor

    target : int or None

    n_steps : int

    Returns
    -------
    attributions : numpy.ndarray
    """

    ########################################################
    # Integrated Gradients
    ########################################################

    ig = IntegratedGradients(

        model

    )

    ########################################################
    # Baseline
    ########################################################

    baseline = torch.zeros_like(

        sample_tensor

    )

    ########################################################
    # Target Class
    ########################################################

    if target is None:

        with torch.no_grad():

            prediction = model(

                sample_tensor

            )

            target = prediction.argmax(

                dim=1

            ).item()

    ########################################################
    # Attribution
    ########################################################

    attributions = ig.attribute(

        inputs=sample_tensor,

        baselines=baseline,

        target=target,

        n_steps=n_steps

    )

    ########################################################

    return (

        attributions

        .detach()

        .cpu()

        .numpy()

    )


############################################################
# Local Importance DataFrame
############################################################

def create_local_importance_dataframe(

    feature_names,

    shap_values,

    ig_values

):
    """
    Create local feature importance DataFrame.

    Parameters
    ----------
    feature_names : list[str]

    shap_values : numpy.ndarray

    ig_values : numpy.ndarray

    Returns
    -------
    local_df : pandas.DataFrame
    """

    ########################################################
    # Flatten
    ########################################################

    shap_values = np.asarray(

        shap_values

    ).flatten()

    ig_values = np.asarray(

        ig_values

    ).flatten()

    ########################################################
    # DataFrame
    ########################################################

    local_df = pd.DataFrame(

        {

            "Feature": feature_names,

            "SHAP": shap_values,

            "IntegratedGradients": ig_values

        }

    )

    ########################################################
    # Absolute Scores
    ########################################################

    local_df["AbsSHAP"] = (

        np.abs(

            local_df["SHAP"]

        )

    )

    local_df["AbsIG"] = (

        np.abs(

            local_df["IntegratedGradients"]

        )

    )

    ########################################################
    # Mean Local Importance
    ########################################################

    local_df["LocalImportance"] = (

        local_df[

            [

                "AbsSHAP",

                "AbsIG"

            ]

        ]

        .mean(

            axis=1

        )

    )

    ########################################################
    # Ranking
    ########################################################

    local_df = local_df.sort_values(

        by="LocalImportance",

        ascending=False

    ).reset_index(

        drop=True

    )

    ########################################################
    # Rank
    ########################################################

    local_df.insert(

        0,

        "Rank",

        range(

            1,

            len(local_df)+1

        )

    )

    ########################################################

    return local_df



############################################################
# Save Results
############################################################

def save_results(

    local_df,

    output_dir,

    sample_id,

    file_name=None

):
    """
    Save local explanation results.

    Parameters
    ----------
    local_df : pandas.DataFrame

    output_dir : str

    sample_id : str

    file_name : str or None

    Returns
    -------
    output_file : str
    """

    ########################################################
    # Output Directory
    ########################################################

    os.makedirs(

        output_dir,

        exist_ok=True

    )

    ########################################################
    # File Name
    ########################################################

    if file_name is None:

        file_name = (

            f"{sample_id}_local_importance.tsv"

        )

    ########################################################
    # TSV
    ########################################################

    output_file = os.path.join(

        output_dir,

        file_name

    )

    local_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )

    ########################################################
    # CSV
    ########################################################

    csv_file = os.path.join(

        output_dir,

        f"{sample_id}_local_importance.csv"

    )

    local_df.to_csv(

        csv_file,

        index=False

    )

    ########################################################
    # JSON
    ########################################################

    json_file = os.path.join(

        output_dir,

        f"{sample_id}_local_importance.json"

    )

    local_df.to_json(

        json_file,

        orient="records",

        indent=4

    )

    ########################################################

    print(

        f"Local explanation saved to:\n{output_file}"

    )

    ########################################################

    return output_file



############################################################
# Local Feature Importance
############################################################

def plot_local_importance(

    local_df,

    output_file,

    top_k=20

):
    """
    Plot local feature importance.
    """

    ########################################################
    # Top Features
    ########################################################

    top_df = local_df.head(

        top_k

    )

    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(10,8)

    )

    plt.barh(

        top_df["Feature"],

        top_df["LocalImportance"]

    )

    plt.gca().invert_yaxis()

    plt.xlabel(

        "Local Importance"

    )

    plt.ylabel(

        "Feature"

    )

    plt.title(

        f"Top {top_k} Local Features"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# SHAP vs Integrated Gradients
############################################################

def plot_local_comparison(

    local_df,

    output_file,

    top_k=15

):
    """
    Compare SHAP and Integrated Gradients.
    """

    ########################################################
    # Top Features
    ########################################################

    top_df = local_df.head(

        top_k

    )

    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(12,6)

    )

    x = np.arange(

        len(top_df)

    )

    width = 0.35

    ########################################################

    plt.bar(

        x-width/2,

        top_df["AbsSHAP"],

        width,

        label="|SHAP|"

    )

    plt.bar(

        x+width/2,

        top_df["AbsIG"],

        width,

        label="|Integrated Gradients|"

    )

    ########################################################

    plt.xticks(

        x,

        top_df["Feature"],

        rotation=90

    )

    plt.ylabel(

        "Absolute Attribution"

    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



