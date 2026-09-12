#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
train.py

Training utilities for deep learning models used in the
Microbiome Meta-analysis pipeline.

Features
--------
- Training loop
- Validation loop
- Mixed precision training
- Early stopping
- Learning-rate scheduling
- Model checkpointing
- Prediction utilities

Author : Matin Fathollahi
Project: Microbiome Meta-analysis
License: 
Python : >=3.10
PyTorch: >=2.5
"""

############################################################
# Standard Library
############################################################


############################################################
# Third-party Libraries
############################################################

import numpy as np


from tqdm.auto import tqdm

############################################################
# PyTorch
############################################################

import torch
import optuna



############################################################
# Mixed Precision
############################################################

from torch.amp import autocast
from torch.amp import GradScaler

############################################################
# Learning Rate Scheduler
############################################################

from torch.optim.lr_scheduler import ReduceLROnPlateau

############################################################

############################################################
# Local Modules
############################################################

from deep_learning.utils import (
    save_model,
    load_model
)

from deep_learning.metrics import evaluate
############################################################
# Ignore Warnings
############################################################

import warnings

warnings.filterwarnings(
    "ignore"
)


############################################################
# Device Selection
############################################################

def get_device():
    """
    Automatically select the best available device.

    Priority
    --------
    CUDA GPU
        ↓
    Apple MPS
        ↓
    CPU

    Returns
    -------
    torch.device
    """

    ########################################################
    # NVIDIA CUDA
    ########################################################

    if torch.cuda.is_available():

        device = torch.device("cuda")

        print(
            f"Using GPU : {torch.cuda.get_device_name(0)}"
        )

    ########################################################
    # Apple Silicon (M1 / M2 / M3)
    ########################################################

    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():

        device = torch.device("mps")

        print(
            "Using Apple Metal (MPS)"
        )

    ########################################################
    # CPU
    ########################################################

    else:

        device = torch.device("cpu")

        print(
            "Using CPU"
        )

    ########################################################

    return device



############################################################
# Train One Epoch
############################################################

def train_one_epoch(

    model,

    dataloader,

    criterion,

    optimizer,

    device,

    scaler,

    gradient_clip=1.0

):
    """
    Train one epoch.

    Parameters
    ----------
    model : nn.Module

    dataloader : DataLoader

    criterion : Loss Function

    optimizer : torch.optim

    device : torch.device

    scaler : torch.amp.GradScaler

    

    gradient_clip : float

    Returns
    -------
    dict
    """

    ########################################################

    model.train()

    ########################################################

    running_loss = 0.0

    predictions = []

    probabilities = []

    targets = []

    ########################################################

    progress = tqdm(

        dataloader,

        desc="Training",

        leave=False

    )

    ########################################################

    for x, y in progress:

        ###############################################
        # Device
        ###############################################

        x = x.to(

            device,

            non_blocking=True

        )

        y = y.to(

            device,

            non_blocking=True

        )

        ###############################################
        # Zero Gradient
        ###############################################

        optimizer.zero_grad(

            set_to_none=True

        )

        ###############################################
        # Forward
        ###############################################

        with autocast(
            "cuda",
            enabled=(device.type == "cuda")
        ):

            output = model(

                x

            )

            ###########################################

            if isinstance(

                output,

                dict

            ):

                logits = output[

                    "logits"

                ]

            else:

                logits = output

            ###########################################

            loss = criterion(

                logits,

                y

            )

        ###############################################
        # Backward
        ###############################################

        scaler.scale(

            loss

        ).backward()

        ###############################################
        # Gradient Clipping
        ###############################################

        scaler.unscale_(

            optimizer

        )

        torch.nn.utils.clip_grad_norm_(

            model.parameters(),

            gradient_clip

        )

        ###############################################
        # Optimizer
        ###############################################

        scaler.step(

            optimizer

        )

        scaler.update()

        ###############################################
      
        ###############################################
        # Statistics
        ###############################################

        running_loss += (

            loss.item()

            *

            x.size(0)

        )

        ###############################################

        prob = torch.softmax(

            logits,

            dim=1

        )

        pred = torch.argmax(

            prob,

            dim=1

        )

        ###############################################

        predictions.extend(

            pred.detach()

            .cpu()

            .numpy()

        )

        probabilities.extend(

            prob.detach()

            .cpu()

            .numpy()

        )

        targets.extend(

            y.detach()

            .cpu()

            .numpy()

        )

        ###############################################

        progress.set_postfix(

            loss=f"{loss.item():.4f}"

        )

    ########################################################

    epoch_loss = (

        running_loss

        /

        len(

            dataloader.dataset

        )

    )

    ########################################################

    metrics = evaluate(

        np.array(

            targets

        ),

        np.array(

            predictions

        ),

        np.array(

            probabilities

        )

    )

    ########################################################

    metrics[

        "Loss"

    ] = epoch_loss

    ########################################################

    return metrics



############################################################
# Validate One Epoch
############################################################

def validate_one_epoch(

    model,

    dataloader,

    criterion,

    device

):
    """
    Validate one epoch.

    Parameters
    ----------
    model : nn.Module

    dataloader : DataLoader

    criterion : Loss Function

    device : torch.device

    Returns
    -------
    dict
    """

    ########################################################

    model.eval()

    ########################################################

    running_loss = 0.0

    predictions = []

    probabilities = []

    targets = []

    ########################################################

    progress = tqdm(

        dataloader,

        desc="Validation",

        leave=False

    )

    ########################################################

    with torch.no_grad():

        ####################################################

        for x, y in progress:

            ###############################################
            # Device
            ###############################################

            x = x.to(

                device,

                non_blocking=True

            )

            y = y.to(

                device,

                non_blocking=True

            )

            ###############################################
            # Forward
            ###############################################
            with autocast(
                "cuda",
                enabled=(device.type == "cuda")
            ):

                output = model(

                    x

                )

                ###########################################

                if isinstance(

                    output,

                    dict

                ):

                    logits = output[

                        "logits"

                    ]

                else:

                    logits = output

                ###########################################

                loss = criterion(

                    logits,

                    y

                )

            ###############################################
            # Statistics
            ###############################################

            running_loss += (

                loss.item()

                *

                x.size(0)

            )

            ###############################################

            prob = torch.softmax(

                logits,

                dim=1

            )

            pred = torch.argmax(

                prob,

                dim=1

            )

            ###############################################

            predictions.extend(

                pred.cpu().numpy()

            )

            probabilities.extend(

                prob.cpu().numpy()

            )

            targets.extend(

                y.cpu().numpy()

            )

            ###############################################

            progress.set_postfix(

                loss=f"{loss.item():.4f}"

            )

    ########################################################

    epoch_loss = (

        running_loss

        /

        len(

            dataloader.dataset

        )

    )

    ########################################################

    metrics = evaluate(

        np.array(

            targets

        ),

        np.array(

            predictions

        ),

        np.array(

            probabilities

        )

    )

    ########################################################

    metrics["Loss"] = epoch_loss

    ########################################################

    return metrics




############################################################
# Fit
############################################################

def fit(
    model,
    train_loader,
    valid_loader=None,
    criterion=None,
    optimizer=None,
    scheduler=None,
    early_stopping=None,
    trial=None,
    device=None,
    epochs=100,
    checkpoint_path=None,
    gradient_clip=1.0
):
    """
    Complete training loop.

    Parameters
    ----------
    model : nn.Module

    train_loader : DataLoader

    valid_loader : DataLoader

    criterion : Loss

    optimizer : Optimizer

    scheduler : Scheduler

    early_stopping : EarlyStopping

    device : torch.device

    epochs : int

    checkpoint_path : str

    gradient_clip : float

    Returns
    -------
    history
    """

    ########################################################

    scaler = GradScaler(
        "cuda",
        enabled=(device.type == "cuda")
    )



    ########################################################

    history = {

        "train_loss": [],

        "valid_loss": [],

        "train_auc": [],

        "valid_auc": []

    }

    

    ########################################################

    best_metric = -np.inf

    ########################################################

    for epoch in range(

        epochs

    ):

        print(

            f"\nEpoch {epoch+1}/{epochs}"

        )

        ####################################################
        # Training
        ####################################################

        train_metrics = train_one_epoch(

            model=model,

            dataloader=train_loader,

            criterion=criterion,

            optimizer=optimizer,

            device=device,

            scaler=scaler,

            

            gradient_clip=gradient_clip

        )

        ####################################################
        # Validation
        ####################################################

        if valid_loader is not None:

            valid_metrics = validate_one_epoch(
                model=model,
                dataloader=valid_loader,
                criterion=criterion,
                device=device
            )

        else:

            valid_metrics = None


####################################################
# Best Model
####################################################

        if valid_metrics is not None:

            if valid_metrics["ROC_AUC"] > best_metric:

                best_metric = valid_metrics["ROC_AUC"]

                if checkpoint_path is not None:

                    save_model(
                        model,
                        checkpoint_path
                    )
        ####################################################
        # Plateau Scheduler
        ####################################################

        if scheduler is not None:

            if isinstance(scheduler, ReduceLROnPlateau):

                if valid_metrics is not None:

                    scheduler.step(valid_metrics["Loss"])

            else:

                scheduler.step()
        ####################################################
        # History
        ####################################################

        history["train_loss"].append(train_metrics["Loss"])
        history["train_auc"].append(train_metrics["ROC_AUC"])

        if valid_metrics is not None:

            history["valid_loss"].append(valid_metrics["Loss"])
            history["valid_auc"].append(valid_metrics["ROC_AUC"])

        else:

            history["valid_loss"].append(np.nan)
            history["valid_auc"].append(np.nan)


####################################################
# Optuna Pruning
####################################################

        if trial is not None and valid_metrics is not None:

            trial.report(valid_metrics["ROC_AUC"], step=epoch)

            if trial.should_prune():

                raise optuna.TrialPruned()

        ####################################################
        # Print Metrics
        ####################################################

        print(f"Train Loss : {train_metrics['Loss']:.4f}")
        print(f"Train AUC  : {train_metrics['ROC_AUC']:.4f}")

        if valid_metrics is not None:

            print(f"Valid Loss : {valid_metrics['Loss']:.4f}")
            print(f"Valid AUC  : {valid_metrics['ROC_AUC']:.4f}")

       
    ####################################################
        # Early Stopping
    ####################################################

        if valid_metrics is not None and early_stopping is not None:

            early_stopping(valid_metrics["ROC_AUC"])

            if early_stopping.early_stop:

                print("Early stopping triggered.")

                break    
    ########################################################


####################################################
# Save Final Model (No Validation)
####################################################

    if valid_loader is None and checkpoint_path is not None:

        save_model(
            model,
            checkpoint_path
        )


####################################################
# Restore Best Model
####################################################

    if valid_loader is not None and checkpoint_path is not None:

        model = load_model(
            model=model,
            path=checkpoint_path,
            device=device
        )

    return model, history


############################################################
# Predict
############################################################

def predict(

    model,

    dataloader,

    device

):
    """
    Predict class labels.

    Parameters
    ----------
    model : torch.nn.Module

    dataloader : torch.utils.data.DataLoader

    device : torch.device

    Returns
    -------
    numpy.ndarray
        Predicted class labels.
    """

    ########################################################

    model.eval()

    ########################################################

    predictions = []

    ########################################################

    with torch.no_grad():

        ####################################################

        for batch in dataloader:

            ###############################################
            # Dataset may return:
            #   x
            # or
            #   (x, y)
            ###############################################

            if isinstance(

                batch,

                (list, tuple)

            ):

                x = batch[0]

            else:

                x = batch

            ###############################################

            x = x.to(

                device,

                non_blocking=True

            )

            ###############################################

            with autocast(
                "cuda",
                enabled=(device.type == "cuda")
            ):

                output = model(

                    x

                )

            ###############################################
            # Compatible with future models
            ###############################################

            if isinstance(

                output,

                dict

            ):

                logits = output["logits"]

            else:

                logits = output

            ###############################################

            pred = torch.argmax(

                logits,

                dim=1

            )

            ###############################################

            predictions.extend(

                pred.cpu().numpy()

            )

    ########################################################

    return np.asarray(

        predictions

    )


############################################################
# Predict Probabilities
############################################################

def predict_proba(

    model,

    dataloader,

    device

):
    """
    Predict class probabilities.

    Parameters
    ----------
    model : torch.nn.Module

    dataloader : torch.utils.data.DataLoader

    device : torch.device

    Returns
    -------
    numpy.ndarray

        Predicted probabilities

        shape:

        (n_samples, n_classes)
    """

    ########################################################

    model.eval()

    ########################################################

    probabilities = []

    ########################################################

    with torch.no_grad():

        ####################################################

        for batch in dataloader:

            ###############################################
            # Dataset may return:
            # x
            # or
            # (x,y)
            ###############################################

            if isinstance(

                batch,

                (list, tuple)

            ):

                x = batch[0]

            else:

                x = batch

            ###############################################

            x = x.to(

                device,

                non_blocking=True

            )

            ###############################################

            with autocast(
                "cuda",
                enabled=(device.type == "cuda")
            ):

                output = model(

                    x

                )

            ###############################################

            if isinstance(

                output,

                dict

            ):

                logits = output["logits"]

            else:

                logits = output

            ###############################################
            # Softmax
            ###############################################

            prob = torch.softmax(

                logits,

                dim=1

            )

            ###############################################

            probabilities.extend(

                prob.cpu()

                .numpy()

            )

    ########################################################

    return np.asarray(

        probabilities

    )

