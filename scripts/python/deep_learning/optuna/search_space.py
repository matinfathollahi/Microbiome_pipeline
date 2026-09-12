#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
search_space.py

Optuna Search Space
for Deep Learning Models

Currently Supported
-------------------
- MLP
"""

############################################################
# Imports
############################################################

import optuna

############################################################
# MLP Search Space
############################################################

def mlp_search_space(trial):
    """
    Hyperparameter search space for MLP.

    Parameters
    ----------
    trial : optuna.trial.Trial

    Returns
    -------
    dict
    """

    scheduler = trial.suggest_categorical(
        "scheduler",
        [
            "Plateau",
            "Cosine",
            "Step",
            "None"
        ]
    )

    params = {

        ####################################################
        # Network Architecture
        ####################################################

        "hidden_dims":

            trial.suggest_categorical(

                "hidden_dims",

                [

                    [256, 128],

                    [512, 256],

                    [512, 256, 128],

                    [1024, 512, 256],

                    [1024, 512, 256, 128]

                ]

            ),

        ####################################################
        # Activation
        ####################################################

        "activation":

            trial.suggest_categorical(

                "activation",

                [

                    "relu",

                    "gelu",

                    "elu",

                    "selu"

                ]

            ),

        ####################################################
        # Dropout
        ####################################################

        "dropout":

            trial.suggest_float(

                "dropout",

                0.0,

                0.6

            ),

        ####################################################
        # Batch Normalization
        ####################################################

        "batch_norm":

            trial.suggest_categorical(

                "batch_norm",

                [

                    True,

                    False

                ]

            ),

        ####################################################
        # Optimizer
        ####################################################

        "optimizer":

            trial.suggest_categorical(

                "optimizer",

                [

                    "Adam",

                    "AdamW",

                    "RMSprop"

                ]

            ),

        ####################################################
        # Learning Rate
        ####################################################

        "learning_rate":

            trial.suggest_float(

                "learning_rate",

                1e-5,

                1e-2,

                log=True

            ),

        ####################################################
        # Weight Decay
        ####################################################

        "weight_decay":

            trial.suggest_float(

                "weight_decay",

                1e-8,

                1e-2,

                log=True

            ),

        ####################################################
        # Batch Size
        ####################################################

        "batch_size":

            trial.suggest_categorical(

                "batch_size",

                [

                    32,

                    64,

                    128,

                    256

                ]

            ),

        ####################################################
        # Scheduler
        ####################################################

        "scheduler": scheduler,




        ####################################################
        # Early Stopping
        ####################################################

        "patience":

            trial.suggest_int(

                "patience",

                10,

                40

            ),

        ####################################################
        # Gradient Clipping
        ####################################################

        "gradient_clip":

            trial.suggest_float(

                "gradient_clip",

                0.5,

                5.0

            )

    }

    if scheduler == "Step":

        params["step_size"] = trial.suggest_int(
            "step_size",
            5,
            30
        )

        params["gamma"] = trial.suggest_float(
            "gamma",
            0.1,
            0.9
        )

    return params


############################################################
# Dispatcher
############################################################

SEARCH_SPACE = {

    "MLP": mlp_search_space

}


############################################################
# Factory Function
############################################################

def get_search_space(

    model_name

):
    """
    Return Optuna search space function.

    Parameters
    ----------
    model_name : str

    Returns
    -------
    callable
    """

    model_name = model_name.upper()

    if model_name not in SEARCH_SPACE:

        raise ValueError(

            f"Unknown model: {model_name}"

        )

    return SEARCH_SPACE[model_name]