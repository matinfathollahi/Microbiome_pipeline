"""
objective.py

Optuna objective function used for hyperparameter
optimization of deep learning models.

Responsibilities
----------------
- Sample hyperparameters
- Build model
- Train model
- Validate model
- Return ROC-AUC score

Author : Matin Fathollahi
Project: Microbiome Meta-analysis
License: 
"""

############################################################
# Imports
############################################################
import os
import gc
import torch
import torch.nn as nn
import random
import numpy as np

from torch.utils.data import DataLoader


from deep_learning.models.mlp import build_mlp
from sklearn.preprocessing import StandardScaler

from deep_learning.dataset import MicrobiomeDataset

from deep_learning.train import fit

from deep_learning.early_stopping import EarlyStopping

from deep_learning.optuna.search_space import get_search_space

############################################################
# Objective
############################################################

def objective(
    trial,
    X_train,
    y_train,
    X_valid,
    y_valid,
    device,
    seed,
    enable_pruning=True
):
    """
    Optuna objective function.
    """

    SEED = seed

    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    if torch.cuda.is_available():
        torch.cuda.manual_seed(SEED)
        torch.cuda.manual_seed_all(SEED)

    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    ########################################################
    # Hyperparameters
    ########################################################

    params = get_search_space(

        "MLP"

    )(trial)




    ########################################################
    # Fold-specific scaling
    # Fit ONLY on inner training data
    ########################################################

    scaler = StandardScaler()

    X_train_scaled = scaler.fit_transform(
        X_train
    )

    X_valid_scaled = scaler.transform(
        X_valid
    )
    ########################################################
  

    ########################################################
    # Dataset
    ########################################################

    train_dataset = MicrobiomeDataset(

        X_train_scaled,

        y_train

    )

    valid_dataset = MicrobiomeDataset(

        X_valid_scaled,

        y_valid

    )

    ########################################################
    # DataLoader
    ########################################################

    train_loader = DataLoader(

        train_dataset,

        batch_size=params["batch_size"],

        shuffle=True,

        drop_last=False

    )

    valid_loader = DataLoader(

        valid_dataset,

        batch_size=params["batch_size"],

        shuffle=False

    )

    ########################################################
    # Model
    ########################################################

    model = build_mlp(
        params=params,
        input_dim=X_train.shape[1],
        output_dim=np.unique(
            np.concatenate([y_train, y_valid])
        ).size
    )
    model.to(device)

    ########################################################
    # Loss
    ########################################################

    criterion = nn.CrossEntropyLoss()

    ########################################################
    # Optimizer
    ########################################################

    if params["optimizer"] == "Adam":

        optimizer = torch.optim.Adam(

            model.parameters(),

            lr=params["learning_rate"],

            weight_decay=params["weight_decay"]

        )

    elif params["optimizer"] == "AdamW":

        optimizer = torch.optim.AdamW(

            model.parameters(),

            lr=params["learning_rate"],

            weight_decay=params["weight_decay"]

        )

    elif params["optimizer"] == "RMSprop":

        optimizer = torch.optim.RMSprop(

            model.parameters(),

            lr=params["learning_rate"],

            weight_decay=params["weight_decay"]

        )
    else:
        raise ValueError(f"Unknown optimizer: {params['optimizer']}")

    ########################################################
    # Scheduler
    ########################################################

    scheduler = None

    if params["scheduler"] == "Plateau":

        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            patience=5
        )

    elif params["scheduler"] == "Cosine":

        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=200
        )

    elif params["scheduler"] == "Step":

        scheduler = torch.optim.lr_scheduler.StepLR(
            optimizer,
            step_size=params["step_size"],
            gamma=params["gamma"]
        )

    elif params["scheduler"] in (None, "None"):

        scheduler = None

    else:

        raise ValueError(
            f"Unknown scheduler: {params['scheduler']}"
        )





    ########################################################
    # Early Stopping
    ########################################################

    early_stopping = EarlyStopping(

        patience=params["patience"],

        mode="max"

    )

    ########################################################
    # Train
    ########################################################

    checkpoint_path = f"tmp_trial_{trial.number}.pt"

    best_auc = 0.0

    try:

        model, history = fit(
            model=model,
            train_loader=train_loader,
            valid_loader=valid_loader,
            criterion=criterion,
            optimizer=optimizer,
            scheduler=scheduler,
            early_stopping=early_stopping,
            trial=trial if enable_pruning else None,
            device=device,
            epochs=200,
            checkpoint_path=checkpoint_path,
            gradient_clip=params["gradient_clip"]
        )

        if len(history["valid_auc"]) == 0:
            best_auc = 0.0
        else:
            best_auc = np.nanmax(history["valid_auc"])

    finally:

        try:
            os.remove(checkpoint_path)
        except FileNotFoundError:
            pass

        del model
        del optimizer
        del scheduler
        del criterion
        del train_loader
        del valid_loader
        del train_dataset
        del valid_dataset
        
        if "history" in locals():
            del history
        
        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    return best_auc


