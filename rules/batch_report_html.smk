rule batch_correction_html:

    input:

        summary="results/batch_correction/report/batch_report.tsv",

        pca_before="results/pca/PCA.pdf",

        pca_after="results/batch_correction/pca/PCA_after_batch.pdf",

        pcoa_before="results/pcoa/PCoA.pdf",

        pcoa_after="results/batch_correction/pcoa/PCoA_after_batch.pdf",

        variance="results/batch_correction/variance_partition/variance_partition.pdf",

        confounding="results/batch_correction/confounding/confounding_after.pdf"

    output:

        "results/batch_correction/report/batch_report.html"

    conda:

        "envs/R.yaml"

    shell:

        """
        Rscript scripts/R/batch_report_html.R \
            {input.summary} \
            {input.pca_before} \
            {input.pca_after} \
            {input.pcoa_before} \
            {input.pcoa_after} \
            {input.variance} \
            {input.confounding} \
            {output}
        """