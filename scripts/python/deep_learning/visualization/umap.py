#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UMAP Visualization
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
# Dimensionality Reduction
############################################################

import umap

############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################


############################################################
# Fit UMAP
############################################################

def fit_umap(

    latent_df,

    n_components=2,

    n_neighbors=15,

    min_dist=0.1,

    metric="euclidean",

    random_state=42

):
    """
    Compute UMAP embedding.

    Parameters
    ----------
    latent_df : pandas.DataFrame

    n_components : int

    n_neighbors : int

    min_dist : float

    metric : str

    random_state : int

    Returns
    -------
    embedding : numpy.ndarray
    """

    ########################################################
    # Select Latent Features
    ########################################################

    latent_columns = [

        col

        for col in latent_df.columns

        if col.startswith(

            "Latent_"

        )

    ]

########################################################
# Check Latent Features
########################################################

    if not latent_columns:

        raise ValueError(

            "No columns starting with 'Latent_' were found."

        )

########################################################
# Feature Matrix
########################################################

    X = latent_df[

        latent_columns

    ].values

    ########################################################
    # UMAP
    ########################################################

    reducer = umap.UMAP(

        n_components=n_components,

        n_neighbors=n_neighbors,

        min_dist=min_dist,

        metric=metric,

        random_state=random_state

    )

    ########################################################
    # Fit
    ########################################################

    embedding = reducer.fit_transform(

        X

    )

    ########################################################

    return embedding




############################################################
# Create DataFrame
############################################################

def create_umap_dataframe(

    embedding,

    latent_df,

    label_column=None

):
    """
    Create DataFrame from UMAP embedding.

    Parameters
    ----------
    embedding : numpy.ndarray
        Output of fit_umap()

    latent_df : pandas.DataFrame

    label_column : str or None
        Column containing class labels.

    Returns
    -------
    umap_df : pandas.DataFrame
    """

    ########################################################
    # UMAP Coordinates
    ########################################################

    umap_df = pd.DataFrame(

        {

            "UMAP1": embedding[:, 0],

            "UMAP2": embedding[:, 1]

        }

    )

    ########################################################
    # Sample IDs
    ########################################################

    if "SampleID" in latent_df.columns:

        umap_df.insert(

            0,

            "SampleID",

            latent_df["SampleID"].values

        )

    ########################################################
    # Class Labels
    ########################################################

    if (

        label_column is not None

        and

        label_column in latent_df.columns

    ):

        umap_df["Class"] = latent_df[

            label_column

        ].values

    ########################################################

    return umap_df



############################################################
# Save Results
############################################################

def save_results(

    umap_df,

    output_dir,

    file_name="umap_coordinates.tsv"

):
    """
    Save UMAP coordinates.

    Parameters
    ----------
    umap_df : pandas.DataFrame

    output_dir : str

    file_name : str

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
    # Output File
    ########################################################

    output_file = os.path.join(

        output_dir,

        file_name

    )

    ########################################################
    # Save TSV
    ########################################################

    umap_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )

    ########################################################
    # Save CSV
    ########################################################

    csv_file = os.path.join(

        output_dir,

        "umap_coordinates.csv"

    )

    umap_df.to_csv(

        csv_file,

        index=False

    )

    ########################################################
    # Save JSON
    ########################################################

    json_file = os.path.join(

        output_dir,

        "umap_coordinates.json"

    )

    umap_df.to_json(

        json_file,

        orient="records",

        indent=4

    )

    ########################################################

    print(

        f"UMAP coordinates saved to:\n{output_file}"

    )

    ########################################################

    return output_file





############################################################
# UMAP Scatter Plot
############################################################

def plot_umap(

    umap_df,

    output_file,

    label_column="Class",

    point_size=40,

    alpha=0.80

):
    """
    Plot UMAP embedding.

    Parameters
    ----------
    umap_df : pandas.DataFrame

    output_file : str

    label_column : str

    point_size : int

    alpha : float
    """

    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(8,7)

    )

    ########################################################
    # Colored Scatter
    ########################################################

    if (

        label_column is not None

        and

        label_column in umap_df.columns

    ):

        classes = sorted(

            umap_df[label_column].unique()

        )

        cmap = plt.get_cmap(

            "tab10"

        )

        colors = cmap(

            np.linspace(

                0,

                1,

                len(classes)

            )

        )

        for color, cls in zip(

            colors,

            classes

        ):

            mask = (

                umap_df[label_column]

                == cls

            )

            plt.scatter(

                umap_df.loc[mask, "UMAP1"],

                umap_df.loc[mask, "UMAP2"],

                s=point_size,

                alpha=alpha,

                color=color,

                label=str(cls)

            )

        plt.legend(

            title=label_column,

            frameon=False

        )

    ########################################################
    # Single Color
    ########################################################

    else:

        plt.scatter(

            umap_df["UMAP1"],

            umap_df["UMAP2"],

            s=point_size,

            alpha=alpha

        )

    ########################################################
    # Labels
    ########################################################

    plt.xlabel(

        "UMAP 1"

    )

    plt.ylabel(

        "UMAP 2"

    )

    plt.title(

        "UMAP Visualization of Latent Space"

    )

    plt.tight_layout()

    ########################################################
    # Save
    ########################################################

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()





