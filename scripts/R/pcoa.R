library(ape)
library(ggplot2)
library(dplyr)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) != 4) {
    stop("Usage: Rscript pcoa.R distance.tsv method metadata.tsv output_dir")
}

distance_file <- args[1]
method <- args[2]
metadata_file <- args[3]
output_dir <- args[4]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

#-----------------------------
# Read distance matrix
#-----------------------------
distance <- read.delim(
    distance_file,
    row.names = 1,
    check.names = FALSE
)

distance <- as.matrix(distance)

if (any(is.na(distance))) {
    stop("Distance matrix contains missing values.")
}

if (any(distance < 0)) {
    stop("Distance matrix contains negative values.")
}



if (!all(diag(distance) == 0)) {
    stop("Diagonal of distance matrix must be zero.")
}

if (nrow(distance) != ncol(distance)) {
    stop("Distance matrix must be square.")
}

if (!identical(rownames(distance), colnames(distance))) {
    stop("Row names and column names of the distance matrix do not match.")
}

if (!isSymmetric(distance)) {
    stop("Distance matrix is not symmetric.")
}

distance <- as.dist(distance)

#-----------------------------
# Run PCoA
#-----------------------------
pcoa_result <- ape::pcoa(
    distance,
    correction = "cailliez"
)

coordinates <- as.data.frame(
    pcoa_result$vectors
)

print(colnames(coordinates))

coordinates$SampleID <- rownames(coordinates)

#-----------------------------
# Read metadata
#-----------------------------
metadata <- read.delim(
    metadata_file,
    check.names = FALSE
)

if (!"SampleID" %in% colnames(metadata)) {
    stop("Metadata file must contain a 'SampleID' column.")
}

if (!"Group" %in% colnames(metadata)) {
    stop("Metadata file must contain a 'Group' column.")
}

if (anyDuplicated(metadata$SampleID)) {
    stop("Duplicate SampleID values found in metadata.")
}

coordinates <- left_join(
    coordinates,
    metadata,
    by = "SampleID"
)

if (any(is.na(coordinates$Group))) {
    stop("Some samples in the distance matrix are missing from the metadata.")
}

coordinates$Group <- as.factor(coordinates$Group)

if (!all(c("Axis.1", "Axis.2") %in% colnames(coordinates))) {
    stop("PCoA did not return at least two axes.")
}


#-----------------------------
# Save coordinates
#-----------------------------
write.table(
    coordinates,
    file.path(
        output_dir,
        paste0(method, "_coordinates.tsv")
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

#-----------------------------
# Save eigenvalues
#-----------------------------
eigen <- data.frame(
    Axis = seq_along(
        pcoa_result$values$Eigenvalues
    ),
    Eigenvalue = pcoa_result$values$Eigenvalues
)

write.table(
    eigen,
    file.path(
        output_dir,
        paste0(method, "_eigenvalues.tsv")
    ),
    sep = "\t",
    quote = FALSE,
    row.names = FALSE
)

#-----------------------------
# Variance explained
#-----------------------------
if (length(pcoa_result$values$Relative_eig) < 2) {
    stop("PCoA returned fewer than two axes.")
}

var1 <- round(
    pcoa_result$values$Relative_eig[1] * 100,
    2
)

var2 <- round(
    pcoa_result$values$Relative_eig[2] * 100,
    2
)

#-----------------------------
# Plot
#-----------------------------
p <- ggplot(
    coordinates,
    aes(
        x = Axis.1,
        y = Axis.2,
        color = Group
    )
) +
    geom_point(size = 3) +
    labs(
        x = paste0("PCoA1 (", var1, "%)"),
        y = paste0("PCoA2 (", var2, "%)")
    ) +
    theme_classic()

# Draw ellipses only when each group has >= 3 samples
group_sizes <- table(coordinates$Group)

valid_groups <- names(group_sizes[group_sizes >= 3])

if (length(valid_groups) > 0) {
    p <- p +
        stat_ellipse(
            data = subset(coordinates, Group %in% valid_groups),
            level = 0.95
        )
}

ggsave(
    filename = file.path(
        output_dir,
        paste0(method, "_pcoa.pdf")
    ),
    plot = p,
    width = 7,
    height = 6
)