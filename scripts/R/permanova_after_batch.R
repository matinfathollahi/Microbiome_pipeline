library(vegan)

args <- commandArgs(trailingOnly = TRUE)

distance_file <- args[1]

metadata_file <- args[2]

output_file <- args[3]

########################################################

dist_mat <- read.delim(

    distance_file,

    row.names = 1,

    check.names = FALSE

)

dist_mat <- as.matrix(dist_mat)

dist_mat <- as.dist(dist_mat)

########################################################

metadata <- read.delim(

    metadata_file,

    check.names = FALSE

)

########################################################
## Align metadata with distance matrix
########################################################

sample_order <- labels(dist_mat)

idx <- match(
    sample_order,
    metadata$SampleID
)

if(any(is.na(idx))){
    missing_samples <- sample_order[is.na(idx)]
    stop(
        paste(
            "Missing samples in metadata:",
            paste(missing_samples, collapse=", ")
        )
    )
}

metadata <- metadata[idx, ]

if(nrow(metadata) != attr(dist_mat, "Size")){
    stop("Number of metadata samples does not match distance matrix")
}


# اطمینان نهایی
if(!all(metadata$SampleID == sample_order)){
    stop("Metadata order does not match distance matrix order")
}


########################################################
## Check metadata columns
########################################################

required_columns <- c("Batch", "Group")

if(!all(required_columns %in% colnames(metadata))){
    
    missing_columns <- required_columns[
        !required_columns %in% colnames(metadata)
    ]
    
    stop(
        paste(
            "Missing metadata columns:",
            paste(missing_columns, collapse=", ")
        )
    )
}


metadata$Batch <- as.factor(metadata$Batch)
metadata$Group <- as.factor(metadata$Group)

if(any(is.na(metadata$Batch)) || any(is.na(metadata$Group))){
    stop("Batch or Group contains missing values")
}

########################################################
## Combined model
########################################################

combined_model <- adonis2(

    dist_mat ~

    Batch +

    Group,

    data = metadata,

    permutations = 9999,

    by = "margin"

)

########################################################

########################################################
## Extract results from combined model
########################################################

results <- data.frame(

    Variable = rownames(combined_model)[1:2],

    R2 = combined_model$R2[1:2],

    F = combined_model$F[1:2],

    Pvalue = combined_model$`Pr(>F)`[1:2]

)
########################################################

write.table(

    results,

    output_file,

    sep = "\t",

    quote = FALSE,

    row.names = FALSE

)

########################################################

capture.output(

    combined_model,

    file = sub(
        "\\.tsv$",
        "_combined.txt",
        output_file
    )

)