rule pca:

    input:
        table="results/batch_effect/feature_table_clr.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        scores="results/batch_effect/pca/pca_scores.tsv",
        loadings="results/batch_effect/pca/pca_loadings.tsv",
        variance="results/batch_effect/pca/pca_variance.tsv",
        figure="results/batch_effect/pca/pca.pdf"

    log:
        "logs/batch_effect/pca.log"

    benchmark:
        "benchmark/batch_effect/pca.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p results/batch_effect/pca

        Rscript scripts/R/pca.R \
            {input.table} \
            {input.metadata} \
            results/batch_effect/pca \
            > {log} 2>&1
        """