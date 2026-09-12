#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
dataloader.py

Utility functions for creating PyTorch DataLoaders.

Features
--------
- Automatic DataLoader creation
- Multi-worker loading
- Pinned memory support
- Persistent workers

Author : Matin Fathollahi
Project: Microbiome Meta-analysis
License: All Rights Reserved
"""

################################################################
import torch

from torch.utils.data import DataLoader

############################################################

def create_dataloader(

    dataset,

    batch_size=64,

    shuffle=True,

    num_workers=4,

    pin_memory=None,

    drop_last=False

):

    """
    Create PyTorch DataLoader.

    Parameters
    ----------
    dataset : Dataset

    batch_size : int

    shuffle : bool

    num_workers : int

    pin_memory : bool

    drop_last : bool

    Returns
    -------
    torch.utils.data.DataLoader
    """

    if pin_memory is None:
        pin_memory = torch.cuda.is_available()

    loader = DataLoader(

        dataset=dataset,

        batch_size=batch_size,

        shuffle=shuffle,

        num_workers=num_workers,

        pin_memory=pin_memory,

        drop_last=drop_last,

        persistent_workers=(num_workers > 0)

    )

    return loader