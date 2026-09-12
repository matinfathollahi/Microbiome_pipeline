#!/usr/bin/env python3

############################################################
# Search Space Definitions
############################################################


def rf_space(trial):

    return {

        "n_estimators":
            trial.suggest_int(
                "n_estimators",
                300,
                2000,
                step=100
            ),

        "max_depth":
            trial.suggest_int(
                "max_depth",
                3,
                40
            ),

        "min_samples_split":
            trial.suggest_int(
                "min_samples_split",
                2,
                20
            ),

        "min_samples_leaf":
            trial.suggest_int(
                "min_samples_leaf",
                1,
                10
            ),

        "max_features":
            trial.suggest_categorical(
                "max_features",
                [
                    "sqrt",
                    "log2",
                    None
                ]
            ),

        "bootstrap":
            trial.suggest_categorical(
                "bootstrap",
                [
                    True,
                    False
                ]
            ),

        "criterion":
            trial.suggest_categorical(
                "criterion",
                [
                    "gini",
                    "entropy",
                    "log_loss"
                ]
            )

    }


############################################################


def svm_space(trial):


    kernel = trial.suggest_categorical(
        "kernel",
        ["linear", "rbf", "poly", "sigmoid"]
    )

    params = {
        "kernel": kernel,
        "C": trial.suggest_float(
            "C",
            1e-4,
            1e4,
            log=True
        )
    }

    # فقط برای کرنل‌هایی که gamma دارند
    if kernel in ["rbf", "poly", "sigmoid"]:
        params["gamma"] = trial.suggest_float(
            "gamma",
            1e-5,
            10,
            log=True
        )

    if kernel == "poly":
        params["degree"] = trial.suggest_int(
            "degree",
            2,
            5
        )
        params["coef0"] = trial.suggest_float(
            "coef0",
            0,
            2
        )

    elif kernel == "sigmoid":
        params["coef0"] = trial.suggest_float(
            "coef0",
            0,
            2
        )

    return params


############################################################


def xgb_space(trial):

    return {

        "n_estimators":

            trial.suggest_int(

                "n_estimators",

                200,

                2000,

                step=100

            ),

        "max_depth":

            trial.suggest_int(

                "max_depth",

                3,

                12

            ),

        "learning_rate":

            trial.suggest_float(

                "learning_rate",

                0.001,

                0.3,

                log=True

            ),

        "subsample":

            trial.suggest_float(

                "subsample",

                0.5,

                1.0

            ),

        "colsample_bytree":

            trial.suggest_float(

                "colsample_bytree",

                0.5,

                1.0

            ),

        "gamma":

            trial.suggest_float(

                "gamma",

                0,

                10

            ),

        "reg_alpha":

            trial.suggest_float(

                "reg_alpha",

                0,

                10

            ),

        "reg_lambda":

            trial.suggest_float(

                "reg_lambda",

                0,

                10

            )

    }


############################################################


def lgbm_space(trial):

    return {

        "n_estimators":

            trial.suggest_int(

                "n_estimators",

                200,

                2000,

                step=100

            ),

        "num_leaves":

            trial.suggest_int(

                "num_leaves",

                15,

                255

            ),

        "max_depth":

            trial.suggest_int(

                "max_depth",

                -1,

                30

            ),

        "learning_rate":

            trial.suggest_float(

                "learning_rate",

                0.001,

                0.3,

                log=True

            ),

        "feature_fraction":

            trial.suggest_float(

                "feature_fraction",

                0.5,

                1.0

            ),

        "bagging_fraction":

            trial.suggest_float(

                "bagging_fraction",

                0.5,

                1.0

            ),

        "bagging_freq": trial.suggest_int(
            "bagging_freq",
            1,
            10
        ),


        "min_child_samples":

            trial.suggest_int(

                "min_child_samples",

                5,

                100

            )

    }


############################################################


def catboost_space(trial):

    return {

        "iterations":

            trial.suggest_int(

                "iterations",

                300,

                2000,

                step=100

            ),

        "depth":

            trial.suggest_int(

                "depth",

                3,

                10

            ),

        "learning_rate":

            trial.suggest_float(

                "learning_rate",

                0.001,

                0.3,

                log=True

            ),

        "l2_leaf_reg":

            trial.suggest_float(

                "l2_leaf_reg",

                1,

                20

            ),

        "bagging_temperature":

            trial.suggest_float(

                "bagging_temperature",

                0,

                10

            )

    }


############################################################

SEARCH_SPACE = {

    "rf": rf_space,

    "svm": svm_space,

    "xgb": xgb_space,

    "lgbm": lgbm_space,

    "catboost": catboost_space

}