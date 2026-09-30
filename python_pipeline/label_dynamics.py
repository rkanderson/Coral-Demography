
"""
Extract coral dynamics from tidy coral observation data.

This script is a Python translation of coral dynamics parsing originally
implemented in coral_tidy_2024_for_dynamics.Rmd.

The parsing logic is intentionally kept close to the original R code.
"""

from pathlib import Path
import re

import pandas as pd


# =============================================================================
# CONFIGURATION
# =============================================================================

# Final year of the dataset.
# Change this when working with a different year's dataset.
YEAR = 2025

# First year of the study.
FIRST_YEAR = 2013

# Project root directory.
# Assumes this script lives in the root project directory.
PROJECT_ROOT = Path(__file__).resolve().parent

# Input/output directories.
DATA_OUTPUTS = Path("../data_outputs")

# Input and output files.
INPUT_FILE = DATA_OUTPUTS / f"coral_tidy_{FIRST_YEAR}-{YEAR}.csv"
OUTPUT_FILE = DATA_OUTPUTS / f"coral_tidy_dyn_{FIRST_YEAR}-{YEAR}.csv"


# =============================================================================
# SETUP
# =============================================================================

# Load tidy coral dataset.
coral_df_tidy = pd.read_csv(INPUT_FILE)


# Create coral_number.
#
# This uniquely identifies a coral by combining:
# site, habitat, transect, taxa, x, y, z
#
# This is equivalent to:
# paste0(site, "_", habitat, "_", transect, "_",
#        taxa, "_", x, "_", y, "_", z)
def format_coordinate(value):
    """Drop the decimal part from coordinates that are whole numbers."""
    if pd.isna(value):
        return str(value)
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return str(value)


coral_df_tidy["coral_number"] = (
    coral_df_tidy["site"].astype(str)
    + "_"
    + coral_df_tidy["habitat"].astype(str)
    + "_"
    + coral_df_tidy["transect"].astype(str)
    + "_"
    + coral_df_tidy["taxa"].astype(str)
    + "_"
    + coral_df_tidy["x"].map(format_coordinate)
    + "_"
    + coral_df_tidy["y"].map(format_coordinate)
    + "_"
    + coral_df_tidy["z"].map(format_coordinate)
)


# Debugging: identify duplicate coral/year observations.
coral_df_debug = (
    coral_df_tidy
    .groupby(["coral_number", "year"])
    .size()
    .reset_index(name="count")
)

duplicates = coral_df_debug[coral_df_debug["count"] > 1]

if not duplicates.empty:
    print("WARNING: Duplicate coral/year observations found:")
    print(duplicates)


# =============================================================================
# AGGREGATING AND TOKENIZING NOTES
# =============================================================================

def extract_notes(note, note_extra):
    """
    Reproduce the R note-tokenization logic.

    R:
        strsplit(tolower(.x), "[,;]")
        strsplit(tolower(.y), "[,;]")
        c(...)
        str_trim(...)
    """

    # Match R's general handling of missing values reasonably closely.
    note = "" if pd.isna(note) else str(note)
    note_extra = "" if pd.isna(note_extra) else str(note_extra)

    notes = re.split(r"[,;]", note.lower())
    notes_extra = re.split(r"[,;]", note_extra.lower())

    return [x.strip() for x in notes + notes_extra]


coral_df_tidy["notes_extracted"] = coral_df_tidy.apply(
    lambda row: extract_notes(row["note"], row["note_extra"]),
    axis=1,
)


# =============================================================================
# FIRST INSTANCE & CORAL ENCOUNTERED
# =============================================================================

# Convert dimensions to numeric.
#
# R:
# suppressWarnings(as.numeric(length))
#
# pandas.to_numeric(..., errors="coerce") gives the equivalent behavior
# for values such as "Na", "Dead", "D", etc.
length_numeric = pd.to_numeric(coral_df_tidy["length"], errors="coerce")
width_numeric = pd.to_numeric(coral_df_tidy["width"], errors="coerce")
height_numeric = pd.to_numeric(coral_df_tidy["height"], errors="coerce")


# Keep only observations with numeric data for all three dimensions.
numeric_only = coral_df_tidy[
    length_numeric.notna()
    & width_numeric.notna()
    & height_numeric.notna()
].copy()


# Get the first instance year for each coral.
#
# Equivalent to:
# group_by(coral_number) %>%
# summarize(first_instance_year = min(year))
first_instance_years = (
    numeric_only
    .groupby("coral_number")["year"]
    .min()
    .to_dict()
)


# Initialize empty columns.
coral_df_tidy["first_instance"] = False
coral_df_tidy["coral_encountered"] = False


# Reproduce the R loop:
#
# first_instance = TRUE if observation year == first instance year
# coral_encountered = TRUE if observation year >= first instance year
for i in coral_df_tidy.index:

    coral_number = str(coral_df_tidy.at[i, "coral_number"])

    # Some corals don't have a first instance year.
    if coral_number not in first_instance_years:
        continue

    first_instance_year = first_instance_years[coral_number]
    year = coral_df_tidy.at[i, "year"]

    coral_df_tidy.at[i, "first_instance"] = (
        year == first_instance_year
    )

    coral_df_tidy.at[i, "coral_encountered"] = (
        year >= first_instance_year
    )


# =============================================================================
# DEATH
# =============================================================================

# Initialize death column.
coral_df_tidy["death"] = 0


for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    # If notes contain "d" or "dead", mark death.
    if "d" in notes or "dead" in notes:
        coral_df_tidy.at[i, "death"] = 1

    # Some deaths are indicated directly in the length field.
    length_value = coral_df_tidy.at[i, "length"]

    if not pd.isna(length_value):
        length_value = str(length_value).lower()

        if length_value == "d" or length_value == "dead":
            coral_df_tidy.at[i, "death"] = 1


# =============================================================================
# DEATH YEARS & CORAL DIED
# =============================================================================

death_years = (
    coral_df_tidy[coral_df_tidy["death"] == 1]
    .groupby("coral_number")["year"]
    .min()
    .to_dict()
)


coral_df_tidy["coral_died"] = False


for i in coral_df_tidy.index:

    coral_number = str(coral_df_tidy.at[i, "coral_number"])

    # Corals without a death year remain False.
    if coral_number not in death_years:
        continue

    death_year = death_years[coral_number]

    coral_df_tidy.at[i, "coral_died"] = (
        coral_df_tidy.at[i, "year"] >= death_year
    )


# =============================================================================
# RECRUITMENT — EXPLICITLY NOTED
# =============================================================================

coral_df_tidy["recruitment"] = 0


for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        if pd.isna(note):
            continue

        if (
            note == "r"
            or note == "(r)"
            or note == "r-fr"
            or note == "recruit"
            or re.search(r"^recruitment", note)
        ):
            coral_df_tidy.at[i, "recruitment"] = 1


# =============================================================================
# RECRUITMENT — IMPLICIT & MISSING DATA
# =============================================================================

coral_df_tidy["missing_data"] = 0


for i in coral_df_tidy.index:

    coral_length = pd.to_numeric(
        coral_df_tidy.at[i, "length"],
        errors="coerce",
    )

    coral_width = pd.to_numeric(
        coral_df_tidy.at[i, "width"],
        errors="coerce",
    )

    coral_height = pd.to_numeric(
        coral_df_tidy.at[i, "height"],
        errors="coerce",
    )

    # DEBUG
    # trigger breakpoint on following coral: LTER1_BR_P01_Acr_3.3_65_50
    # if coral_df_tidy.at[i, "coral_number"] == "LTER1_BR_P01_Acr_3.3_65_50":
    #     breakpoint()

    if coral_df_tidy.at[i, "first_instance"] == True:

        # If any dimension is non-numeric, skip.
        if (
            pd.isna(coral_length)
            or pd.isna(coral_width)
            or pd.isna(coral_height)
        ):
            continue

        # Get largest dimension.
        largest_dim = max(
            coral_length,
            coral_width,
            coral_height,
        )

        if largest_dim < 6:

            coral_df_tidy.at[i, "recruitment"] = 1

        elif coral_df_tidy.at[i, "year"] > coral_df_tidy["year"].min():

            coral_df_tidy.at[i, "missing_data"] = 1


# =============================================================================
# EXPLICITLY NOTED MISSING DATA
# =============================================================================

for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        if pd.isna(note):
            continue

        if note == "unsampled" or note == "not sampled":
            coral_df_tidy.at[i, "missing_data"] = 1


# =============================================================================
# VANISHING CORALS — ANOTHER TYPE OF DEATH
# =============================================================================

# The original R code explicitly sorts by year before this loop.
coral_df_tidy = coral_df_tidy.sort_values("year").reset_index(drop=True)


# Keep track of corals that have already been marked as vanished.
vanished_corals = set()


for i in coral_df_tidy.index:

    coral_number = str(coral_df_tidy.at[i, "coral_number"])

    # Skip if this coral has already been marked as vanished.
    if coral_number in vanished_corals:
        continue

    # No coral can vanish in the first year of the study.
    if coral_df_tidy.at[i, "year"] == FIRST_YEAR:
        continue

    # Get numeric dimensions.
    coral_length = pd.to_numeric(
        coral_df_tidy.at[i, "length"],
        errors="coerce",
    )

    coral_width = pd.to_numeric(
        coral_df_tidy.at[i, "width"],
        errors="coerce",
    )

    coral_height = pd.to_numeric(
        coral_df_tidy.at[i, "height"],
        errors="coerce",
    )

    # Check whether explicitly noted as unsampled.
    noted_as_unsampled = False

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        if pd.isna(note):
            continue

        if note == "unsampled" or note == "not sampled":
            noted_as_unsampled = True
            break

    # Vanishing logic:
    #
    # coral has been encountered
    # AND has not already been confirmed dead
    # AND all dimensions are non-numeric
    # AND was not explicitly unsampled
    #
    # => mark death.
    if (
        coral_df_tidy.at[i, "coral_encountered"]
        and not coral_df_tidy.at[i, "coral_died"]
        and pd.isna(coral_length)
        and pd.isna(coral_width)
        and pd.isna(coral_height)
        and not noted_as_unsampled
    ):

        coral_df_tidy.at[i, "death"] = 1

        vanished_corals.add(coral_number)


# =============================================================================
# FUSION
# =============================================================================

coral_df_tidy["fusion"] = 0
coral_df_tidy["fusion_group"] = pd.NA


for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        # Equivalent to:
        # ^fu[0-9]*$
        # ^fus[0-9]*$
        # ^fu[0-9]*-ed$
        if (
            re.search(r"^fu[0-9]*$", note)
            or re.search(r"^fus[0-9]*$", note)
            or re.search(r"^fu[0-9]*-ed$", note)
        ):

            coral_df_tidy.at[i, "fusion"] = 1

            # Equivalent to:
            # str_extract(note, "^fus?([0-9]*)(-ed)?$", group = 1)
            match = re.search(
                r"^fus?([0-9]*)(-ed)?$",
                note,
            )

            if match:
                fusion_group = match.group(1)

                # as.numeric("") becomes NA in R.
                if fusion_group == "":
                    coral_df_tidy.at[i, "fusion_group"] = pd.NA
                else:
                    coral_df_tidy.at[i, "fusion_group"] = int(
                        fusion_group
                    )

        elif "fused" in note or "fusion" in note:

            # Don't overwrite an existing fusion group.
            if coral_df_tidy.at[i, "fusion"] == 1:
                continue

            coral_df_tidy.at[i, "fusion"] = 1
            coral_df_tidy.at[i, "fusion_group"] = pd.NA


# =============================================================================
# FISSION
# =============================================================================

coral_df_tidy["fission"] = 0
coral_df_tidy["fission_group"] = pd.NA


for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        # Equivalent to:
        # ^fis?[0-9]*$
        if re.search(r"^fis?[0-9]*$", note):

            coral_df_tidy.at[i, "fission"] = 1

            # Extract group number.
            match = re.search(
                r"^fis?([0-9]*)$",
                note,
            )

            if match:
                fission_group = match.group(1)

                # as.numeric("") becomes NA in R.
                if fission_group == "":
                    coral_df_tidy.at[i, "fission_group"] = pd.NA
                else:
                    coral_df_tidy.at[i, "fission_group"] = int(
                        fission_group
                    )

        elif "fission" in note:

            # Don't overwrite an existing fission group.
            if coral_df_tidy.at[i, "fission"] == 1:
                continue

            coral_df_tidy.at[i, "fission"] = 1
            coral_df_tidy.at[i, "fission_group"] = pd.NA


# =============================================================================
# GROWTH & SHRINKAGE
# =============================================================================

# Compute numeric dimensions.
coral_df_tidy["_length_numeric"] = pd.to_numeric(
    coral_df_tidy["length"],
    errors="coerce",
)

coral_df_tidy["_width_numeric"] = pd.to_numeric(
    coral_df_tidy["width"],
    errors="coerce",
)

coral_df_tidy["_height_numeric"] = pd.to_numeric(
    coral_df_tidy["height"],
    errors="coerce",
)


# Sum dimensions.
coral_df_tidy["_sum_dims"] = (
    coral_df_tidy["_length_numeric"]
    + coral_df_tidy["_width_numeric"]
    + coral_df_tidy["_height_numeric"]
)


# Previous year's sum of dimensions.
#
# R:
# group_by(coral_number) %>%
# mutate(prev_sum_dims = lag(sum_dims))
#
# Sorting by year is important because lag() depends on row order.
coral_df_tidy = coral_df_tidy.sort_values(
    ["coral_number", "year"]
).reset_index(drop=True)


coral_df_tidy["_prev_sum_dims"] = (
    coral_df_tidy
    .groupby("coral_number")["_sum_dims"]
    .shift(1)
)


# Growth ratio.
coral_df_tidy["growth_ratio"] = (
    coral_df_tidy["_sum_dims"]
    / coral_df_tidy["_prev_sum_dims"]
)


# Initialize growth/shrinkage.
coral_df_tidy["growth"] = 0
coral_df_tidy["shrinkage"] = 0


for i in coral_df_tidy.index:

    growth_ratio = coral_df_tidy.at[i, "growth_ratio"]

    if pd.isna(growth_ratio):
        continue

    if growth_ratio > 1:
        coral_df_tidy.at[i, "growth"] = 1

    elif growth_ratio < 1:
        coral_df_tidy.at[i, "shrinkage"] = 1


# Remove temporary calculation fields.
coral_df_tidy = coral_df_tidy.drop(
    columns=[
        "_length_numeric",
        "_width_numeric",
        "_height_numeric",
        "_sum_dims",
        "_prev_sum_dims",
    ]
)


# =============================================================================
# IMMIGRATION & EMIGRATION
# =============================================================================

coral_df_tidy["immigration"] = 0
coral_df_tidy["emigration"] = 0


for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        if re.search(r"^im", note):
            coral_df_tidy.at[i, "immigration"] = 1

        if re.search(r"^em", note):
            coral_df_tidy.at[i, "emigration"] = 1


# =============================================================================
# EDGE
# =============================================================================

coral_df_tidy["edge"] = 0


for i in coral_df_tidy.index:

    notes = coral_df_tidy.at[i, "notes_extracted"]

    for note in notes:

        if (
            "edge" in note
            or re.search(r"^(fu[0-9]*-)?ed$", note)
        ):
            coral_df_tidy.at[i, "edge"] = 1


# =============================================================================
# RENAME DYNAMIC FIELDS
# =============================================================================

coral_df_tidy = coral_df_tidy.rename(
    columns={
        "growth": "dyn_growth",
        "shrinkage": "dyn_shrinkage",
        "death": "dyn_death",
        "recruitment": "dyn_recruitment",
        "fission": "dyn_fission",
        "fusion": "dyn_fusion",
        "edge": "dyn_edge",
        "immigration": "dyn_immigration",
        "emigration": "dyn_emigration",
        "missing_data": "dyn_missing_data",
    }
)


# =============================================================================
# STORAGE
# =============================================================================

# Remove temporary/exploratory fields.
coral_df_tidy = coral_df_tidy.drop(
    columns=[
        "notes_extracted",
        "first_instance",
        "coral_encountered",
        "coral_died",
    ]
)


# Write final CSV.
coral_df_tidy.to_csv(
    OUTPUT_FILE,
    index=False,
)


print(f"Finished processing coral dynamics.")
print(f"Input:  {INPUT_FILE}")
print(f"Output: {OUTPUT_FILE}")
