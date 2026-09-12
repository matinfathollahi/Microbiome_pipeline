rule batch_correction_report:

    input:

        pca_before="results/pca/pca_variance.tsv",

        pca_after="results/batch_correction/pca/variance_explained.tsv",

        permanova_before="results/permanova/permanova.tsv",

        permanova_after="results/batch_correction/permanova/permanova_after.tsv",

        variance_before="results/variance_partition/variance_partition.tsv",

        variance_after="results/batch_correction/variance_partition/variance_partition.tsv",

        conf_before="results/confounding/confounding_results.tsv",

        conf_after="results/batch_correction/confounding/confounding_after.tsv"

    output:

        directory("results/batch_correction/report")

    log:

        "logs/batch_correction/report.log"

    benchmark:

        "benchmark/batch_correction/report.txt"

    conda:

        "envs/R.yaml"

    shell:

        """
        mkdir -p {output}

        Rscript scripts/R/batch_correction_report.R \
            {input.pca_before} \
            {input.pca_after} \
            {input.permanova_before} \
            {input.permanova_after} \
            {input.variance_before} \
            {input.variance_after} \
            {input.conf_before} \
            {input.conf_after} \
            {output} \
            > {log} 2>&1
        """