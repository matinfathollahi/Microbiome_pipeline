#!/usr/bin/env Rscript

library(vegan)
library(ggplot2)


########################################################
## Arguments
########################################################

args <- commandArgs(trailingOnly = TRUE)

if(length(args) != 4){
    stop(
        "Usage: variance_partition.R <table.tsv> <metadata.tsv> <variables> <output_dir>"
    )
}

table_file    <- args[1]
metadata_file <- args[2]
variables     <- trimws(strsplit(args[3], ",")[[1]])
output_dir    <- args[4]

########################################################
## Check input
########################################################

if(!file.exists(table_file)){
    stop("Feature table not found.")
}

if(!file.exists(metadata_file)){
    stop("Metadata file not found.")
}

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

########################################################
## Read feature table
########################################################

counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE
)

counts <- t(as.matrix(counts))

counts <- decostand(
    counts,
    method = "hellinger"
)


keep_nonzero <- rowSums(counts) > 0

counts <- counts[
    keep_nonzero,
    ,
    drop = FALSE
]

########################################################
## Read metadata
########################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE
)

if(!("SampleID" %in% colnames(metadata))){
    stop("SampleID column not found in metadata.")
}


if(anyDuplicated(metadata$SampleID)){
    dup <- unique(metadata$SampleID[duplicated(metadata$SampleID)])

    stop(
        paste(
            "Duplicate SampleID found:",
            paste(dup, collapse = ", ")
        )
    )
}

metadata <- metadata[
    match(
        rownames(counts),
        metadata$SampleID
    ),
    ,
    drop = FALSE
]

########################################################
## Remove unmatched samples
########################################################

valid <- !is.na(metadata$SampleID)

metadata <- metadata[
    valid,
    ,
    drop = FALSE
]

counts <- counts[
    valid,
    ,
    drop = FALSE
]

########################################################
## Variance partition
########################################################

results <- data.frame()

for(v in variables){

    if(!(v %in% colnames(metadata))){
        warning(paste("Variable", v, "not found."))
        next
    }

    keep <- complete.cases(metadata[, v, drop = FALSE])

    if(sum(keep) < 3){
        warning(paste(v, ": insufficient samples."))
        next
    }

    meta_sub <- metadata[
        keep,
        ,
        drop = FALSE
    ]

    count_sub <- counts[
        keep,
        ,
        drop = FALSE
    ]

    if(length(unique(meta_sub[[v]])) < 2){
        warning(paste(v, ": only one level."))
        next
    }

    fit <- tryCatch(

        rda(
            as.formula(paste("count_sub ~", v)),
            data = meta_sub
        ),

        error = function(e) NULL

    )

    if(is.null(fit))
        next

    adj_r2 <- RsquareAdj(fit)$adj.r.squared

    pvalue <- tryCatch(

        anova.cca(
            fit,
            permutations = 999
        )$`Pr(>F)`[1],

        error = function(e) NA

    )

    if(is.na(adj_r2))
        adj_r2 <- 0

    

    results <- rbind(

        results,

        data.frame(

            Variable = v,

            Adjusted_R2 = adj_r2,

            Pvalue = pvalue

        )

    )
}

########################################################
## Check results
########################################################

if(nrow(results) == 0){
    stop("No valid variables available for variance partitioning.")
}

########################################################
## Sort
########################################################

results <- results[
    order(
        results$Adjusted_R2,
        decreasing = TRUE
    ),
]

########################################################
## Save table
########################################################

write.table(

    results,

    file.path(
        output_dir,
        "variance_partition.tsv"
    ),

    sep = "\t",

    quote = FALSE,

    row.names = FALSE

)

########################################################
## Plot
########################################################

p <- ggplot(

    results,

    aes(

        reorder(
            Variable,
            Adjusted_R2
        ),

        Adjusted_R2,

        fill = Variable

    )

) +

geom_col(width = 0.8) +

coord_flip() +

theme_classic(base_size = 14) +

xlab("") +

ylab("Adjusted R²") +

theme(

    legend.position = "none",

    axis.text.y = element_text(face = "bold")

)

########################################################
## Save figures
########################################################

ggsave(

    file.path(
        output_dir,
        "variance_partition.pdf"
    ),

    p,

    width = 8,

    height = 5

)

ggsave(

    file.path(
        output_dir,
        "variance_partition.png"
    ),

    p,

    width = 8,

    height = 5,

    dpi = 300

)