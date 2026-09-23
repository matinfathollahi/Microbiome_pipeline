import qiime2
import pandas as pd


def calculate_score(stats_qza):


    stats = qiime2.Artifact.load(
        stats_qza
    )


    df = stats.view(
        pd.DataFrame
    )


    input_reads = df["input"].sum()

    merged_reads = df["merged"].sum()

    nonchim_reads = df["non-chimeric"].sum()


    if input_reads == 0:
        return 0



    merge_rate = merged_reads / input_reads

    nonchim_rate = nonchim_reads / input_reads



    score = (
        0.5 * merge_rate +
        0.5 * nonchim_rate
    )


    return score