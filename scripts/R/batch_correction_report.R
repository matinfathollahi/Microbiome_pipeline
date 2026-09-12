

library(openxlsx)

args <- commandArgs(trailingOnly=TRUE)

if (length(args) != 9) {
    stop(
        paste(
            "Expected 9 input arguments, but received",
            length(args)
        )
    )
}

pca_before <- read.delim(args[1])

pca_after <- read.delim(args[2])

perm_before <- read.delim(args[3])

perm_after <- read.delim(args[4])

var_before <- read.delim(args[5])

var_after <- read.delim(args[6])

conf_before <- read.delim(args[7])

conf_after <- read.delim(args[8])

output_dir <- args[9]

dir.create(
    output_dir,
    recursive=TRUE,
    showWarnings=FALSE
)


if (!"Batch" %in% perm_before$Variable)
    stop("Batch not found in perm_before")

if (!"Batch" %in% perm_after$Variable)
    stop("Batch not found in perm_after")

if (!"Batch" %in% var_before$Variable)
    stop("Batch not found in var_before")

if (!"Batch" %in% var_after$Variable)
    stop("Batch not found in var_after")

if (!"Batch" %in% conf_before$Variable)
    stop("Batch not found in conf_before")

if (!"Batch" %in% conf_after$Variable)
    stop("Batch not found in conf_after")


##########################################################

report  <- data.frame(

    Metric=c(

        "Batch PERMANOVA R2",

        "Batch PERMANOVA P",

        "Batch Variance",

        "Batch Confounding FDR"

    ),

    Before=c(

        perm_before$R2[
            perm_before$Variable=="Batch"
        ],

        perm_before$Pvalue[
            perm_before$Variable=="Batch"
        ],

        var_before$AdjR2[
            var_before$Variable=="Batch"
        ],

        conf_before$FDR[
            conf_before$Variable=="Batch"
        ]

    ),

    After=c(

        perm_after$R2[
            perm_after$Variable=="Batch"
        ],

        perm_after$Pvalue[
            perm_after$Variable=="Batch"
        ],

        var_after$AdjR2[
            var_after$Variable=="Batch"
        ],

        conf_after$FDR[
            conf_after$Variable=="Batch"
        ]

    )

)

##########################################################

report$Difference <-

report$After -

report$Before

##########################################################

write.table(

    report,

    file.path(

        output_dir,

        "batch_report.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)

##########################################################

write.xlsx(

    report,

    file.path(

        output_dir,

        "batch_report.xlsx"

    ),

    overwrite=TRUE

)

##########################################################

##########################################################

sink(
    file.path(
        output_dir,
        "batch_report.txt"
    )
)

on.exit(sink(), add = TRUE)

cat("--------------------------------\n")

cat("Batch Correction Summary\n")

cat("--------------------------------\n\n")

print(report)

cat("\n")

##########################################################

if(

report$After[1] <

report$Before[1]

){

cat(

"✓ Batch variance decreased.\n"

)

}else{

cat(

"✗ Batch variance did not decrease.\n"

)

}

##########################################################

if(

report$After[2] >

0.05

){

cat(

"✓ Batch PERMANOVA is no longer significant.\n"

)

}else{

cat(

"✗ Batch effect is still significant.\n"

)

}

##########################################################

sink()