library(metafor)

library(dplyr)

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
  stop("Usage: Rscript meta.R input_file output_dir")
}

input_file <- args[1]

output_dir <- args[2]

dir.create(

    output_dir,

    recursive = TRUE,

    showWarnings = FALSE

)

############################################################



dat <- read.delim(
    input_file,
    check.names = FALSE
)


dat$EffectSize <- as.numeric(dat$EffectSize)

dat$Variance <- as.numeric(dat$Variance)

# بررسی ستون‌های مورد نیاز
required_cols <- c("FeatureID", "EffectSize", "Variance", "Study")

missing_cols <- setdiff(required_cols, names(dat))

if (length(missing_cols) > 0) {
    stop(
        paste(
            "Missing columns:",
            paste(missing_cols, collapse = ", ")
        )
    )
}

############################################################

features <- unique(
    dat$FeatureID
)

############################################################

for(feature_id in features){

    x <- dat %>%
        filter(
            FeatureID == feature_id
        )

    # حذف ردیف‌هایی که EffectSize یا Variance ندارند
    x <- x %>%
        filter(
            !is.na(EffectSize),
            !is.na(Variance),
            Variance > 0
        )


    if(nrow(x)<2)
        next

############################################################

fit <- tryCatch(

    rma(

        yi=x$EffectSize,

        vi=x$Variance,

        method="REML"

    ),

    error=function(e){

        NULL

    }

)

if(is.null(fit))
    next

############################################################

pdf(
    file.path(
        output_dir,
        paste0(
            gsub(
                "[^[:alnum:]_\\-]",
                "_",
                feature_id
            ),
            "_forest.pdf"
        )
    ),
    width = 8,
    height = 6
)

forest(
    fit,
    slab = x$Study,
    xlab = "Effect Size",
    mlab = "Random Effect",
    cex = 0.9
)

title(
    main = as.character(feature_id)
)

dev.off()
}