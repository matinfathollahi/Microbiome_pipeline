library(metafor)

library(dplyr)

args <- commandArgs(trailingOnly = TRUE)

input_file <- args[1]

output_dir <- args[2]

dir.create(
    output_dir,
    recursive = TRUE,
    showWarnings = FALSE
)

###########################################################

meta <- read.delim(
    input_file,
    check.names = FALSE
)

###########################################################

features <- unique(meta$FeatureID)

summary_results <- data.frame(

    FeatureID = character(),

    Studies = integer(),

    Egger_Pvalue = numeric(),

    MissingStudies = numeric(),

    stringsAsFactors = FALSE
)

###########################################################

for(feature_id in features){

    x <- meta %>%
        filter(
            FeatureID == feature_id,
            !is.na(EffectSize),
            !is.na(Variance),
            Variance>0
        )

    if(nrow(x)<3)
        next

    fit <- tryCatch(

        rma(
            yi=x$EffectSize,
            vi=x$Variance,
            method="REML"
        ),

        error=function(e) NULL

    )

    if(is.null(fit))
        next

###########################################################
## Funnel Plot
###########################################################

    pdf(

        file.path(

            output_dir,

            paste0(

                gsub("[^A-Za-z0-9_.-]", "_", feature_id),

                "_funnel.pdf"

            )

        ),

        width=6,
        height=6

    )

    funnel(
        fit,
        xlab="Effect Size"
    )

    dev.off()

###########################################################
## Egger Test
###########################################################

    egger <- if(nrow(x) >= 10){

        tryCatch(

            regtest(
                fit,
                model="rma",
                predictor="sei"
            ),

            error=function(e) NULL

        )

    } else {

        NULL

    }

###########################################################
## Trim & Fill
###########################################################

    tf <- tryCatch(
        trimfill(fit),
        warning=function(w) NULL,
        error=function(e) NULL
    )

###########################################################

    summary_results <- rbind(

        summary_results,

        data.frame(

            FeatureID=feature_id,

            Studies=nrow(x),

            Egger_Pvalue=

            ifelse(

                is.null(egger),

                NA,

                egger$pval

            ),

            MissingStudies=

            ifelse(

                is.null(tf),

                NA,

                tf$k0

            )

        )

    )

}

###########################################################

write.table(

    summary_results,

    file.path(

        output_dir,

        "publication_bias.tsv"

    ),

    sep="\t",

    quote=FALSE,

    row.names=FALSE

)