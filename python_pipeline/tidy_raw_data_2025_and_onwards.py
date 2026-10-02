# The goal of this script is to tidy raw data from 2025 
# and onwards for further processing in the pipeline.

# In the spirit of the original R scripts, we will save our output
# to data_outputs/coral_data_tidy_2025_and_onwards_for_update.csv

# (But ultimately, we're going to want to make this more like a module 
# with a function that returns the tidied data frame.)

from pathlib import Path

import pandas as pd

YEARS = [2025]

script_dir = Path(__file__).resolve().parent

tidied_data_list = []

for year in YEARS:
    raw_data_path = script_dir / ".." / "data_raw" / f"coral_datasheets_{year}.xlsx"

    with pd.ExcelFile(raw_data_path) as workbook:
        sheet_names = list(dict.fromkeys(workbook.sheet_names))  # unique, original order

        for sheet_name in sheet_names:
            sheet_data = pd.read_excel(workbook, sheet_name=sheet_name, header=2)

            # Select the columns for this year's measurements.
            current_year = str(year)[-2:]
            expected_columns = [
                "Taxa", "X", "Y", "Z",
                f"L{current_year}", f"W{current_year}", f"H{current_year}", f"Notes{current_year}"
            ]
            sheet_data = sheet_data[expected_columns]

            wide = sheet_data.copy()
            wide["_row_id"] = range(len(wide))

            tidy = (
                pd.wide_to_long(
                    wide,
                    stubnames=["L", "W", "H", "Notes"],
                    i="_row_id",
                    j="year",
                    sep="",
                    suffix=r"\d+",
                )
                .reset_index()
                .rename(columns={"L": "length", "W": "width", "H": "height", "Notes": "note"})
            )

            tidy["year"] += 2000  # 24 -> 2024, 25 -> 2025
            tidy = tidy.drop(columns="_row_id")

            # Rename other columns to lowercase.
            tidy = tidy.rename(columns={"Taxa": "taxa", "X": "x", "Y": "y", "Z": "z"})

            # Sheet names should follow the pattern "Site_Hab_Tran".
            site, habitat, transect = sheet_name.split("_")
            tidy["site"] = site
            tidy["habitat"] = habitat
            tidy["transect"] = transect

            tidied_data_list.append(tidy)


# concatenate all the tidied data into a single DataFrame
final_tidied_data = pd.concat(tidied_data_list, ignore_index=True)

# add blank fields for note_extra and observer
# TODO at some point let's actually read in the observer and account for
# adding a note_extra field post survey (it will be an optional field)
final_tidied_data["note_extra"] = ""
final_tidied_data["observer"] = ""

# order the columns in exactly this manner:
final_tidied_data = final_tidied_data[
    ["site", "habitat", "transect", "taxa", "x", "y", "z", "year", "length", "width", "height", "observer", "note", "note_extra"]
]


# save the final tidied data to a CSV file
output_path = str(
    script_dir / ".." / "data_outputs" /
    f"coral_data_tidy_{YEARS[0]}_to_{YEARS[-1]}_for_update.csv"
)
final_tidied_data.to_csv(output_path, index=False)



