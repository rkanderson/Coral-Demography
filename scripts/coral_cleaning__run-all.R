
# This script runs all the coral cleaning scripts in sequence
# They are .Rmd files, so they'll need to be run by Rscript


# Note this doesn't quite work yet.

# Render the .Rmd file
#render("your_file.Rmd", output_format = "html_document")  # You can specify other formats too, like "pdf_document"
rmarkdown::render(here::here("scripts", "coral_cleaning_1_tidy_coral_data.Rmd"))
rmarkdown::render(here::here("scripts", "coral_cleaning_2_add_coral_dynamics.Rmd"))
rmarkdown::render(here::here("scripts", "coral_cleaning_3_widen_coral_data.Rmd"))
rmarkdown::render(here::here("scripts", "coral_cleaning_4_make_excel.Rmd"))
