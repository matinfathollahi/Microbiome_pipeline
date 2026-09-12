"""
metrics.py

Evaluation metrics for microbiome classification models.

Implemented metrics
-------------------
- Accuracy
- Balanced Accuracy
- Precision
- Recall
- F1-score
- MCC
- ROC-AUC

Author : Matin
Project: Microbiome Meta-analysis
"""

############################################################

import numpy as np

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

############################################################
# Evaluate
############################################################

def evaluate(
    y_true,
    y_pred,
    y_prob
):

    """
    Evaluate classification performance.
    """

    ########################################################
    # Convert inputs
    ########################################################

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    y_prob = np.asarray(y_prob)


    ########################################################
    # Validate dimensions
    ########################################################

    if y_true.ndim != 1:
        raise ValueError(
            "y_true must be a 1D array."
        )


    if y_pred.ndim != 1:
        raise ValueError(
            "y_pred must be a 1D array."
        )


    if y_prob.ndim != 2:
        raise ValueError(
            "y_prob must be a 2D array."
        )


    ########################################################
    # Validate number of samples
    ########################################################

    if len(y_true) != len(y_pred):

        raise ValueError(
            "y_true and y_pred must have same length."
        )


    if len(y_true) != y_prob.shape[0]:

        raise ValueError(
            "y_prob samples do not match labels."
        )


    if len(y_true) == 0:

        raise ValueError(
            "Input arrays cannot be empty."
        )


########################################################
# Check NaN / Infinite values
########################################################

    # y_prob must always be numeric

    if not np.issubdtype(
        y_prob.dtype,
        np.number
    ):

        raise TypeError(
            "y_prob must contain numeric probabilities."
        )


    if not np.isfinite(y_prob).all():

        raise ValueError(
            "y_prob contains NaN or infinite values."
        )


########################################################
# Check probability range
########################################################

    if np.any(y_prob < 0) or np.any(y_prob > 1):

        raise ValueError(
            "y_prob values must be between 0 and 1."
        )

########################################################
# Validate labels
########################################################

    try:

        y_true = y_true.astype(np.int64)
        y_pred = y_pred.astype(np.int64)

    except Exception:

        raise TypeError(
            "Labels must be integer encoded before evaluation."
        )
########################################################
    ########################################################
    # Determine model classes
    ########################################################

    true_classes = np.unique(
        y_true
    )

    pred_classes = np.unique(
        y_pred
    )


    # Number of classes represented by the trained model
    # comes from probability columns, NOT only from
    # the current held-out study.
    n_model_classes = int(
        y_prob.shape[1]
    )


    if n_model_classes < 2:

        raise ValueError(
            "Model must have at least "
            "two output classes."
        )


    ########################################################
    # Validate encoded labels
    ########################################################

    valid_labels = np.arange(
        n_model_classes
    )


    if not np.all(
        np.isin(
            true_classes,
            valid_labels
        )
    ):

        raise ValueError(
            "y_true contains class labels "
            "outside the model output range."
        )


    if not np.all(
        np.isin(
            pred_classes,
            valid_labels
        )
    ):

        raise ValueError(
            "y_pred contains class labels "
            "outside the model output range."
        )


    ########################################################
    # Calculate standard metrics
    ########################################################

    metrics = {}


    metrics["Accuracy"] = accuracy_score(
        y_true,
        y_pred
    )


    metrics["BalancedAccuracy"] = (
        balanced_accuracy_score(
            y_true,
            y_pred
        )
    )


    metrics["Precision"] = precision_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )


    metrics["Recall"] = recall_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )


    metrics["F1"] = f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )


    metrics["F1_macro"] = f1_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )


    metrics["MCC"] = matthews_corrcoef(
        y_true,
        y_pred
    )


    ########################################################
    # Sensitivity / Specificity
    #
    # Only meaningful for globally binary classification.
    # labels=[0, 1] guarantees a 2x2 matrix even if the
    # held-out study contains only one of the two classes.
    ########################################################

    if n_model_classes == 2:

        cm = confusion_matrix(
            y_true,
            y_pred,
            labels=[0, 1]
        )


        tn, fp, fn, tp = (
            cm.ravel()
        )


        metrics["Sensitivity"] = (
            tp / (tp + fn)
            if (tp + fn) > 0
            else np.nan
        )


        metrics["Specificity"] = (
            tn / (tn + fp)
            if (tn + fp) > 0
            else np.nan
        )


    ########################################################
    # ROC-AUC
    ########################################################

    # ROC-AUC is undefined when the held-out study
    # contains only one observed class.
    if len(true_classes) < 2:

        metrics["ROC_AUC"] = np.nan


    elif n_model_classes == 2:

        try:

            metrics["ROC_AUC"] = (
                roc_auc_score(
                    y_true,
                    y_prob[:, 1]
                )
            )

        except ValueError:

            metrics["ROC_AUC"] = np.nan


    else:

        try:

            metrics["ROC_AUC"] = (
                roc_auc_score(
                    y_true,
                    y_prob,
                    labels=valid_labels,
                    multi_class="ovr",
                    average="weighted"
                )
            )

        except ValueError:

            metrics["ROC_AUC"] = np.nan


    return metrics

