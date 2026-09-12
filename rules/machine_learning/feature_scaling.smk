rule feature_scaling:

    input:

        train="results/machine_learning/train.tsv",

        test="results/machine_learning/test.tsv"

    output:

        train="results/machine_learning/train_scaled.tsv",

        test="results/machine_learning/test_scaled.tsv"

    conda:

        "envs/ml.yaml"

    log:

        "logs/machine_learning/feature_scaling.log"

    benchmark:

        "benchmark/machine_learning/feature_scaling.txt"

    params:

        method=config["machine_learning"]["scaling"]["method"],

        metadata=",".join(
            config["machine_learning"]["metadata_columns"]
        )

    shell:

        """
        python scripts/python/feature_scaling.py \
            --train {input.train} \
            --test {input.test} \
            --method {params.method} \
            --metadata "{params.metadata}" \
            --train_output {output.train} \
            --test_output {output.test} \
            > {log} 2>&1
        """