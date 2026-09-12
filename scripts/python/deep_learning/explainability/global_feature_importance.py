#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
global_feature_importance.py

Merge feature importance results from
multiple explainability methods.
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
# Load Importance Files
############################################################

def load_importance_files(

    shap_file,

    ig_file,

    permutation_file

):
    """
    Load feature importance files.

    Parameters
    ----------
    shap_file : str

    ig_file : str

    permutation_file : str

    Returns
    -------
    shap_df : pandas.DataFrame

    ig_df : pandas.DataFrame

    permutation_df : pandas.DataFrame
    """

    ########################################################
    # SHAP
    ########################################################

    shap_df = pd.read_csv(

        shap_file,

        sep="\t"

    )

    ########################################################
    # Integrated Gradients
    ########################################################

    ig_df = pd.read_csv(

        ig_file,

        sep="\t"

    )

    ########################################################
    # Permutation Importance
    ########################################################

    permutation_df = pd.read_csv(

        permutation_file,

        sep="\t"

    )

    ########################################################

    return (

        shap_df,

        ig_df,

        permutation_df

    )



############################################################
# Merge Importance
############################################################

def merge_importance(

    shap_df,

    ig_df,

    permutation_df

):
    """
    Merge feature importance from different methods.

    Parameters
    ----------
    shap_df : pandas.DataFrame

    ig_df : pandas.DataFrame

    permutation_df : pandas.DataFrame

    Returns
    -------
    merged_df : pandas.DataFrame
    """

    ########################################################
    # Rename Columns
    ########################################################

    shap_df = shap_df.rename(

        columns={

            "Importance": "SHAP"

        }

    )

    ig_df = ig_df.rename(

        columns={

            "Importance": "IntegratedGradients"

        }

    )

    permutation_df = permutation_df.rename(

        columns={

            "Importance": "Permutation"

        }

    )



    ########################################################
    # Aggregate Duplicate Features
    ########################################################

    shap_df = shap_df.groupby(
        "Feature",
        as_index=False
    )["SHAP"].mean()


    ig_df = ig_df.groupby(
        "Feature",
        as_index=False
    )["IntegratedGradients"].mean()


    permutation_df = permutation_df.groupby(
        "Feature",
        as_index=False
    )["Permutation"].mean()

    ########################################################
    # Keep Only Needed Columns
    ########################################################

    shap_df = shap_df[

        [

            "Feature",

            "SHAP"

        ]

    ]

    ig_df = ig_df[

        [

            "Feature",

            "IntegratedGradients"

        ]

    ]

    permutation_df = permutation_df[

        [

            "Feature",

            "Permutation"

        ]

    ]

    ########################################################
    # Merge
    ########################################################

    merged_df = pd.merge(

        shap_df,

        ig_df,

        on="Feature",

        how="outer"

    )

    merged_df = pd.merge(

        merged_df,

        permutation_df,

        on="Feature",

        how="outer"

    )

    ########################################################
    # Fill Missing Values
    ########################################################

    merged_df = merged_df.fillna(

        0.0

    )

    ########################################################

    return merged_df




############################################################
# Normalize Scores
############################################################

def normalize_scores(

    merged_df

):
    """
    Normalize feature importance scores to [0, 1].

    Parameters
    ----------
    merged_df : pandas.DataFrame

    Returns
    -------
    normalized_df : pandas.DataFrame
    """

    ########################################################
    # Copy
    ########################################################

    normalized_df = merged_df.copy()

    ########################################################
    # Methods
    ########################################################

    methods = [

        "SHAP",

        "IntegratedGradients",

        "Permutation"

    ]


    for method in methods:

        normalized_df[method] = pd.to_numeric(
            normalized_df[method],
            errors="coerce"
        ).fillna(0.0)


    ########################################################
    # Max Normalization
    ########################################################

    for method in methods:

        values = normalized_df[method]
      

        # SHAP and Integrated Gradients
        # use absolute magnitude
        if method in [
            "SHAP",
            "IntegratedGradients",
            "Permutation"
        ]:
            values = values.abs()

        max_value = values.max()

        if max_value == 0:

            normalized_df[method] = 0.0

        else:

            normalized_df[method] = (
                values / max_value
            )


    ########################################################

    return normalized_df



############################################################
# Global Ranking
############################################################

def global_ranking(

    normalized_df

):
    """
    Compute global feature importance ranking.

    Parameters
    ----------
    normalized_df : pandas.DataFrame

    Returns
    -------
    ranking_df : pandas.DataFrame
    """

    ########################################################
    # Copy
    ########################################################

    ranking_df = normalized_df.copy()

    ########################################################
    # Global Importance
    ########################################################

    ranking_df["GlobalImportance"] = (

        ranking_df["SHAP"] * 0.4 +

        ranking_df["IntegratedGradients"] * 0.4 +

        ranking_df["Permutation"] * 0.2

    )

    ########################################################
    # Sort
    ########################################################

    ranking_df = ranking_df.sort_values(

        by="GlobalImportance",

        ascending=False

    )

    ########################################################
    # Rank
    ########################################################

    ranking_df.insert(

        0,

        "Rank",

        range(

            1,

            len(ranking_df) + 1

        )

    )

    ########################################################
    # Reset Index
    ########################################################

    ranking_df = ranking_df.reset_index(

        drop=True

    )

    ########################################################

    return ranking_df



############################################################
# Save Results
############################################################

def save_results(

    ranking_df,

    output_dir,

    file_name="global_feature_importance.tsv"

):
    """
    Save global feature importance.

    Parameters
    ----------
    ranking_df : pandas.DataFrame

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
    # TSV
    ########################################################

    output_file = os.path.join(

        output_dir,

        file_name

    )

    ranking_df.to_csv(

        output_file,

        sep="\t",

        index=False

    )

    ########################################################
    # CSV
    ########################################################

    csv_file = os.path.join(

        output_dir,

        "global_feature_importance.csv"

    )

    ranking_df.to_csv(

        csv_file,

        index=False

    )

    ########################################################
    # JSON
    ########################################################

    json_file = os.path.join(

        output_dir,

        "global_feature_importance.json"

    )

    ranking_df.to_json(

        json_file,

        orient="records",

        indent=4

    )

    ########################################################

    print(

        f"Global feature importance saved to:\n{output_file}"

    )

    ########################################################

    return output_file






############################################################
# Global Feature Importance Plot
############################################################

def plot_global_importance(

    ranking_df,

    output_file,

    top_k=20

):
    """
    Plot global feature importance.
    """

    ########################################################
    # Top Features
    ########################################################

    top_df = ranking_df.head(

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

        top_df["GlobalImportance"]

    )

    plt.gca().invert_yaxis()

    plt.xlabel(

        "Global Importance"

    )

    plt.ylabel(

        "Feature"

    )

    plt.title(

        f"Top {top_k} Global Features"

    )

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()




############################################################
# Comparison Plot
############################################################

def plot_method_comparison(

    ranking_df,

    output_file,

    top_k=15

):
    """
    Compare feature importance across methods.
    """

    ########################################################
    # Top Features
    ########################################################

    top_df = ranking_df.head(

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

    width = 0.25

    ########################################################

    plt.bar(

        x-width,

        top_df["SHAP"],

        width,

        label="SHAP"

    )

    plt.bar(

        x,

        top_df["IntegratedGradients"],

        width,

        label="Integrated Gradients"

    )

    plt.bar(

        x+width,

        top_df["Permutation"],

        width,

        label="Permutation"

    )

    ########################################################

    plt.xticks(

        x,

        top_df["Feature"],

        rotation=90

    )

    plt.ylabel(

        "Normalized Importance"

    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()




