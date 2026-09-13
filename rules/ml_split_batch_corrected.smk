# IMPORTANT:
# This branch is a transductive sensitivity analysis.
# MMUPHin harmonization was performed before application
# of the fixed Raw train/test sample IDs.
#
# Do NOT interpret this branch as strict unseen-study
# inductive performance.


rule ml_split_batch_corrected:
    input:
        dataset=
            "results/machine_learning_batch_corrected/"
            "dataset.tsv",

        train_samples=
            "results/machine_learning/split/"
            "train_samples.tsv",

        test_samples=
            "results/machine_learning/split/"
            "test_samples.tsv"

    output:
        train=
            "results/machine_learning_batch_corrected/"
            "train.tsv",

        test=
            "results/machine_learning_batch_corrected/"
            "test.tsv"

    params:
        sample_column=
            "SampleID"

    conda:
        "envs/ml.yaml"

    log:
        "logs/machine_learning_batch_corrected/"
        "split.log"

    shell:
        r"""
        mkdir -p \
            results/machine_learning_batch_corrected

        mkdir -p \
            logs/machine_learning_batch_corrected

        python \
            scripts/python/apply_existing_split.py \
            --dataset "{input.dataset}" \
            --train-samples "{input.train_samples}" \
            --test-samples "{input.test_samples}" \
            --sample-column "{params.sample_column}" \
            --train-output "{output.train}" \
            --test-output "{output.test}" \
            > "{log}" 2>&1
        """