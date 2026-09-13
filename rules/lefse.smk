rule lefse:
    input:
        table="results/export/feature_table/feature-table.tsv",
        taxonomy="results/export/taxonomy/taxonomy.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        significant="results/lefse/significant_taxa.tsv",
        raw="results/lefse/lefse_results.res",
        abundance="results/lefse/feature_abundance.tsv",
        mapping="results/lefse/feature_mapping.tsv"

    params:
        outdir="results/lefse",
        class_column=config["lefse"]["class_column"],
        normalization=config["lefse"]["normalization"],
        alpha=config["lefse"]["alpha"],
        lda=config["lefse"]["lda_threshold"]

    log:
        "logs/lefse/lefse.log"

    benchmark:
        "benchmark/lefse/lefse.txt"

    conda:
        "envs/lefse.yaml"

    shell:
        """
        mkdir -p results/lefse
        mkdir -p $(dirname {log})

        bash scripts/bash/lefse.sh \
            {input.table} \
            {input.taxonomy} \
            {input.metadata} \
            {params.outdir} \
            "{params.class_column}" \
            {params.normalization} \
            {params.alpha} \
            {params.lda} \
            > {log} 2>&1
        """