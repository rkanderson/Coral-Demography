# Data Cleaning Pipeline

**coral_cleaning_1_tidy_coral_data.Rmd**
- This script is designed to take specifically a raw coral data and clean it for analysis.
- It currently takes in a raw file provided by Hunter in 2024, which contains survey data
- extending as late as 2023. The file is messy and has inconsistencies.

**coral_cleaning_1.5_add_new_data.Rmd**
- Script that adds new (tidy) survey data to the existing dataset. Can be used to aggregate
- new survey results with the data that already exists.

**coral_cleaning_2_add_coral_dynamics.Rmd**
- This script processes the tidy dataset and determines which dynamics are present
- The dynamics are indicated in dummy variables

**coral_cleaning_3_widen_coral_data.Rmd**
- Transforms the data into a wider format that Hunter and Mohsen find easier to look at

**coral_cleaning_4_make_excel.Rmd**
- Creates an excel file with color coding

