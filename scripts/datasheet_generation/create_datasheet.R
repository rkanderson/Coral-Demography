


# We want to have a spreadsheet for entering in data that is easy to use. 
# 
# It should be filtered to only get corals that are still alive. 
# (Or at least not confirmed to be dead).
# 
# It should have fields for the Site, Habitat, Transect, Taxa, Coordiantes, Measurements for the Previous Year, and then blank fields for measurements in the current survey Year.
# 
# So for example, if our survey year was 2024, then the fields we would want in our datasheet are
# 
# Site, Hab, Tran, Taxa, X, Y, Z, W23, L23, H23, Notes23, And then blank fields for L24, W24, H24, Notes24


# Clear env
rm(list=ls())

# Load Libs
library(tidyverse)
library(here)
library(openxlsx)

# PARAMETERS
# MOST_RECENT_SURVEY_YEAR <- 2024


# Load the data (we're going to start off with the tidy data with dynamics)
# data_outputs/coral_tidy_2024_with_dynamics.csv

coral_df_tidy <- read_csv(here("data_outputs", "coral_tidy_2024_with_dynamics.csv"))


# Now we're going to group the corals by coral_number
# and then we're going to summarize each group by whether that group contains any single
# dyn_death == 1

coral_death_summary <- coral_df_tidy %>% 
  group_by(coral_number) %>% 
  summarize(any_death = any(dyn_death == 1))

# Now let's load our wide dataset
# data_outputs/coral_clean_wide_2024.csv

coral_df_wide <- read_csv(here("data_outputs", "coral_clean_wide_2024.csv"))

# Now let's filter to only keep corals not confirmed dead
# We'll do this by doing a left join on our wide dataset, and then filtering to only keep rows where any_death == FALSE.
coral_df_wide_no_dead <- coral_df_wide %>% 
  left_join(coral_death_summary, by = "coral_number") %>% 
  filter(any_death == FALSE)

# Now let's only keep the columns relevant for our data entry sheet.
# We'll need to use the CURRENT_SURVEY_YEAR (at some point)
# for now I'll just hardcode for 2024
coral_df_no_dead_selected_cols <- coral_df_wide_no_dead %>% 
  select(site, habitat, transect, taxa, x, y, z, length_2024, width_2024, height_2024, note_2024)


# Now let's rename the columns to be more user-friendly
coral_df_no_dead_selected_cols <- coral_df_no_dead_selected_cols %>% 
  rename(
    Site = site,
    Hab = habitat,
    Tran = transect,
    Taxa = taxa,
    X = x,
    Y = y,
    Z = z,
    L24 = length_2024,
    W24 = width_2024,
    H24 = height_2024,
    Notes24 = note_2024
  )


# Little nitpick, many of the Notes24 values contain a comma separated list containing NA
# (This is an artifact from a previous operation)
# let's remove these for the datasheet by splitting Notes24 by comma, filtering out "NA" string,
# and then pasting back together
coral_df_no_dead_selected_cols <- coral_df_no_dead_selected_cols %>% 
  mutate(
    Notes24 = sapply(Notes24, function(x) {
      notes_split <- unlist(strsplit(x, ","))
      notes_filtered <- notes_split[notes_split != "NA"]
      notes_pasted <- paste(notes_filtered, collapse = ", ")
      return(notes_pasted)
    })
  )


# Now we'll add some blank fields for data entry for the coming survey year
# (2025)
coral_df_for_datasheet <- coral_df_no_dead_selected_cols %>% 
  mutate(
    L25 = NA,
    W25 = NA,
    H25 = NA,
    Notes25 = NA
  )


# Finally we'll save this to an excel spreadsheet where there's a separate tab
# for each combo of Site, Habitat, and Transect
# The title of each tab should be in the format Site_Hab_Tran

# Save to Excel with separate tabs
datasheet_filepath <- here("data_outputs", "coral_data_entry_datasheet_2025.xlsx")

# Get unique combinations of Site, Hab, Tran
unique_combos <- coral_df_for_datasheet %>%
  select(Site, Hab, Tran) %>%
  distinct()
# 
data_list <- list()

wb <- createWorkbook()
for (i in 1:nrow(unique_combos)) {
  site_i <- unique_combos$Site[i]
  hab_i <- unique_combos$Hab[i]
  tran_i <- unique_combos$Tran[i]

  sheet_name <- paste(site_i, hab_i, tran_i, sep = "_")
  #
  # Filter data for this combo
  data_i <- coral_df_for_datasheet %>%
    filter(Site == site_i, Hab == hab_i, Tran == tran_i)

  # append to data_list
  data_list[[sheet_name]] <- data_i


  # Add worksheet
  addWorksheet(wb, sheet_name)
  
  # print(sheet_name)
  # print(dim(data_i))
  # print(rownames(data_i))
  
  rownames(data_i) <- NULL
  

  # Write data to worksheet
  writeData(wb, sheet = sheet_name, x = data_i)
}

## DEBUG
# display all the colnames for all data_list items
for (name in names(data_list)) {
  cat("Sheet:", name, "\n")
  print(colnames(data_list[[name]]))
  cat("\n")
}

# Do this but get all the distinct values of colnames
all_colnames <- unique(unlist(lapply(data_list, colnames)))

# Save workbook
saveWorkbook(wb, file = datasheet_filepath, overwrite = TRUE)

# Done


# DEBUG
# Let's attempt to do the sheet saving with just a single combo


