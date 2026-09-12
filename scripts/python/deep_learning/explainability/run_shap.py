from shap_explainer import (
    load_model,
    prepare_background,
    compute_shap_values,
    summary_plot,
    beeswarm_plot,
    bar_plot,
    waterfall_plot,
    force_plot,
)

from deep_learning.train import get_device

import pandas as pd

####################################################
# Device
####################################################

device = get_device()

####################################################
# Load Data
####################################################

X_train = pd.read_csv(
    "X_train.tsv",
    sep="\t"
)

X_test = pd.read_csv(
    "X_test.tsv",
    sep="\t"
)

####################################################
# Load Model
####################################################

model = load_model(
    model_path="best_model.pt",
    parameter_file="best_parameters.json",
    input_dim=X_train.shape[1],
    output_dim=2,        # تعداد کلاس‌ها
    device=device
)

####################################################
# Background
####################################################

background = prepare_background(
    X_train,
    n_background=100
)

####################################################
# Compute SHAP
####################################################

shap_values, expected_value = compute_shap_values(
    model=model,
    background=background,
    X_explain=X_test,
    device=device
)

####################################################
# Plots
####################################################

summary_plot(
    shap_values,
    X_test,
    "summary.png"
)

beeswarm_plot(
    shap_values,
    X_test,
    "beeswarm.png"
)

bar_plot(
    shap_values,
    X_test,
    "bar.png"
)

waterfall_plot(
    shap_values=shap_values,
    expected_value=expected_value,
    X=X_test,
    sample_index=0,
    output_file="waterfall.png"
)

force_plot(
    shap_values=shap_values,
    expected_value=expected_value,
    X=X_test,
    sample_index=0,
    output_file="force.html"
)

print("Done.")