library(ggplot2)



args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 3) {
    stop("Usage: Rscript pca.R counts.tsv metadata.tsv output_dir")
}

table_file <- args[1]
metadata_file <- args[2]
output_dir <- args[3]

if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
}

###########################################################

if (!file.exists(table_file)) {
    stop("Counts file does not exist: ", table_file)
}

counts <- read.delim(

    table_file,

    row.names = 1,

    check.names = FALSE

)
counts <- t(counts)
counts <- counts[, apply(counts, 2, var) > 0]

if (ncol(counts) == 0) {
    stop("No genes with non-zero variance remain after filtering.")
}

if (anyNA(counts)) {
    stop("Counts table contains missing values (NA).")
}

###########################################################

###########################################################

if (!file.exists(metadata_file)) {
    stop("Metadata file does not exist: ", metadata_file)
}

metadata <- read.delim(

    metadata_file,

    check.names = FALSE

)

idx <- match(rownames(counts), metadata$SampleID)

if (any(is.na(idx))) {
    stop("Some samples in the counts table are missing from the metadata.")
}

metadata <- metadata[idx, ]

###########################################################

pca <- prcomp(

    counts,

    center=TRUE,

    scale.=TRUE

)

###########################################################

scores <- as.data.frame(

    pca$x

)

scores$SampleID <- rownames(scores)

scores <- cbind(

    scores,

    metadata[, setdiff(names(metadata), "SampleID")]

)

###########################################################

var_exp <- round(

    100 * pca$sdev^2 /

    sum(pca$sdev^2),

    2

)

###########################################################

write.table(

    scores,

    file.path(

        output_dir,

        "pca_coordinates.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)

###########################################################

write.table(

    data.frame(

        PC=paste0(

            "PC",

            seq_along(var_exp)

        ),

        Variance=var_exp

    ),

    file.path(

        output_dir,

        "variance_explained.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)

###########################################################

p <- ggplot(

    scores,

    aes(

        PC1,

        PC2,

        color=Batch,

        shape=Group

    )

)+

geom_point(

    size=3

)+

theme_classic(

    base_size=14

)+

labs(

    x=paste0(

        "PC1 (",

        var_exp[1],

        "%)"

    ),

    y=paste0(

        "PC2 (",

        var_exp[2],

        "%)"

    )

)

###########################################################

ggsave(

    file.path(

        output_dir,

        "PCA_after_batch.pdf"

    ),

    p,

    width=7,

    height=6

)

ggsave(

    file.path(

        output_dir,

        "PCA_after_batch.png"

    ),

    p,

    width=7,

    height=6,

    dpi=300

)