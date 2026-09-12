
library(dplyr)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
    stop(
        "Usage: Rscript prepare_meta.R study1,study2 comparison output_dir"
    )
}

studies <- strsplit(args[1], ",")[[1]]
comparison <- args[2]
output_dir <- args[3]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

############################################################

all_results <- data.frame()

############################################################

for(study in studies){

############################################################
## DESeq2
############################################################

file <- file.path(
    "results",
    study,
    "deseq2",
    "results.tsv"
)

if(file.exists(file)){

    x <- read.delim(
        file,
        check.names = FALSE
    )

    out <- data.frame(

        Taxon=x$Taxon,

        EffectSize=x$log2FoldChange,

        StandardError=x$lfcSE,

        Pvalue=x$pvalue,

        FDR=x$padj,

        Study=study,

        Method="DESeq2",

        Comparison=comparison

    )

    all_results <- bind_rows(
        all_results,
        out
    )

}

############################################################
## ANCOMBC
############################################################

file <- file.path(
    "results",
    study,
    "ancombc",
    "results.tsv"
)

if(file.exists(file)){

    x <- read.delim(
        file,
        check.names = FALSE
    )

    out <- data.frame(

        Taxon=x$Taxon,

        EffectSize=x$beta,

        StandardError=x$se,

        Pvalue=x$p_val,

        FDR=x$q_val,

        Study=study,

        Method="ANCOMBC",

        Comparison=comparison

    )

    all_results <- bind_rows(
        all_results,
        out
    )

}

############################################################
## ALDEx2
############################################################

file <- file.path(
    "results",
    study,
    "aldex2",
    "results.tsv"
)

if(file.exists(file)){

    x <- read.delim(
        file,
        check.names = FALSE
    )

    out <- data.frame(

        Taxon=x$Taxon,

        EffectSize=x$effect,

        StandardError=NA_real_,

        Pvalue=x$we.ep,

        FDR=x$we.eBH,

        Study=study,

        Method="ALDEx2",

        Comparison=comparison

    )

    all_results <- bind_rows(
        all_results,
        out
    )

}

############################################################
## MaAsLin2
############################################################

file <- file.path(
    "results",
    study,
    "maaslin2",
    "results.tsv"
)

if(file.exists(file)){

    x <- read.delim(
        file,
        check.names = FALSE
    )

    out <- data.frame(

        Taxon=x$feature,

        EffectSize=x$coef,

        StandardError=x$stderr,

        Pvalue=x$pval,

        FDR=x$qval,

        Study=study,

        Method="MaAsLin2",

        Comparison=comparison

    )

    all_results <- bind_rows(
        all_results,
        out
    )

}

}

############################################################

all_results <- all_results %>%

filter(
    !is.na(EffectSize)
)

if (nrow(all_results) == 0) {
    stop("No results were found.")
}

############################################################

write.table(

    all_results,

    file.path(

        output_dir,

        "meta_prepared.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)

############################################################

split(
    all_results,
    all_results$Study
) |>

lapply(

function(x){

write.table(

x,

file.path(

output_dir,

paste0(

unique(x$Study),

"_prepared.tsv"

)

),

sep="\t",

quote=FALSE,

row.names=FALSE

)

}

)