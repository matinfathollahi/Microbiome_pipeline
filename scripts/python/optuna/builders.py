#!/usr/bin/env python3

############################################################
# Model Builders
############################################################

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

from xgboost import XGBClassifier

from lightgbm import LGBMClassifier

from catboost import CatBoostClassifier

############################################################
# Random Forest
############################################################

def build_rf(

    params,

    random_seed

):

    params = params.copy()

    params.update({

        "class_weight": "balanced",

        "random_state": random_seed,

        "n_jobs": -1

    })

    model = RandomForestClassifier(

        **params

    )

    return model


############################################################
# SVM
############################################################

def build_svm(

    params,

    random_seed

):

    params = params.copy()

    params.update({

        "probability": True,

        "class_weight": "balanced",

        "random_state": random_seed

    })

    model = Pipeline(

        [

            (

                "scaler",

                StandardScaler()

            ),

            (

                "svm",

                SVC(

                    **params

                )

            )

        ]

    )

    return model


############################################################
# XGBoost
############################################################

def build_xgb(

    params,

    random_seed

):

    params = params.copy()

    params.update({

        "random_state": random_seed,

        "n_jobs": -1,

        "verbosity": 0,

        "eval_metric": "mlogloss"

    })

    model = XGBClassifier(

        **params

    )

    return model


############################################################
# LightGBM
############################################################

def build_lgbm(

    params,

    random_seed

):

    params = params.copy()

    params.update({

        "random_state": random_seed,

        "class_weight": "balanced",

        "verbosity": -1,

        "n_jobs": -1

    })

    model = LGBMClassifier(

        **params

    )

    return model


############################################################
# CatBoost
############################################################

def build_catboost(

    params,

    random_seed

):

    params = params.copy()

    params.update({

        "random_seed": random_seed,

        "verbose": False,

        "auto_class_weights": "Balanced"

    })

    model = CatBoostClassifier(

        **params

    )

    return model


############################################################
# Registry
############################################################

MODEL_BUILDERS = {

    "rf": build_rf,

    "svm": build_svm,

    "xgb": build_xgb,

    "lgbm": build_lgbm,

    "catboost": build_catboost

}