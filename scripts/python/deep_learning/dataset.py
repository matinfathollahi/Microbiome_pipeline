"""
dataset.py

PyTorch Dataset implementation for microbiome datasets.

Supports
--------
- Feature matrices
- Classification labels
- Tensor conversion
- NumPy/Pandas input

Author : Matin Fathollahi
Project: Microbiome Meta-analysis
License: All Rights Reserved
"""
#############################################################



import torch

from torch.utils.data import Dataset

import pandas as pd

import numpy as np

############################################################

class MicrobiomeDataset(Dataset):

    """
    PyTorch Dataset for microbiome classification.
    """

    ########################################################

    def __init__(

        self,

        X,

        y=None

    ):

        """
        Parameters
        ----------
        X : pandas.DataFrame or numpy.ndarray

        y : pandas.Series or numpy.ndarray
        """

 
        ####################################################

        if not isinstance(X, (pd.DataFrame, np.ndarray)):
            raise TypeError(
                "X must be a pandas.DataFrame or numpy.ndarray."
            )


        if isinstance(X, pd.DataFrame):
            X = X.values

        self.X = torch.as_tensor(

            X,

            dtype=torch.float32

        )

       ####################################################


####################################################
# Check X shape
####################################################

        if self.X.ndim != 2:
            raise ValueError(
                f"X must be a 2D array (n_samples, n_features), "
                f"but got shape {tuple(self.X.shape)}."
            )

        if self.X.size(1) == 0:
            raise ValueError(
                "X contains zero features."
            )

        if self.X.size(0) == 0:
            raise ValueError(
                "X contains zero samples."
            )

        ####################################################

        if y is None:

            self.y = None

        else:

            if isinstance(y, pd.DataFrame):

                if y.shape[1] != 1:
                    raise ValueError(
                        "y DataFrame must contain exactly one column."
                    )

                y = y.iloc[:, 0].values

            elif isinstance(y, pd.Series):

                y = y.values

            elif not isinstance(y, np.ndarray):
                raise TypeError(
                    "y must be a pandas.Series, pandas.DataFrame, numpy.ndarray or None."
                )

            if isinstance(y, np.ndarray):

                if y.ndim != 1:
                    raise ValueError(
                        f"y must be a 1D array, but got shape {y.shape}."
                    )

####################################################
# Check number of samples
####################################################

            if self.X.size(0) != len(y):

                raise ValueError(
                    f"Number of samples mismatch: "
                    f"X has {self.X.size(0)} samples but "
                    f"y has {len(y)} labels."
                )



            self.y = torch.as_tensor(

                y,

                dtype=torch.long

            )

    ########################################################

    def __len__(

        self

    ):

        return len(

            self.X

        )

    ########################################################

    def __getitem__(

        self,

        idx

    ):

        if self.y is None:

            return self.X[idx]

        else:

            return (

                self.X[idx],

                self.y[idx]

            )