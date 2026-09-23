import os
import subprocess
import qiime2
import pandas as pd


def run_dada2_trial(
    demux,
    output_dir,
    trim_left_f,
    trim_left_r,
    trunc_len_f,
    trunc_len_r,
    max_ee_f,
    max_ee_r
):

    os.makedirs(
        output_dir,
        exist_ok=True
    )


    stats = f"{output_dir}/denoising_stats.qza"

    repseqs = f"{output_dir}/representative_sequences.qza"

    table = f"{output_dir}/feature_table.qza"



    cmd = [

        "qiime",
        "dada2",
        "denoise-paired",

        "--i-demultiplexed-seqs",
        demux,

        "--p-trim-left-f",
        str(trim_left_f),

        "--p-trim-left-r",
        str(trim_left_r),

        "--p-trunc-len-f",
        str(trunc_len_f),

        "--p-trunc-len-r",
        str(trunc_len_r),

        "--p-max-ee-f",
        str(max_ee_f),

        "--p-max-ee-r",
        str(max_ee_r),

        "--o-table",
        table,

        "--o-representative-sequences",
        repseqs,

        "--o-denoising-stats",
        stats
    ]


    subprocess.run(
        cmd,
        check=True
    )


    return stats