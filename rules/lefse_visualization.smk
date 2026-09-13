rule lefse_visualization:
    input:
        significant="results/lefse/significant_taxa.tsv",
        abundance="results/lefse/feature_abundance.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/lefse/figures")

    log:
        "logs/lefse/visualization.log"

    benchmark:
        "benchmark/lefse/visualization.txt"

    conda:
        "envs/R.yaml"

    shell:
        """
        mkdir -p {output}

        Rscript scripts/R/lefse_plots.R \
            results/lefse \
            {output}

        Rscript scripts/R/lefse_heatmap.R \
            {input.abundance} \
            {input.significant} \
            {input.metadata} \
            {output} \
            > {log} 2>&1
        """