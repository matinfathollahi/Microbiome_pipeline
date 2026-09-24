import optuna
import yaml
import json
import os

from run_trial import run_dada2_trial
from scoring import calculate_score

# -------------------------------
# Snakemake inputs / wildcards
# -------------------------------

demux = snakemake.input.demux

# optimization is batch-only

batch = snakemake.wildcards.batch

# -------------------------------
# Load config
# -------------------------------

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)


search_space = config["dada2_optimization"]["search_space"]

n_trials = config["dada2_optimization"]["optimizer"]["trials"]

seed = config["dada2_optimization"]["optimizer"]["seed"]






# -------------------------------
# Bayesian Optimization
# -------------------------------

def objective(trial):

    params = {}


    params["trim_left_f"] = trial.suggest_int(
        "trim_left_f",
        search_space["trim_left_f"]["min"],
        search_space["trim_left_f"]["max"]
    )


    params["trim_left_r"] = trial.suggest_int(
        "trim_left_r",
        search_space["trim_left_r"]["min"],
        search_space["trim_left_r"]["max"]
    )


    params["trunc_len_f"] = trial.suggest_int(
        "trunc_len_f",
        search_space["trunc_len_f"]["min"],
        search_space["trunc_len_f"]["max"]
    )


    params["trunc_len_r"] = trial.suggest_int(
        "trunc_len_r",
        search_space["trunc_len_r"]["min"],
        search_space["trunc_len_r"]["max"]
    )


    params["max_ee_f"] = trial.suggest_categorical(
        "max_ee_f",
        search_space["max_ee_f"]["values"]
    )


    params["max_ee_r"] = trial.suggest_categorical(
        "max_ee_r",
        search_space["max_ee_r"]["values"]
    )


    stats = run_dada2_trial(

        demux=demux,

        output_dir=f"results/qiime2/optimization/{batch}/trial_{trial.number}",

        trim_left_f=params["trim_left_f"],

        trim_left_r=params["trim_left_r"],

        trunc_len_f=params["trunc_len_f"],

        trunc_len_r=params["trunc_len_r"],

        max_ee_f=params["max_ee_f"],

        max_ee_r=params["max_ee_r"],


    ) 


    score = calculate_score(stats)


    return score



# -------------------------------
# Run Optuna
# -------------------------------

study = optuna.create_study(
    direction="maximize",
    sampler=optuna.samplers.TPESampler(
        seed=seed
    )
)


study.optimize(
    objective,
    n_trials=n_trials
)



# -------------------------------
# Save result
# -------------------------------

best_parameters = study.best_params


os.makedirs(
    "results/optimization",
    exist_ok=True
)


with open(
    snakemake.output.params,
    "w"
) as f:

    json.dump(
        best_parameters,
        f,
        indent=4
    )


print("Best parameters:")
print(best_parameters)