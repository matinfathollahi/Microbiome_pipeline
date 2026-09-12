#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
shap_explainer.py

SHAP Explainability for PyTorch Models
Microbiome Meta-analysis
"""

############################################################
# Standard Library
############################################################



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
# Explainability
############################################################

import shap

############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################

from deep_learning.train import get_device

from deep_learning.models.mlp import build_mlp


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

    output_dim : int

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

    model.load_state_dict(

        state_dict

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
# Prepare Background Data
############################################################

def prepare_background(

    X_train,

    n_background=100,

    random_seed=2026

):
    """
    Select background samples for SHAP.

    Parameters
    ----------
    X_train : pandas.DataFrame
        Training feature matrix.

    n_background : int, default=100
        Number of background samples.

    random_seed : int, default=2026

    Returns
    -------
    background : torch.Tensor
    """

    ########################################################
    # Random Seed
    ########################################################

    np.random.seed(

        random_seed

    )

    ########################################################
    # Number of Samples
    ########################################################

    n_background = min(

        n_background,

        len(X_train)

    )

    ########################################################
    # Random Sampling
    ########################################################

    indices = np.random.choice(

        len(X_train),

        size=n_background,

        replace=False

    )

    ########################################################
    # Background Matrix
    ########################################################

    background = X_train.iloc[

        indices

    ].values

    ########################################################
    # Convert to Tensor
    ########################################################

    background = torch.tensor(

        background,

        dtype=torch.float32

    )

    ########################################################

    return background


############################################################
# Compute SHAP Values
############################################################

def compute_shap_values(

    model,

    background,

    X_explain,

    device

):
    """
    Compute SHAP values for PyTorch model.

    Parameters
    ----------
    model : torch.nn.Module

    background : torch.Tensor

    X_explain : pandas.DataFrame

    device : torch.device

    Returns
    -------
    shap_values
    """

    ########################################################
    # Move Background to Device
    ########################################################

    background = background.to(

        device

    )

    ########################################################
    # Convert Samples
    ########################################################

    samples = torch.tensor(

        X_explain.values,

        dtype=torch.float32

    ).to(

        device

    )

    ########################################################
    # Build Explainer
    ########################################################

    try:

        explainer = shap.DeepExplainer(

            model,

            background

        )

    except Exception:

        explainer = shap.GradientExplainer(

            model,

            background

        )

    ########################################################
    # Compute SHAP
    ########################################################

    shap_values = explainer.shap_values(

        samples

    )

    ########################################################

    if hasattr(explainer, "expected_value"):
        expected_value = explainer.expected_value
    elif hasattr(explainer, "expected_values"):
        expected_value = explainer.expected_values
    else:
        expected_value = None

    return shap_values, expected_value



############################################################
# SHAP Summary Plot
############################################################

def summary_plot(

    shap_values,

    X,

    output_file,

    class_index=0

):
    """
    SHAP Summary Plot

    Parameters
    ----------
    shap_values

    X : pandas.DataFrame

    output_file : str

    class_index : int
    """

    ########################################################
    # Multi-class
    ########################################################

    if isinstance(

        shap_values,

        list

    ):

        values = shap_values[

            class_index

        ]

    ########################################################
    # Binary
    ########################################################

    else:

        values = shap_values

    ########################################################
    # Plot
    ########################################################

    plt.figure(

        figsize=(10,8)

    )

    shap.summary_plot(

        values,

        X,

        show=False

    )

    ########################################################
    # Save
    ########################################################

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()




############################################################
# SHAP Beeswarm Plot
############################################################

def beeswarm_plot(

    shap_values,

    X,

    output_file,

    class_index=0

):

    if isinstance(shap_values, list):

        values = shap_values[class_index]

    else:

        values = shap_values


  

    plt.figure(figsize=(10, 8))

    shap.summary_plot(

        values,

        X,

        plot_type="dot",

        show=False

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# SHAP Bar Plot
############################################################

def bar_plot(

    shap_values,

    X,

    output_file,

    class_index=0

):

    if isinstance(shap_values, list):

        values = shap_values[class_index]

    else:

        values = shap_values

    plt.figure(figsize=(10, 8))

    shap.summary_plot(

        values,

        X,

        plot_type="bar",

        show=False

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# SHAP Waterfall Plot
############################################################

def waterfall_plot(
    shap_values,
    expected_value,
    X,
    sample_index,
    output_file,
    class_index=0
):

    if isinstance(shap_values, list):

        values = shap_values[class_index]

    else:

        values = shap_values




    if expected_value is None:
        raise ValueError(
            "expected_value is unavailable. Use DeepExplainer or compute a base value."
        )


    if isinstance(expected_value, (list, np.ndarray)):
        base_value = expected_value[class_index]
    else:
        base_value = expected_value


    explanation = shap.Explanation(

        values=values[sample_index],

        base_values=base_value,

        data=X.iloc[sample_index].values,

        feature_names=X.columns.tolist()

    )

    plt.figure(figsize=(10, 8))

    shap.plots.waterfall(

        explanation,

        show=False

    )

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# SHAP Force Plot
############################################################

def force_plot(

    shap_values,

    expected_value,     

    X,

    sample_index,

    output_file,

    class_index=0

):

    if isinstance(shap_values, list):

        values = shap_values[class_index]

    else:

        values = shap_values

    if expected_value is None:
        raise ValueError(
            "expected_value is unavailable. Force plot requires expected_value."
        )

   
    if isinstance(expected_value, (list, np.ndarray)):
        base_value = expected_value[class_index]
    else:
        base_value = expected_value

    force = shap.force_plot(

        base_value=base_value,

        shap_values=values[sample_index],

        features=X.iloc[sample_index],

        feature_names=X.columns,

        matplotlib=False

    )

    shap.save_html(

        output_file,

        force

    )



############################################################
# Main
############################################################

if __name__ == "__main__":

    print("This module provides SHAP utility functions.")

    print("Example usage:")

    print("""
device = get_device()

model = load_model(
    model_path="best_model.pt",
    parameter_file="best_parameters.json",
    input_dim=X_train.shape[1],
    output_dim=2,
    device=device
)

background = prepare_background(X_train)

shap_values, expected_value = compute_shap_values(
    model,
    background,
    X_test,
    device
)

summary_plot(
    shap_values,
    X_test,
    "summary.png"
)

waterfall_plot(
    shap_values,
    expected_value,
    X_test,
    sample_index=0,
    output_file="waterfall.png"
)

force_plot(
    shap_values,
    expected_value,
    X_test,
    sample_index=0,
    output_file="force.html"
)
""")
