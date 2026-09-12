#!/usr/bin/env python3

import numpy as np
import pandas as pd


class MicrobiomeCLRPreprocessor:
    """
    Leakage-safe microbiome preprocessing.

    Fit:
      - abundance filtering
      - prevalence filtering

    Transform:
      - use only features selected during fit
      - sample-wise multiplicative zero replacement
      - sample-wise CLR

    No validation/test information is used during fit.
    """

    def __init__(
        self,
        min_count=10,
        prevalence=0.10,
        zero_fraction=0.5
    ):

        self.min_count = float(
            min_count
        )

        self.prevalence = float(
            prevalence
        )

        self.zero_fraction = float(
            zero_fraction
        )

        self.selected_features_ = None

        self.n_features_in_ = None

        self.n_features_out_ = None


    ########################################################
    # Validation
    ########################################################

    def _validate_X(
        self,
        X
    ):

        if not isinstance(
            X,
            pd.DataFrame
        ):

            X = pd.DataFrame(
                X
            )

        if X.empty:

            raise ValueError(
                "Feature matrix is empty."
            )

        X = X.apply(
            pd.to_numeric,
            errors="coerce"
        )

        if X.isna().any().any():

            raise ValueError(
                "Feature matrix contains "
                "missing or non-numeric values."
            )

        if not np.isfinite(
            X.to_numpy()
        ).all():

            raise ValueError(
                "Feature matrix contains "
                "Inf or NaN values."
            )

        if (
            X.to_numpy()
            < 0
        ).any():

            raise ValueError(
                "Negative counts detected."
            )

        if X.columns.duplicated().any():

            raise ValueError(
                "Duplicated feature names detected."
            )

        return X.astype(
            float
        )


    ########################################################
    # Fit feature filtering
    ########################################################

    def fit(
        self,
        X,
        y=None
    ):

        X = self._validate_X(
            X
        )

        self.n_features_in_ = (
            X.shape[1]
        )

        ####################################################
        # Abundance:
        # determined ONLY from training samples
        ####################################################

        abundance_keep = (

            X.sum(
                axis=0
            )

            >= self.min_count
        )

        ####################################################
        # Prevalence:
        # determined ONLY from training samples
        ####################################################

        prevalence_keep = (

            (
                X > 0
            )
            .mean(
                axis=0
            )

            >= self.prevalence
        )

        keep = (

            abundance_keep
            &
            prevalence_keep
        )

        self.selected_features_ = (

            X.columns[
                keep
            ]
            .astype(str)
            .tolist()
        )

        self.n_features_out_ = len(
            self.selected_features_
        )

        if (
            self.n_features_out_
            == 0
        ):

            raise ValueError(
                "Abundance/prevalence filtering "
                "removed all features."
            )

        return self


    ########################################################
    # Sample-wise zero replacement + CLR
    ########################################################

    def _clr_one_sample(
        self,
        values
    ):

        values = np.asarray(
            values,
            dtype=float
        )

        total = values.sum()

        if (
            not np.isfinite(total)
            or total <= 0
        ):

            raise ValueError(
                "A sample contains zero total abundance "
                "after feature filtering."
            )

        ####################################################
        # Convert counts to composition
        ####################################################

        composition = (
            values / total
        )

        zero_mask = (
            composition == 0
        )

        zero_count = int(
            zero_mask.sum()
        )

        ####################################################
        # Multiplicative zero replacement
        # independently for each sample
        ####################################################

        if zero_count > 0:

            positive = composition[
                ~zero_mask
            ]

            if positive.size == 0:

                raise ValueError(
                    "Sample contains only zeros."
                )

            delta = (

                positive.min()
                *
                self.zero_fraction
            )

            ################################################
            # Ensure valid composition
            ################################################

            maximum_delta = (
                0.99 / zero_count
            )

            delta = min(
                delta,
                maximum_delta
            )

            remaining_mass = (
                1.0
                -
                zero_count
                * delta
            )

            if remaining_mass <= 0:

                raise ValueError(
                    "Invalid zero-replacement mass."
                )

            composition[
                zero_mask
            ] = delta

            composition[
                ~zero_mask
            ] = (

                composition[
                    ~zero_mask
                ]

                * remaining_mass
            )

        ####################################################
        # Numerical safeguard
        ####################################################

        if (
            composition <= 0
        ).any():

            raise ValueError(
                "Non-positive values remain "
                "before CLR."
            )

        log_values = np.log(
            composition
        )

        clr_values = (

            log_values
            -
            log_values.mean()
        )

        return clr_values


    ########################################################
    # Transform
    ########################################################

    def transform(
        self,
        X
    ):

        if (
            self.selected_features_
            is None
        ):

            raise RuntimeError(
                "Preprocessor has not been fitted."
            )

        X = self._validate_X(
            X
        )

        missing = [

            feature

            for feature
            in self.selected_features_

            if feature not in X.columns
        ]

        if missing:

            raise ValueError(
                "Missing selected features: "
                f"{missing[:10]}"
            )

        X_selected = X[
            self.selected_features_
        ].copy()

        transformed = np.vstack(
            [
                self._clr_one_sample(
                    row
                )

                for row
                in X_selected.to_numpy()
            ]
        )

        return pd.DataFrame(

            transformed,

            index=X_selected.index,

            columns=
                self.selected_features_
        )


    def fit_transform(
        self,
        X,
        y=None
    ):

        return (
            self.fit(
                X,
                y
            )
            .transform(
                X
            )
        )