"""
early_stopping.py

Early stopping utility for PyTorch models.

Stops training when the monitored metric
does not improve for a specified number of epochs.

Supports
--------
- Minimization metrics (e.g. Loss)
- Maximization metrics (e.g. ROC-AUC)
- Configurable patience
- Configurable minimum improvement

Author : Matin Fathollahi
Project: Microbiome Meta-analysis
License: All Rights Reserved
"""
#########################################################
from numbers import Real
import math
############################################################
# EarlyStopping
############################################################

class EarlyStopping:
    """
    Early stopping utility.

    Parameters
    ----------
    patience : int

    min_delta : float

    mode : str

    verbose : bool
    """

    ########################################################

    def __init__(

        self,

        patience=20,

        min_delta=0.0,

        mode="min",

        verbose=True

    ):


########################################################
# Validate inputs
########################################################

        if not isinstance(patience, int) or patience < 1:
            raise ValueError(
                "patience must be a positive integer."
            )

        if not isinstance(min_delta, Real) or min_delta < 0:
            raise ValueError(
                "min_delta must be a non-negative number."
            )

        if not isinstance(verbose, bool):
            raise TypeError(
                "verbose must be a boolean."
            )

        if not isinstance(mode, str):
            raise TypeError(
                "mode must be a string."
            )

        mode = mode.lower()

        if mode not in ("min", "max"):
            raise ValueError(
                "mode must be either 'min' or 'max'."
            )


        self.patience = patience

        self.min_delta = float(min_delta)

        self.mode = mode

        self.verbose = verbose




        ###############################################

        self.counter = 0

        self.best_score = None

        self.early_stop = False

        ###############################################





############################################################

    def __call__(

        self,

        metric

    ):
        """
        Update early stopping.
        """

########################################################
# Validate metric
########################################################

        if not isinstance(metric, Real):
            raise TypeError(
                "metric must be a real number."
            )

        metric = float(metric)


        if not math.isfinite(metric):
            raise ValueError(
                "metric must be a finite number."
            )



    ########################################################

        if self.best_score is None:

            self.best_score = metric

            return

    ########################################################

        if self.mode == "min":

            improved = (

                metric <

                self.best_score -

                self.min_delta

            )

        else:

            improved = (

                metric >

                self.best_score +

                self.min_delta

            )

    ########################################################

        if improved:

            self.best_score = metric

            self.counter = 0

        else:

            self.counter += 1

        ###############################################

            if self.verbose:

                print(

                    f"EarlyStopping: "

                    f"{self.counter}/"

                    f"{self.patience}"

                )

        ###############################################

            if self.counter >= self.patience:

                self.early_stop = True




############################################################

    def reset(

        self

    ):

        """
        Reset state.
        """

        self.counter = 0

        self.best_score = None

        self.early_stop = False


