# MCR LTER Coral Demography Data Cleaning

This repository contains scripts for cleaning and standardizing coral demography survey data from the Moorea Coral Reef (MCR) Long Term Ecological Research (LTER) site in Mo'orea, French Polynesia. The dataset spans surveys conducted between 2013 and 2024. These scripts focus on preparing the raw field data for downstream analysis by addressing inconsistencies, standardizing formats, and ensuring data integrity.

---

## Repository Structure and Files

Below is an overview of the repository contents and their organization:

```
project/
├── Coral Demography.Rproj         # RStudio project file
├── README.md                      # Project documentation (this file)
├── data_raw/                      # Raw input data
│   ├── coral_raw_wide_2023.xlsx   # 2013-2023 raw data (site tabs only valid)
│   ├── coral_raw_wide_2023_bad_and_duplicate_rows_removed.xlsx # Manually pre-cleaned input
│   └── data_raw_2024_sheets/      # 2024 survey data (individual Excel sheets)
├── data_outputs/                  # Cleaned and processed data files
│   ├── coral_clean_wide_human-friendly.xlsx  # Wide-format Excel (for manual inspection)
│   ├── coral_tidy_2024.csv        # Tidy cleaned data (no dynamics)
│   └── coral_tidy_2024_with_dynamics.csv # Tidy cleaned data with dynamic fields
├── explorations/                  # Exploratory R Markdown notebooks
│   └── exX.Y.Z-<title>.Rmd        # Hierarchically numbered exploration files
├── figures/                       # Output plots and graphics
└── scripts/                       # Cleaning pipeline scripts
    ├── coral_cleaning_1_tidy_coral_data.Rmd
    ├── coral_cleaning_1.3_create_coral_2024_tidy.R
    ├── coral_cleaning_1.5_add_new_data.Rmd
    ├── coral_cleaning_2_add_coral_dynamics.Rmd
    ├── coral_cleaning_3_widen_coral_data.Rmd
    └── coral_cleaning_4_make_excel.Rmd
```

### Top-Level Files

* **Coral Demography.Rproj** — R project file for organizing the RStudio project environment.
* **README.md** — This documentation file.

---

### Directories and Contents

#### `data_outputs/`

Directory containing all processed, cleaned, and analysis-ready data files. Key files include:

* **coral\_clean\_wide\_human-friendly.xlsx**
  Wide-format Excel file intended for easy human review. Includes color coding and site-specific tabs.

* **coral\_tidy\_2024.csv**
  Cleaned, tidy-format dataset containing all observations.

* **coral\_tidy\_2024\_with\_dynamics.csv**
  Same as `coral_tidy_2024.csv`, but includes dummy variables for each coral dynamic identified (details on dynamics provided below).

#### `data_raw/`

Directory containing raw data files prior to cleaning.

* **coral\_raw\_wide\_2023.xlsx**
  Raw survey data spanning 2013–2023. The "allsites" tab contains invalid data; only site-specific tabs should be used.

* **coral\_raw\_wide\_2023\_bad\_and\_duplicate\_rows\_removed.xlsx**
  Manually pre-cleaned version with erroneous and duplicate rows removed by Hunter and Ryan. This is the input file for the cleaning pipeline.

##### `data_raw/data_raw_2024_sheets/`

Subdirectory containing individual Excel sheets from the 2024 survey. These sheets are combined during the cleaning process.

#### `explorations/`

Contains exploratory R Markdown notebooks. File naming convention follows:

```
exX.Y.Z-<short_title>.Rmd
```

* The numbering allows hierarchical organization (e.g., `ex1.2.1-...` nests under `ex1.2-...`).
* The first number loosely indicates chronology.

#### `figures/`

Directory where output figures and visualizations are saved.

#### `scripts/`

Contains all R scripts for cleaning and processing the data. Current files include:

* **coral\_cleaning\_1\_tidy\_coral\_data.Rmd**
  Cleans and tidies raw 2013–2023 coral data.

* **coral\_cleaning\_1.3\_create\_coral\_2024\_tidy.R**
  Processes and tidies the separate 2024 survey sheets.

* **coral\_cleaning\_1.5\_add\_new\_data.Rmd**
  Merges 2024 data into the existing 2013–2023 dataset.

* **coral\_cleaning\_2\_add\_coral\_dynamics.Rmd**
  Adds dummy variables for coral dynamics.
  *\[Full documentation for the dynamics logic provided in a later section.]*

* **coral\_cleaning\_3\_widen\_coral\_data.Rmd**
  Converts the tidy data into a wide format for easier human interpretation.

* **coral\_cleaning\_4\_make\_excel.Rmd**
  Produces a polished Excel file with color coding and site-specific tabs.

---

## Cleaning Pipeline Overview

The data cleaning pipeline consists of a sequence of R scripts that should be run in the order indicated by their filenames (e.g. `coral_cleaning_1_...`, `coral_cleaning_1.3_...`, etc). Each script reads input data, processes it, and writes an updated file that serves as input for the next step. At present, this process requires running the files manually in order.

> **Note:**  
> An automated master script has not yet been implemented; for now, users should manually execute each script in sequence. When running the pipeline, always verify that each script is reading the correct output file produced by the previous step — this is how data flows between scripts. While not fully ideal, this approach was the most practical way to structure the pipeline given R’s environment management.

The files and their respective roles are described in detail above in the files section.

---

## Dynamics Logic

The cleaning pipeline extracts a set of coral "dynamics" — indicators of different biological or observational events — from both the coral size measurements and the free-text notes provided in the survey data. The following describes the logic used to define each dynamic field:

### Death (`dyn_death`)

* Set when:

  * The `note` or `note_extra` field contains `"d"` or `"dead"`, OR
  * The `length` field contains `"d"` or `"dead"`, OR
  * The coral was previously observed but suddenly vanishes from measurements (i.e. dimensions are NA, but it had been seen before, and was not already marked dead).
* Once a coral is marked dead, all subsequent years for that coral are considered dead.

### Recruitment (`dyn_recruitment`)

* Set when:

  * The `note` or `note_extra` contains `"r"`, `"(r)"`, `"r-fr"`, `"recruit"`, or strings starting with `"recruitment"`.
  * OR: When a coral is observed for the first time (i.e., newly encountered) with a largest dimension less than 6 cm. This logic automatically classifies small newly observed corals as recruits.

### Missing Data (`dyn_missing_data`)

* Applied when:

  * A newly observed coral (`first_instance=TRUE`) has a largest dimension ≥ 6 cm but is not marked explicitly as a recruit.
  * (Note: A former rule for assigning missing data due to gaps in observation has been deprecated as of October 2024.)

### Growth & Shrinkage (`dyn_growth`, `dyn_shrinkage`)

* Calculated from change in coral size measurements over time:

  * `growth_ratio = (current length + width + height) / (previous year length + width + height)`
  * Growth (`dyn_growth`) is set if ratio > 1; shrinkage (`dyn_shrinkage`) is set if ratio < 1.
  * If growth ratio is undefined (e.g., no prior year data), neither dynamic is applied.

### Fusion (`dyn_fusion`)

* Set when:

  * The `note` or `note_extra` fields include tokens like:

    * `"fuX"`, `"fusX"`, or `"fuX-ed"` (where X is a group ID of digits), OR
    * Strings containing `"fused"` or `"fusion"`.
* If group ID X is found, it is extracted into the field `fusion_group`.

### Fission (`dyn_fission`)

* Set when:

  * The `note` or `note_extra` fields include:

    * `"fiX"` or `"fisX"` (where X is a group ID of digits), OR
    * Strings containing `"fission"`.
* If group ID X is found, it is extracted into the field `fission_group`.

### Immigration (`dyn_immigration`)

* Set when:

  * The `note` or `note_extra` fields contain tokens starting with `"im"`.

### Emigration (`dyn_emigration`)

* Set when:

  * The `note` or `note_extra` fields contain tokens starting with `"em"`.

### Edge (`dyn_edge`)

* Set when:

  * The `note` or `note_extra` fields contain `"edge"` or match patterns like `"(fu-)?ed"`.

---

### Notes on Parsing

* Notes fields are tokenized by splitting on commas and semicolons, trimming whitespace, and converting to lowercase.
* Dynamics fields are all prefixed with `dyn_` for consistency and clarity.


