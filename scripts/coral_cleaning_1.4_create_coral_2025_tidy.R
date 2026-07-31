

# Clear env
rm(list=ls())

# Load libs
library(tidyverse)
library(here)
library(openxlsx)
library(janitor)

# Set Params 
TEST_MODE <- FALSE # If TEST_MODE is true, only a portion of the data will be
# loaded so that way it's faster to test.




# Load Data
# (M) First try loading just one of the 2024 observation files to test this out
# data_raw > data_raw_2024_sheets > LTER1_BR_P01_P10_2024.xlsx
# Note the column names start on row 2


if(TEST_MODE) {
  # If test mode is true, then we'll only load this one sheet
  data_raw_2025 <- read.xlsx(here("data_raw", "coral_datasheets_2025", "LTER1_BR_T01.xlsx"), 
                             sheet = 1) %>% 
    clean_names()
} else {
  # Otherwise, we'll load ALL THE SHEETS
  # Load them all!
  # The pattern for all of them is starting with LTER and ending with 2024.xlsx
  data_raw_2025_vec <- list.files(here("data_raw", "coral_datasheets_2025"),
                                  pattern = "^LTER.*.xlsx$", full.names = FALSE) %>%
    map(~here("data_raw", "coral_datasheets_2025", .x)) %>%
    map(~read.xlsx(.x, sheet = 1)) %>%
    map(~clean_names(.x))
  # map(~mutate_all(., as.character)) %>%
  # reduce(bind_rows)
  
  # Now loop through each
  # And do renaming
  # # l24 --> l2024
  # # w24 --> w2024
  # # h24 --> h2024
  # dynamics, dyn, and dynamic --> dynam
  # Perform this renaming rule exactly
  # Define renaming rules
  rename_rules <- c(
    "^l25$" = "l2025",
    "^w25$" = "w2025",
    "^h25$" = "h2025",
    "^notes25$" = "notes"
  )
  # 
  # # Apply renaming rules to each dataframe
  data_raw_2025_vec <- map(data_raw_2025_vec, ~ rename_with(.x,
                                                            ~ str_replace_all(., rename_rules)))
  
  # # Now bind them all together
  data_raw_2025 <- data_raw_2025_vec %>%
    map(~mutate_all(., as.character)) %>%
    reduce(bind_rows)
  
  
  
  
  
  # the columns are not named consistently across all files, so I need to figure out which files have which naming schemes
  # so I can go in and change them if necessary
  
  # colnames_of_all_files <- list.files(here("data_raw", "data_raw_2024_sheets"),
  #                           pattern = "^LTER.*2024.xlsx$", full.names = FALSE) %>%
  #   map(~here("data_raw", "data_raw_2024_sheets", .x)) %>% # map to a list where keys are the filenames and values are the colnames()
  #   map(~list(file = .x, colnames = colnames(read.xlsx(.x, sheet = 1, startRow = 2))))
  # 
  # # display the whole list to the console
  # print(colnames_of_all_files)
  
  # map(~read.xlsx(.x, sheet = 1, startRow = 2)) %>%
  # map(~clean_names(.x)) %>%
  # map(~colnames(.x))
  
  
}



# Turn the data into tidy format that can be bound with the tidy data
# Note that the current coral tidy dataset uses columns
#  [1] "coral_number" "site"         "habitat"      "transect"     "taxa"         "x"            "y"            "z"       
# [9] "year"         "length"       "width"        "height"       "observer"     "note"         "note_extra"  

# The cols of data_2024 are
# [1] "site"          "hab"           "tran"          "taxa"          "x"             "y"             "z"            
# [8] "status"        "l2024"         "w2024"         "h2024"         "dynam"         "notes"         "notes_w_dynam"

# For our purposes, we won't use coral number. That original coral number was derived from the row number of the original dataset, and that'll be too tricky to deal with.
# For our notes field, we'll select notes_w_dynam
# year will be 2024

data_2025_tidy <- data_raw_2025 %>%
  select(site, hab, tran, taxa, x, y, z, l2025, w2025, h2025, notes) %>%
  rename(
    length = l2025,
    width = w2025,
    height = h2025,
    habitat = hab,
    transect = tran,
    note = notes
  ) %>%
  mutate(year = 2025, 
         observer = "TBD",
         note_extra = NA) %>% 
  select(site, habitat, transect, taxa, x, y, z, year, length, width, height, observer, note, note_extra)

# Double check the column names, make sure data_2024_tidy
data_2025_tidy %>% colnames()





# Save data_2024_tidy
# save to data_outputs/coral_data_update_tidy_2025.csv
write_csv(data_2025_tidy, here("data_outputs", "coral_data_tidy_2025_for_update.csv"))






