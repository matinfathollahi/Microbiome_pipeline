#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
latent_representation.py

Extract Latent Representations
from trained PyTorch models.
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

import json

from deep_learning.models.mlp import build_mlp

############################################################
# Deep Learning
############################################################
import torch.nn as nn
import torch

############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################


############################################################
# Feature Extractor
############################################################
class FeatureExtractor(torch.nn.Module):
    """
    Extract latent representation before the final classifier layer.
    """

    def __init__(self, model):

        super().__init__()

        self.feature_layers = nn.Sequential(
            *list(model.network.children())[:-1]
        )

    def forward(self, x):

        return self.feature_layers(x)

############################################################
# Extract Latent Features
############################################################

def extract_latent_features(

    extractor,

    dataloader,

    device

):
    """
    Extract latent representations from a trained model.

    Parameters
    ----------
    extractor : FeatureExtractor

    dataloader : DataLoader

    device : torch.device

    Returns
    -------
    latent_features : numpy.ndarray
        (samples × latent_dimension)
    """

    ########################################################
    # Evaluation Mode
    ########################################################

    extractor.eval()

    ########################################################
    # Storage
    ########################################################

    latent_features = []

    ########################################################
    # Disable Gradient
    ########################################################

    with torch.no_grad():

        ####################################################
        # Loop DataLoader
        ####################################################

        for batch in dataloader:

            ################################################
            # Input
            ################################################

            x = batch[0].to(

                device

            )

            ################################################
            # Forward
            ################################################

            latent = extractor(

                x

            )

            ################################################
            # Save
            ################################################

            latent_features.append(

                latent.cpu()

            )

    ########################################################
    # Concatenate
    ########################################################

    latent_features = torch.cat(

        latent_features,

        dim=0

    )

    ########################################################
    # Convert to NumPy
    ########################################################

    latent_features = latent_features.numpy()

    ########################################################

    return latent_features



############################################################
# Save Latent Matrix
############################################################

def save_latent_matrix(

    latent_features,

    output_dir,

    file_name="latent_features.tsv",

    sample_ids=None

):
    """
    Save latent representations.

    Parameters
    ----------
    latent_features : numpy.ndarray

    output_dir : str

    file_name : str

    sample_ids : array-like or None

    Returns
    -------
    latent_df : pandas.DataFrame
    """

    ########################################################
    # Output Directory
    ########################################################

    os.makedirs(

        output_dir,

        exist_ok=True

    )

    ########################################################
    # Column Names
    ########################################################

    columns = [

        f"Latent_{i+1}"

        for i in range(

            latent_features.shape[1]

        )

    ]

    ########################################################
    # DataFrame
    ########################################################

    latent_df = pd.DataFrame(

        latent_features,

        columns=columns

    )

    ########################################################
    # Sample IDs
    ########################################################

    if sample_ids is not None:

        latent_df.insert(

            0,

            "SampleID",

            sample_ids

        )

    ########################################################
    # Save
    ########################################################

    output_file = os.path.join(

        output_dir,

        file_name

    )

    latent_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )

    ########################################################

    print(

        f"Latent features saved to:\n{output_file}"

    )

    ########################################################

    return latent_df



############################################################
# Latent Statistics
############################################################

def latent_statistics(

    latent_df

):
    """
    Compute statistics of latent representations.

    Parameters
    ----------
    latent_df : pandas.DataFrame

    Returns
    -------
    stats : pandas.DataFrame
    """

    ########################################################
    # Select Latent Columns
    ########################################################

    latent_columns = [

        col

        for col in latent_df.columns

        if col.startswith(

            "Latent_"

        )

    ]

    ########################################################
    # Statistics
    ########################################################

    stats = pd.DataFrame(

        {

            "Mean": latent_df[latent_columns].mean(),

            "Std": latent_df[latent_columns].std(),

            "Min": latent_df[latent_columns].min(),

            "Max": latent_df[latent_columns].max(),

            "Median": latent_df[latent_columns].median()

        }

    )

    ########################################################

    return stats


############################################################
# Save Statistics
############################################################

def save_statistics(

    stats,

    output_dir,

    file_name="latent_statistics.tsv"

):
    """
    Save latent statistics.
    """

    os.makedirs(

        output_dir,

        exist_ok=True

    )

    output_file = os.path.join(

        output_dir,

        file_name

    )

    stats.to_csv(

        output_file,

        sep="\t"

    )

    print(

        f"Statistics saved to:\n{output_file}"

    )

    return output_file


############################################################
# Latent Heatmap
############################################################

def plot_latent_heatmap(

    latent_df,

    output_file,

    max_samples=50

):

    latent_columns = [

        col

        for col in latent_df.columns

        if col.startswith(

            "Latent_"

        )

    ]

    plt.figure(

        figsize=(14,8)

    )

    plt.imshow(

        latent_df[latent_columns].iloc[:max_samples],

        aspect="auto",

        cmap="viridis"

    )

    plt.colorbar(

        label="Activation"

    )

    plt.xlabel(

        "Latent Dimensions"

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
# Latent Distribution
############################################################

def plot_latent_distribution(

    latent_df,

    output_file

):

    latent_columns = [

        col

        for col in latent_df.columns

        if col.startswith(

            "Latent_"

        )

    ]

    plt.figure(

        figsize=(8,6)

    )

    plt.hist(

        latent_df[latent_columns].values.ravel(),

        bins=100

    )

    plt.xlabel(

        "Latent Value"

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
# Mean Activation
############################################################

def plot_mean_activation(

    latent_df,

    output_file

):

    latent_columns = [

        col

        for col in latent_df.columns

        if col.startswith(

            "Latent_"

        )

    ]

    mean_activation = latent_df[

        latent_columns

    ].mean(

        axis=0

    )

    plt.figure(

        figsize=(12,6)

    )

    plt.plot(

        mean_activation.values

    )

    plt.xlabel(

        "Latent Dimension"

    )

    plt.ylabel(

        "Mean Activation"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Latent Standard Deviation
############################################################

def plot_std_activation(

    latent_df,

    output_file

):

    latent_columns = [

        col

        for col in latent_df.columns

        if col.startswith(

            "Latent_"

        )

    ]

    std_activation = latent_df[

        latent_columns

    ].std(

        axis=0

    )

    plt.figure(

        figsize=(12,6)

    )

    plt.plot(

        std_activation.values

    )

    plt.xlabel(

        "Latent Dimension"

    )

    plt.ylabel(

        "Standard Deviation"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Load Feature Extractor
############################################################




def load_feature_extractor(
    checkpoint_path,
    parameter_file,
    input_dim,
    output_dim,
    device
):

    ########################################################
    # Load Parameters
    ########################################################

    with open(parameter_file, "r") as f:

        params = json.load(f)


    ########################################################
    # Extract best parameters
    ########################################################

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
        checkpoint_path,
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
    # Device
    ########################################################

    model.to(device)

    model.eval()


    ########################################################
    # Feature Extractor
    ########################################################

    extractor = FeatureExtractor(model)


    return extractor

