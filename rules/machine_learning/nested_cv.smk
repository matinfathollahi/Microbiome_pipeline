rule nested_cv:

    input:
        "results/machine_learning/train.tsv"

    output:
        directory("results/machine_learning/nested_cv")

    log:
        "logs/machine_learning/nested_cv.log"

    benchmark:
        "benchmark/machine_learning/nested_cv.txt"

    conda:
        "envs/ml.yaml"

    params:
        label=config["machine_learning"]["label"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        ),

        
        inner=config["machine_learning"]["nested_cv"]["inner_folds"],
        seed=config["machine_learning"]["nested_cv"]["random_seed"],

        variance_threshold=
            config["machine_learning"]["variance_filter"]["threshold"],

        boruta_trees=
            config["machine_learning"]["boruta"]["n_estimators"],

        group=
            config["machine_learning"]["group_column"],

        boruta_max_iter=
            config["machine_learning"]["boruta"]["max_iter"],

        boruta_seed=
            config["machine_learning"]["boruta"]["random_seed"],

        elastic_cv=
            config["machine_learning"]["elasticnet"]["cv"],

        elastic_l1=
            config["machine_learning"]["elasticnet"]["l1_ratio"],

        elastic_seed=
            config["machine_learning"]["elasticnet"]["random_seed"],

        rf_trees=
            config["machine_learning"]["random_forest"]["trees"],

        rf_top=
            config["machine_learning"]["random_forest"]["top_features"],

        rf_seed=
            config["machine_learning"]["random_forest"]["random_seed"],


        consensus_min=
            config["machine_learning"]["consensus"]["min_methods"],

        min_count=
            config["filtering"]["min_count"],

        prevalence=
            config["filtering"]["prevalence"],

        zero_fraction=
            config[
                "machine_learning"
            ][
                "predictive_preprocessing"
            ][
                "zero_fraction"
            ]



    shell:
        """
        python scripts/python/nested_cv.py \
            --input {input} \
            --label "{params.label}" \
            --metadata "{params.metadata}" \
            --group "{params.group}" \
            --inner {params.inner} \
            --seed {params.seed} \
            --variance_threshold {params.variance_threshold} \
            --boruta_trees {params.boruta_trees} \
            --boruta_max_iter {params.boruta_max_iter} \
            --boruta_seed {params.boruta_seed} \
            --elastic_cv {params.elastic_cv} \
            --elastic_l1 {params.elastic_l1} \
            --elastic_seed {params.elastic_seed} \
            --rf_trees {params.rf_trees} \
            --rf_top {params.rf_top} \
            --rf_seed {params.rf_seed} \
            --consensus_min {params.consensus_min} \
            --min_count {params.min_count} \
            --prevalence {params.prevalence} \
            --zero_fraction {params.zero_fraction} \
            --output results/machine_learning/nested_cv \
            > {log} 2>&1
        """