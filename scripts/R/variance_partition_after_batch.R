#!/usr/bin/env Rscript

library(vegan)
library(ggplot2)

############################################################
## Arguments
############################################################

args <- commandArgs(trailingOnly = TRUE)

if(length(args) != 4){
    stop(
        "Usage: variance_partition_after_batch.R <table.tsv> <metadata.tsv> <variables> <output_dir>"
    )
}

table_file    <- args[1]
metadata_file <- args[2]
variables     <- trimws(strsplit(args[3], ",")[[1]])
output_dir    <- args[4]

############################################################
## Check input
############################################################

if(!file.exists(table_file))
    stop("Feature table not found.")

if(!file.exists(metadata_file))
    stop("Metadata file not found.")

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

############################################################
## Read feature table
############################################################

counts <- read.delim(
    table_file,
    row.names = 1,
    check.names = FALSE
)

counts <- t(as.matrix(counts))

############################################################
## Read metadata
############################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE
)

if(!("SampleID" %in% colnames(metadata))){
    stop("SampleID column not found in metadata.")
}

metadata <- metadata[
    match(
        rownames(counts),
        metadata$SampleID
    ),
    ,
    drop = FALSE
]

############################################################
## Remove unmatched samples
############################################################

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

############################################################
## Variance partitioning
############################################################

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


    keep_nonzero <- rowSums(count_sub) > 0


    count_sub <- count_sub[
        keep_nonzero,
        ,
        drop = FALSE
    ]

    meta_sub <- meta_sub[
        keep_nonzero,
        ,
        drop = FALSE
    ]


    if(nrow(count_sub) < 3){
        warning(paste(v, ": insufficient non-zero samples."))
        next
    }


    # Hellinger transformation
    count_sub <- decostand(
        count_sub,
        method = "hellinger"
    )


    # Convert character variables to factor
    if(is.character(meta_sub[[v]])){
        meta_sub[[v]] <- factor(meta_sub[[v]])
    }

    if(length(unique(meta_sub[[v]])) < 2){
        warning(paste(v, ": only one level."))
        next
    }

    fit <- tryCatch({

        formula <- as.formula(
            paste("count_sub ~", v)
        )

        rda(
            formula,
            data = meta_sub
        )

        }, error = function(e) NULL

    )

    if(is.null(fit))
        next

    r2 <- tryCatch(
        RsquareAdj(fit),
        error = function(e) NULL
    )

    if(is.null(r2))
        next

    raw_r2 <- ifelse(is.na(r2$r.squared), 0, r2$r.squared)
    adj_r2 <- ifelse(is.na(r2$adj.r.squared), 0, r2$adj.r.squared)

    raw_r2 <- max(raw_r2, 0)
    adj_r2 <- max(adj_r2, 0)

    results <- rbind(

        results,

        data.frame(

            Variable = v,

            R2 = raw_r2,

            AdjR2 = adj_r2

        )

    )

}

############################################################
## Check results
############################################################

if(nrow(results) == 0){
    stop("No valid variables available.")
}

############################################################
## Sort
############################################################

results <- results[
    order(
        results$AdjR2,
        decreasing = TRUE
    ),
]

############################################################
## Save table
############################################################

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

############################################################
## Plot
############################################################

p <- ggplot(

    results,

    aes(

        reorder(
            Variable,
            AdjR2
        ),

        AdjR2,

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

############################################################
## Save figures
############################################################

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