############################################################
# Standard Library
############################################################

import os

############################################################
# Scientific Computing
############################################################

import numpy as np


############################################################
# Visualization
############################################################

import matplotlib.pyplot as plt


############################################################
# Figure Export
############################################################

from matplotlib.backends.backend_pdf import PdfPages

############################################################
# Style
############################################################

import matplotlib as mpl

############################################################
# Optional
############################################################



############################################################
# Image Processing
############################################################

from PIL import Image



############################################################
# Figure Style
############################################################

def set_publication_style():
    """
    Configure publication-quality plotting style.
    """

    ########################################################
    # Figure DPI
    ########################################################

    mpl.rcParams["figure.dpi"] = 300
    mpl.rcParams["savefig.dpi"] = 300

    ########################################################
    # Figure Size
    ########################################################

    mpl.rcParams["figure.figsize"] = (8, 6)

    ########################################################
    # Font
    ########################################################

    mpl.rcParams["font.family"] = "sans-serif"
    mpl.rcParams["font.sans-serif"] = ["Arial","DejaVu Sans"]
    mpl.rcParams["font.size"] = 12

    ########################################################
    # Axis
    ########################################################

    mpl.rcParams["axes.titlesize"] = 14
    mpl.rcParams["axes.labelsize"] = 12
    mpl.rcParams["axes.linewidth"] = 1.2

    ########################################################
    # Tick
    ########################################################

    mpl.rcParams["xtick.labelsize"] = 11
    mpl.rcParams["ytick.labelsize"] = 11

    ########################################################
    # Legend
    ########################################################

    mpl.rcParams["legend.fontsize"] = 11
    mpl.rcParams["legend.frameon"] = False

    ########################################################
    # Lines
    ########################################################

    mpl.rcParams["lines.linewidth"] = 2

    ########################################################
    # Grid
    ########################################################

    mpl.rcParams["axes.grid"] = False

    ########################################################
    # PDF
    ########################################################

    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42

    ########################################################
    # Layout
    ########################################################

    mpl.rcParams["figure.autolayout"] = True



############################################################
# ROC Figure
############################################################

def plot_roc_figure(

    roc_df,

    output_file,

    auc_score=None

):
    """
    Plot publication-quality ROC curve.

    Parameters
    ----------
    roc_df : DataFrame

    output_file : str

    auc_score : float or None
    """

    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(6,6)

    )

    ########################################################
    # ROC Curve
    ########################################################

    if auc_score is not None:

        label = (

            f"AUC = {auc_score:.3f}"

        )

    else:

        label = "ROC Curve"

    plt.plot(

        roc_df["FPR"],

        roc_df["TPR"],

        linewidth=2.5,

        label=label

    )

    ########################################################
    # Random Guess
    ########################################################

    plt.plot(

        [0,1],

        [0,1],

        linestyle="--",

        linewidth=1.5,

        color="gray",

        label="Random"

    )

    ########################################################
    # Labels
    ########################################################

    plt.xlabel(

        "False Positive Rate"

    )

    plt.ylabel(

        "True Positive Rate"

    )

    plt.title(

        "Receiver Operating Characteristic"

    )

    ########################################################
    # Limits
    ########################################################

    plt.xlim(

        0,

        1

    )

    plt.ylim(

        0,

        1.02

    )

    ########################################################
    # Legend
    ########################################################

    plt.legend(

        loc="lower right"

    )

    ########################################################
    # Layout
    ########################################################

    plt.tight_layout()

    ########################################################
    # Save
    ########################################################

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()


############################################################
# Precision-Recall Figure
############################################################

def plot_pr_figure(

    pr_df,

    output_file,

    ap_score=None

):
    """
    Plot publication-quality Precision-Recall curve.

    Parameters
    ----------
    pr_df : pandas.DataFrame

    output_file : str

    ap_score : float or None
    """

    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(6,6)

    )

    ########################################################
    # Label
    ########################################################

    if ap_score is not None:

        label = (

            f"AP = {ap_score:.3f}"

        )

    else:

        label = "Precision-Recall Curve"

    ########################################################
    # Curve
    ########################################################

    plt.plot(

        pr_df["Recall"],

        pr_df["Precision"],

        linewidth=2.5,

        label=label

    )

    ########################################################
    # Labels
    ########################################################

    plt.xlabel(

        "Recall"

    )

    plt.ylabel(

        "Precision"

    )

    plt.title(

        "Precision-Recall Curve"

    )

    ########################################################
    # Limits
    ########################################################

    plt.xlim(

        0,

        1

    )

    plt.ylim(

        0,

        1.02

    )

    ########################################################
    # Legend
    ########################################################

    plt.legend(

        loc="lower left"

    )

    ########################################################
    # Layout
    ########################################################

    plt.tight_layout()

    ########################################################
    # Save
    ########################################################

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    plt.savefig(

        output_file,

        dpi=300,

        bbox_inches="tight"

    )

    plt.close()



############################################################
# Confusion Matrix Figure
############################################################

def plot_confusion_matrix(

    cm,

    class_names,

    output_file,

    normalize=False

):
    """
    Plot publication-quality confusion matrix.

    Parameters
    ----------
    cm : numpy.ndarray

    class_names : list[str]

    output_file : str

    normalize : bool
    """

########################################################
# Normalize
########################################################

    if normalize:

        row_sum = cm.sum(axis=1, keepdims=True)

        row_sum[row_sum == 0] = 1

        cm = cm.astype(np.float64) / row_sum
    ########################################################
    # Figure
    ########################################################

    plt.figure(

        figsize=(6,6)

    )

    ########################################################
    # Heatmap
    ########################################################

    plt.imshow(

        cm,

        interpolation="nearest",

        cmap="Blues"

    )

    plt.colorbar()

    ########################################################
    # Tick Labels
    ########################################################

    tick_marks = np.arange(

        len(class_names)

    )

    plt.xticks(

        tick_marks,

        class_names

    )

    plt.yticks(

        tick_marks,

        class_names

    )

    ########################################################
    # Cell Values
    ########################################################

    threshold = (

        cm.max()

        /

        2

    )

    for i in range(

        cm.shape[0]

    ):

        for j in range(

            cm.shape[1]

        ):

            if normalize:

                text = f"{cm[i,j]:.2f}"

            else:

                text = str(

                    int(cm[i,j])

                )

            plt.text(

                j,

                i,

                text,

                ha="center",

                va="center",

                color=(

                    "white"

                    if cm[i,j] > threshold

                    else "black"

                )

            )

    ########################################################
    # Labels
    ########################################################

    plt.xlabel(

        "Predicted Label"

    )

    plt.ylabel(

        "True Label"

    )

    plt.title(

        "Confusion Matrix"

    )

    ########################################################
    # Layout
    ########################################################

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



############################################################
# ROC Export Figure
############################################################

def export_roc_figure(roc_figure, output_file):

    if not os.path.exists(roc_figure):
        print(f"File not found: {roc_figure}")
        return

    try:
        image = Image.open(roc_figure)
    except Exception as e:
        print(e)
        return


    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(output_file, dpi=(300,300))

    print(f"ROC figure saved to:\n{output_file}")


def export_pr_figure(pr_figure, output_file):

    if not os.path.exists(pr_figure):
        print(f"File not found: {pr_figure}")
        return

    try:
        image = Image.open(pr_figure)
    except Exception as e:
        print(e)
        return
   

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(output_file, dpi=(300,300))

    print(f"PR figure saved to:\n{output_file}")


def export_confusion_matrix_figure(confusion_matrix_figure, output_file):

    if not os.path.exists(confusion_matrix_figure):
        print(f"File not found: {confusion_matrix_figure}")
        return


    try:
        image = Image.open(confusion_matrix_figure)
    except Exception as e:
        print(e)
        return
    

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(output_file, dpi=(300,300))

    print(f"Confusion Matrix figure saved to:\n{output_file}")

############################################################
# SHAP Figure
############################################################

def export_shap_figure(

    shap_figure,

    output_file

):
    """
    Export SHAP summary figure for publication.
    """

    ########################################################
    # Check File
    ########################################################

    if not os.path.exists(shap_figure):
        print(f"File not found: {shap_figure}")
        return

    ########################################################
    # Load Image
    ########################################################

    try:
        image = Image.open(shap_figure)
    except Exception as e:
        print(e)
        return


    ########################################################
    # Save
    ########################################################
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300,300)

    )

    ########################################################

    print(

        f"SHAP figure saved to:\n{output_file}"

    )
############################################################
# Permutation Importance Figure
############################################################

def export_permutation_figure(

    permutation_figure,

    output_file

):
    """
    Export permutation importance figure.

    Parameters
    ----------
    permutation_figure : str

        Path to permutation importance figure.

    output_file : str

        Output publication figure.
    """


########################################################
# Check File
########################################################

    if not os.path.exists(permutation_figure):
        print(f"File not found: {permutation_figure}")
        return

    ########################################################
    # Load Figure
    ########################################################

    try:
        image = Image.open(permutation_figure)
    except Exception as e:
        print(e)
        return
    

    ########################################################
    # Save Figure
    ########################################################
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300,300)

    )

    ########################################################

    print(

        f"Permutation figure saved to:\n{output_file}"

    )



############################################################
# PCA Figure
############################################################

def export_pca_figure(

    pca_figure,

    output_file

):
    """
    Export PCA figure for publication.

    Parameters
    ----------
    pca_figure : str

        Path to PCA figure.

    output_file : str

        Output publication figure.
    """

    if not os.path.exists(pca_figure):
        print(f"File not found: {pca_figure}")
        return


    ########################################################
    # Load Figure
    ########################################################
    try:
        image = Image.open(pca_figure)
    except Exception as e:
        print(e)
        return

  

    ########################################################
    # Save Figure
    ########################################################

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300,300)

    )

    ########################################################

    print(

        f"PCA figure saved to:\n{output_file}"

    )




############################################################
# t-SNE Figure
############################################################

def export_tsne_figure(

    tsne_figure,

    output_file

):
    """
    Export t-SNE figure for publication.

    Parameters
    ----------
    tsne_figure : str

        Path to t-SNE figure.

    output_file : str

        Output publication figure.
    """


    if not os.path.exists(tsne_figure):
        print(f"File not found: {tsne_figure}")
        return


    ########################################################
    # Load Figure
    ########################################################

    try:
        image = Image.open(tsne_figure)
    except Exception as e:
        print(e)
        return



    ########################################################
    # Save Figure
    ########################################################
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300, 300)

    )

    ########################################################

    print(

        f"t-SNE figure saved to:\n{output_file}"

    )



############################################################
# UMAP Figure
############################################################

def export_umap_figure(

    umap_figure,

    output_file

):
    """
    Export UMAP figure for publication.

    Parameters
    ----------
    umap_figure : str

        Path to UMAP figure.

    output_file : str

        Output publication figure.
    """


    if not os.path.exists(umap_figure):
        print(f"File not found: {umap_figure}")
        return

    ########################################################
    # Load Figure
    ########################################################
    try:
        image = Image.open(umap_figure)
    except Exception as e:
        print(e)
        return


    ########################################################
    # Save Figure
    ########################################################
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300, 300)

    )

    ########################################################

    print(

        f"UMAP figure saved to:\n{output_file}"

    )



############################################################
# Global Feature Importance Figure
############################################################

def export_global_importance_figure(

    global_importance_figure,

    output_file

):
    """
    Export global feature importance figure for publication.

    Parameters
    ----------
    global_importance_figure : str

        Path to global feature importance figure.

    output_file : str

        Output publication figure.
    """


    if not os.path.exists(global_importance_figure):
        print(f"File not found: {global_importance_figure}")
        return

    ########################################################
    # Load Figure
    ########################################################
    try:
        image = Image.open(global_importance_figure)
    except Exception as e:
        print(e)
        return



    ########################################################
    # Save Figure
    ########################################################
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300, 300)

    )

    ########################################################

    print(

        f"Global importance figure saved to:\n{output_file}"

    )



############################################################
# Local Explanation Figure
############################################################

def export_local_explanation_figure(

    local_explanation_figure,

    output_file

):
    """
    Export local explanation figure for publication.

    Parameters
    ----------
    local_explanation_figure : str

        Path to local explanation figure.

    output_file : str

        Output publication figure.
    """


    if not os.path.exists(local_explanation_figure):
        print(f"File not found: {local_explanation_figure}")
        return

    ########################################################
    # Load Figure
    ########################################################
    try:
        image = Image.open(local_explanation_figure)
    
    except Exception as e:
        print(e)
        return



    ########################################################
    # Save Figure
    ########################################################
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    image.save(

        output_file,

        dpi=(300,300)

    )

    ########################################################

    print(

        f"Local explanation figure saved to:\n{output_file}"

    )



############################################################
# Export Publication Figures
############################################################

def export_publication_figures(

    publication_dir

):
    """
    Export all publication-ready figures.

    Parameters
    ----------
    publication_dir : str
    """

########################################################
# Set Figure Style
########################################################

    set_publication_style()


    ########################################################
    # Output Directory
    ########################################################

    os.makedirs(

        publication_dir,

        exist_ok=True

    )

    ########################################################
    # Export Figures
    ########################################################

    export_roc_figure(

        roc_figure="results/metrics/roc_curve.png",

        output_file=os.path.join(

            publication_dir,

            "Figure1_ROC.png"

        )

    )

    export_pr_figure(

        pr_figure="results/metrics/pr_curve.png",

        output_file=os.path.join(

            publication_dir,

            "Figure2_PR.png"

        )

    )

    export_confusion_matrix_figure(

        confusion_matrix_figure="results/metrics/confusion_matrix.png",

        output_file=os.path.join(

            publication_dir,

            "Figure3_ConfusionMatrix.png"

        )

    )

    export_shap_figure(

        shap_figure="results/shap/shap_summary.png",

        output_file=os.path.join(

            publication_dir,

            "Figure4_SHAP.png"

        )

    )

    export_permutation_figure(

        permutation_figure="results/permutation/permutation_importance.png",

        output_file=os.path.join(

            publication_dir,

            "Figure5_Permutation.png"

        )

    )

    export_pca_figure(

        pca_figure="results/pca/pca.png",

        output_file=os.path.join(

            publication_dir,

            "Figure6_PCA.png"

        )

    )

    export_tsne_figure(

        tsne_figure="results/tsne/tsne.png",

        output_file=os.path.join(

            publication_dir,

            "Figure7_tSNE.png"

        )

    )

    export_umap_figure(

        umap_figure="results/umap/umap.png",

        output_file=os.path.join(

            publication_dir,

            "Figure8_UMAP.png"

        )

    )

    export_global_importance_figure(

        global_importance_figure="results/global_importance/global_importance.png",

        output_file=os.path.join(

            publication_dir,

            "Figure9_GlobalImportance.png"

        )

    )

    export_local_explanation_figure(

        local_explanation_figure="results/local_explanation/Sample017_local_importance.png",

        output_file=os.path.join(

            publication_dir,

            "Figure10_LocalExplanation.png"

        )

    )

    ########################################################
    # Create PDF
    ########################################################

    pdf_path = os.path.join(

        publication_dir,

        "Publication_Figures.pdf"

    )

    with PdfPages(

        pdf_path

    ) as pdf:

        for file_name in sorted(

            os.listdir(

                publication_dir

            )

        ):

            if file_name.lower().endswith(".png"):



                try:
                    img = Image.open(
                        os.path.join(publication_dir, file_name)
                    )
                except Exception as e:
                    print(f"Cannot open {file_name}: {e}")
                    continue

                fig = plt.figure(

                    figsize=(8,6)

                )

                plt.imshow(

                    img

                )

                plt.axis(

                    "off"

                )

                pdf.savefig(

                    fig,

                    bbox_inches="tight"

                )

                plt.close(

                    fig

                )

    ########################################################

    print(

        f"Publication figures exported to:\n{publication_dir}"

    )

    print(

        f"PDF created:\n{pdf_path}"

    )