library(ape)

library(ggplot2)

args <- commandArgs(trailingOnly = TRUE)

distance_file <- args[1]

metadata_file <- args[2]

output_dir <- args[3]

if(!dir.exists(output_dir)){
    dir.create(output_dir, recursive=TRUE)
}

##########################################################

dist_mat <- read.delim(

    distance_file,

    row.names = 1,

    check.names = FALSE

)

dist_mat <- as.matrix(dist_mat)

if(!all(rownames(dist_mat) == colnames(dist_mat))){
    stop("Row names and column names of distance matrix do not match")
}

if(!isTRUE(all.equal(dist_mat, t(dist_mat)))){
    stop("Distance matrix is not symmetric")
}

diag(dist_mat) <- 0

dist_mat <- as.dist(dist_mat)

##########################################################

metadata <- read.delim(

    metadata_file,

    check.names = FALSE

)

if(!"SampleID" %in% colnames(metadata)){
    stop("Metadata file must contain SampleID column")
}

##########################################################

pcoa_result <- ape::pcoa(dist_mat)

##########################################################

scores <- as.data.frame(

    pcoa_result$vectors[,1:2]

)

scores$SampleID <- rownames(scores)

scores <- merge(
    scores,
    metadata,
    by="SampleID",
    sort=FALSE,
    all.x=TRUE
)

##########################################################

variance <- round(

    pcoa_result$values$Relative_eig[1:2] * 100,

    2

)

##########################################################

write.table(

    scores,

    file.path(

        output_dir,

        "pcoa_result_coordinates.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)

##########################################################

write.table(

    data.frame(

        Axis=c("PCoA1","PCoA2"),

        Variance=variance

    ),

    file.path(

        output_dir,

        "variance_explained.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)

##########################################################

p <- ggplot(

    scores,

    aes(

        Axis.1,

        Axis.2,

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

        "PCoA1 (",

        variance[1],

        "%)"

    ),

    y=paste0(

        "PCoA2 (",

        variance[2],

        "%)"

    )

)

##########################################################

ggsave(

    file.path(

        output_dir,

        "PCoA_after_batch.pdf"

    ),

    p,

    width=7,

    height=6

)

ggsave(

    file.path(

        output_dir,

        "PCoA_after_batch.png"

    ),

    p,

    width=7,

    height=6,

    dpi=300

)