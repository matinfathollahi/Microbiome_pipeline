#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
utils.py

Utility Functions

Supports:
    - Save model
    - Load model
    - Count parameters
    - Print model summary

Project:
Microbiome Meta-analysis
"""

############################################################
# Imports
############################################################

import os
import torch


############################################################
# Save Model
############################################################

def save_model(model, path):
    """
    Save model weights.

    Parameters
    ----------
    model : torch.nn.Module

    path : str
    """

    if path is None:
        return

    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    torch.save(
        model.state_dict(),
        path
    )


############################################################
# Load Model
############################################################

def load_model(model, path, device):
    """
    Load model weights.

    Parameters
    ----------
    model : torch.nn.Module

    path : str

    device : torch.device

    Returns
    -------
    torch.nn.Module
    """

    if path is None:
        return model

    checkpoint = torch.load(
        path,
        map_location=device
    )

    model.load_state_dict(checkpoint)

    model.to(device)

    model.eval()

    return model


############################################################
# Count Parameters
############################################################

def count_parameters(model):
    """
    Count trainable parameters.
    """

    return sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )


############################################################
# Print Model Summary
############################################################

def print_model_summary(model):
    """
    Print model architecture.
    """

    print(model)

    print("-" * 60)

    print(
        f"Trainable Parameters: {count_parameters(model):,}"
    )