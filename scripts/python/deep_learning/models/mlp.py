#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
mlp.py

Multi-Layer Perceptron (MLP)
"""

############################################################
# Imports
############################################################

import torch.nn as nn

############################################################
# MLP
############################################################

class MLP(nn.Module):
    """
    Configurable Multi-Layer Perceptron.
    """

    def __init__(
        self,
        input_dim,
        output_dim,
        hidden_dims,
        activation="relu",
        dropout=0.0,
        batch_norm=False
    ):

        super().__init__()

        ####################################################
        # Activation
        ####################################################

        activation = activation.lower()

        activation_dict = {

            "relu": nn.ReLU(),

            "gelu": nn.GELU(),

            "elu": nn.ELU(),

            "selu": nn.SELU()

        }

        if activation not in activation_dict:

            raise ValueError(
                f"Unsupported activation: {activation}"
            )

        act = activation_dict[activation]

        ####################################################
        # Hidden Layers
        ####################################################

        layers = []

        in_features = input_dim

        for hidden_size in hidden_dims:

            layers.append(

                nn.Linear(

                    in_features,

                    hidden_size

                )

            )

            if batch_norm:

                layers.append(

                    nn.BatchNorm1d(

                        hidden_size

                    )

                )

            layers.append(act)

            if dropout > 0:

                layers.append(

                    nn.Dropout(

                        dropout

                    )

                )

            in_features = hidden_size

        ####################################################
        # Output Layer
        ####################################################

        layers.append(

            nn.Linear(

                in_features,

                output_dim

            )

        )

        ####################################################

        self.network = nn.Sequential(

            *layers

        )

    ########################################################

    def forward(

        self,

        x

    ):

        return self.network(x)

############################################################
# Factory Function
############################################################

def build_mlp(

    params,

    input_dim,

    output_dim

):
    """
    Build an MLP model from Optuna parameters.
    """

    model = MLP(

        input_dim=input_dim,

        output_dim=output_dim,

        hidden_dims=params["hidden_dims"],

        activation=params["activation"],

        dropout=params["dropout"],

        batch_norm=params["batch_norm"]

    )

    return model