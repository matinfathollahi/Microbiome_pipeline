rule pcoa:
    input:
        bray="results/batch_effect/distance/bray_distance.tsv",
        jaccard="results/batch_effect/distance/jaccard_distance.tsv",
        weighted="results/batch_effect/distance/weighted_unifrac_distance.tsv",
        unweighted="results/batch_effect/distance/unweighted_unifrac_distance.tsv",
        aitchison="results/batch_effect/distance/aitchison_distance.tsv",
        metadata="results/export/metadata/sample_metadata.tsv"

    output:
        bray_coord="results/batch_effect/pcoa/Bray_coordinates.tsv",
        bray_eigen="results/batch_effect/pcoa/Bray_eigenvalues.tsv",
        bray_pdf="results/batch_effect/pcoa/Bray_pcoa.pdf",

        jaccard_coord="results/batch_effect/pcoa/Jaccard_coordinates.tsv",
        jaccard_eigen="results/batch_effect/pcoa/Jaccard_eigenvalues.tsv",
        jaccard_pdf="results/batch_effect/pcoa/Jaccard_pcoa.pdf",

        weighted_coord="results/batch_effect/pcoa/Weighted_UniFrac_coordinates.tsv",
        weighted_eigen="results/batch_effect/pcoa/Weighted_UniFrac_eigenvalues.tsv",
        weighted_pdf="results/batch_effect/pcoa/Weighted_UniFrac_pcoa.pdf",

        unweighted_coord="results/batch_effect/pcoa/Unweighted_UniFrac_coordinates.tsv",
        unweighted_eigen="results/batch_effect/pcoa/Unweighted_UniFrac_eigenvalues.tsv",
        unweighted_pdf="results/batch_effect/pcoa/Unweighted_UniFrac_pcoa.pdf",

        aitchison_coord="results/batch_effect/pcoa/Aitchison_coordinates.tsv",
        aitchison_eigen="results/batch_effect/pcoa/Aitchison_eigenvalues.tsv",
        aitchison_pdf="results/batch_effect/pcoa/Aitchison_pcoa.pdf"

    log:
        "logs/batch_effect/pcoa.log"

    benchmark:
        "benchmark/batch_effect/pcoa.txt"

    threads: 1

    conda:
        "envs/r_batch.yaml"

    shell:
        r"""
        mkdir -p results/batch_effect/pcoa
        mkdir -p logs/batch_effect
        mkdir -p benchmark/batch_effect

        {{

        Rscript scripts/R/pcoa.R \
            {input.bray} \
            Bray \
            {input.metadata} \
            results/batch_effect/pcoa

        Rscript scripts/R/pcoa.R \
            {input.jaccard} \
            Jaccard \
            {input.metadata} \
            results/batch_effect/pcoa

        Rscript scripts/R/pcoa.R \
            {input.weighted} \
            Weighted_UniFrac \
            {input.metadata} \
            results/batch_effect/pcoa

        Rscript scripts/R/pcoa.R \
            {input.unweighted} \
            Unweighted_UniFrac \
            {input.metadata} \
            results/batch_effect/pcoa

        Rscript scripts/R/pcoa.R \
            {input.aitchison} \
            Aitchison \
            {input.metadata} \
            results/batch_effect/pcoa

        }} > {log} 2>&1
        """