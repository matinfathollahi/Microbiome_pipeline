rule permanova:
    input:
        bray="results/batch_effect/distance/bray_distance.tsv",
        jaccard="results/batch_effect/distance/jaccard_distance.tsv",
        aitchison="results/batch_effect/distance/aitchison_distance.tsv",
        weighted="results/batch_effect/distance/weighted_unifrac_distance.tsv",
        unweighted="results/batch_effect/distance/unweighted_unifrac_distance.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        directory("results/batch_effect/permanova")

    params:
        seed=config["permanova"]["seed"]

    log:
        "logs/batch_effect/permanova.log"

    benchmark:
        "benchmark/batch_effect/permanova.txt"

    conda:
        "envs/r_batch.yaml"

    shell:
        """
        mkdir -p {output}

        {{
            Rscript scripts/R/permanova.R {input.bray} Bray {input.metadata} {output} {params.seed}
            Rscript scripts/R/permanova.R {input.jaccard} Jaccard {input.metadata} {output} {params.seed}
            Rscript scripts/R/permanova.R {input.aitchison} Aitchison {input.metadata} {output} {params.seed}
            Rscript scripts/R/permanova.R {input.weighted} Weighted_UniFrac {input.metadata} {output} {params.seed}
            Rscript scripts/R/permanova.R {input.unweighted} Unweighted_UniFrac {input.metadata} {output} {params.seed}
        }} > {log} 2>&1
        """