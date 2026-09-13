rule supplementary_da_comparison:
    input:
        ancombc2=
            "results/ancombc2/all_results.tsv",

        aldex2=
            "results/aldex2/group_results.tsv",

        maaslin2=
            "results/maaslin2/group_results.tsv"

    output:
        comparison=
            "results/supplementary_da/method_comparison.tsv",

        primary=
            "results/supplementary_da/primary_robustness.tsv"

    params:
        alpha=
            config["differential_abundance"]["alpha"]

    log:
        "logs/supplementary_da/method_comparison.log"

    conda:
        "envs/python.yaml"

    shell:
        r"""
        mkdir -p results/supplementary_da
        mkdir -p logs/supplementary_da

        set -euo pipefail

        python scripts/python/compare_da_methods.py \
            --ancombc2 "{input.ancombc2}" \
            --aldex2 "{input.aldex2}" \
            --maaslin2 "{input.maaslin2}" \
            --output "{output.comparison}" \
            --primary-output "{output.primary}" \
            --alpha {params.alpha} \
            > "{log}" 2>&1

        test -s "{output.comparison}"
        test -f "{output.primary}"
        """