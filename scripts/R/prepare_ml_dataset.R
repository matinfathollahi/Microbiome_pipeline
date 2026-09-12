library(dplyr)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 5) {
    stop(
        paste(
            "Usage: Rscript script.R",
            "<table_file>",
            "<metadata_file>",
            "<label_column>",
            "<metadata_columns>",
            "<output_file>"
        )
    )
}

table_file           <- args[1]
metadata_file        <- args[2]
label_column         <- args[3]
metadata_columns_arg <- args[4]
output_file          <- args[5]



########################################################

counts <- read.delim(

    table_file,

    row.names = 1,

    check.names = FALSE

)

if (!all(sapply(counts, is.numeric))) {
    stop("Feature table contains non-numeric values.")
}

########################################################

# Feature table should become:
# rows = samples
# columns = taxa/features

counts <- as.data.frame(t(counts))

counts$SampleID <- rownames(counts)
feature_number <- ncol(counts) - 1

rownames(counts) <- NULL

########################################################

metadata <- read.delim(
    metadata_file,
    check.names = FALSE
)


metadata_columns <- strsplit(
    metadata_columns_arg,
    ",",
    fixed = TRUE
)[[1]]

metadata_columns <- trimws(
    metadata_columns
)

metadata_columns <- metadata_columns[
    nzchar(metadata_columns)
]

# SampleID و label همیشه metadata هستند
metadata_columns <- unique(
    c(
        "SampleID",
        label_column,
        metadata_columns
    )
)

########################################################
# Validate requested metadata columns
########################################################

missing_metadata <- setdiff(
    metadata_columns,
    colnames(metadata)
)

if (length(missing_metadata) > 0) {

    stop(
        paste(
            "Metadata columns not found:",
            paste(
                missing_metadata,
                collapse = ", "
            )
        )
    )
}

########################################################
# CRITICAL:
# Only explicitly declared metadata enters ML dataset
########################################################

metadata <- metadata[
    ,
    metadata_columns,
    drop = FALSE
]






if (!"SampleID" %in% colnames(metadata)) {
    stop("SampleID column not found in metadata.")
}

if (!label_column %in% colnames(metadata)) {
    stop(
        paste("Label column not found in metadata:", label_column)
    )
}



########################################################

########################################################

########################################################
# Validate duplicate SampleIDs
########################################################

if (anyDuplicated(metadata$SampleID) > 0) {

    duplicated_ids <- unique(
        metadata$SampleID[
            duplicated(metadata$SampleID)
        ]
    )

    stop(
        paste(
            "Duplicated SampleID found in metadata:",
            paste(
                duplicated_ids,
                collapse = ", "
            )
        )
    )
}

if (anyDuplicated(counts$SampleID) > 0) {

    duplicated_ids <- unique(
        counts$SampleID[
            duplicated(counts$SampleID)
        ]
    )

    stop(
        paste(
            "Duplicated SampleID found in feature table:",
            paste(
                duplicated_ids,
                collapse = ", "
            )
        )
    )
}
########################################################
dataset <- metadata %>%
    inner_join(
        counts,
        by = "SampleID"
    )

if (nrow(dataset) == 0) {
    stop("No matching SampleID found between metadata and feature table.")
}



# Remove samples with missing class label

dataset <- dataset %>%

    filter(

        !is.na(.data[[label_column]])

    )

if (nrow(dataset) == 0) {
    stop("No samples remain after removing missing labels.")
}

########################################################

# Put important columns first

first_cols <- intersect(
    metadata_columns,
    colnames(dataset)
)


other_cols <- setdiff(

    colnames(dataset),

    first_cols

)

dataset <- dataset[

    ,

    c(

        first_cols,

        other_cols

    )

]

########################################################

write.table(

    dataset,

    output_file,

    sep = "\t",

    quote = FALSE,

    row.names = FALSE
)

########################################################

cat("Samples :", nrow(dataset), "\n")

cat("Features:", feature_number, "\n")