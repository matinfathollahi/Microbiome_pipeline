#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
t-SNE Visualization
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
# Machine Learning
############################################################

from sklearn.manifold import TSNE

############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt

############################################################
# Local Modules
############################################################




############################################################
# Fit t-SNE
############################################################

def fit_tsne(

    latent_df,

    n_components=2,

    perplexity=30,

    learning_rate="auto",

    n_iter=1000,

    init="pca",

    random_state=42

):
    """
    Compute t-SNE embedding.

    Parameters
    ----------
    latent_df : pandas.DataFrame

    n_components : int

    perplexity : int

    learning_rate : str or float

    n_iter : int

    init : str

    random_state : int

    Returns
    -------
    embedding : numpy.ndarray
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

    X = latent_df[

        latent_columns

    ].values



########################################################
# t-SNE
########################################################

    tsne_kwargs = dict(
        n_components=n_components,
        perplexity=perplexity,
        learning_rate=learning_rate,
        init=init,
        random_state=random_state,
    )

    try:
        tsne = TSNE(
            **tsne_kwargs,
            max_iter=n_iter
        )
    except TypeError:
        tsne = TSNE(
            **tsne_kwargs,
            n_iter=n_iter
        )

    ########################################################
    # Fit
    ########################################################

    embedding = tsne.fit_transform(

        X

    )

    ########################################################

    return embedding



############################################################
# Create DataFrame
############################################################

def create_tsne_dataframe(

    embedding,

    latent_df,

    label_column=None

):
    """
    Create DataFrame from t-SNE embedding.

    Parameters
    ----------
    embedding : numpy.ndarray
        Output of fit_tsne()

    latent_df : pandas.DataFrame

    label_column : str or None
        Column name containing labels.

    Returns
    -------
    tsne_df : pandas.DataFrame
    """

    ########################################################
    # t-SNE Coordinates
    ########################################################

    tsne_df = pd.DataFrame(

        {

            "TSNE1": embedding[:, 0],

            "TSNE2": embedding[:, 1]

        }

    )

    ########################################################
    # Sample IDs
    ########################################################

    if "SampleID" in latent_df.columns:

        tsne_df.insert(

            0,

            "SampleID",

            latent_df["SampleID"].values

        )

    ########################################################
    # Labels
    ########################################################

    if (

        label_column is not None

        and

        label_column in latent_df.columns

    ):

        tsne_df["Class"] = latent_df[

            label_column

        ].values

    ########################################################

    return tsne_df



############################################################
# Save Results
############################################################

def save_results(

    tsne_df,

    output_dir,

    file_name="tsne_coordinates.tsv"

):
    """
    Save t-SNE coordinates.

    Parameters
    ----------
    tsne_df : pandas.DataFrame

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

    tsne_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )

    ########################################################
    # Save CSV
    ########################################################

    csv_file = os.path.join(

        output_dir,

        "tsne_coordinates.csv"

    )

    tsne_df.to_csv(

        csv_file,

        index=False

    )

    ########################################################
    # Save JSON
    ########################################################

    json_file = os.path.join(

        output_dir,

        "tsne_coordinates.json"

    )

    tsne_df.to_json(

        json_file,

        orient="records",

        indent=4

    )

    ########################################################

    print(

        f"t-SNE coordinates saved to:\n{output_file}"

    )

    ########################################################

    return output_file



############################################################
# t-SNE Scatter Plot
############################################################

def plot_tsne(

    tsne_df,

    output_file,

    label_column="Class",

    point_size=40,

    alpha=0.80

):
    """
    Plot t-SNE embedding.

    Parameters
    ----------
    tsne_df : pandas.DataFrame

    output_file : str

    label_column : str

    point_size : int

    alpha : float
    """

    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(8, 7)

    )

    ########################################################
    # Colored Scatter
    ########################################################

    if (

        label_column is not None

        and

        label_column in tsne_df.columns

    ):

        classes = sorted(

            tsne_df[label_column].unique()

        )

        cmap = plt.get_cmap("tab10")

        colors = cmap(

            np.linspace(

                0,

                1,

                len(classes)

            )

        )

        for color, cls in zip(colors, classes):

            mask = (

                tsne_df[label_column]

                == cls

            )

            plt.scatter(

                tsne_df.loc[mask, "TSNE1"],

                tsne_df.loc[mask, "TSNE2"],

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

            tsne_df["TSNE1"],

            tsne_df["TSNE2"],

            s=point_size,

            alpha=alpha

        )

    ########################################################
    # Labels
    ########################################################

    plt.xlabel(

        "t-SNE 1"

    )

    plt.ylabel(

        "t-SNE 2"

    )

    plt.title(

        "t-SNE Visualization of Latent Space"

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


