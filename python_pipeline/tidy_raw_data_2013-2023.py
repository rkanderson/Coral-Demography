"""Tidy the raw 2013-2023 coral workbook, matching the Rmd pipeline."""

from pathlib import Path
import re
import unicodedata

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_FILE = PROJECT_ROOT / "data_raw" / "coral_raw_wide_2013-2023.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "data_outputs" / "coral_tidy_2013-2023.csv"
# Mirrors the Rmd's readxl range, which reads at most the first 100 columns.
COLUMN_LIMIT = 100
SHEET_PATTERN = re.compile(r"^LTER[0-9][A-Z]{2}$")

# Keep fields in the same selection order as the Rmd before pivoting.
METADATA_COLUMNS = ["site", "habitat", "transect", "taxa", "x", "y", "z"]
MEASURE_PATTERNS = [
    re.compile(r"^l[0-9]{4}$"),
    re.compile(r"^w[0-9]{4}$"),
    re.compile(r"^h[0-9]{4}$"),
    re.compile(r"^obs[0-9]{4}$"),
    re.compile(r"^note[0-9]{4}(?:extra)?$"),
]
OUTPUT_MEASURES = {
    "l": "length",
    "w": "width",
    "h": "height",
    "obs": "observer",
    "note": "note",
    "note_extra": "note_extra",
}


def clean_name(name):
    """Approximate janitor::clean_names(..., case = 'snake') for headers."""
    name = unicodedata.normalize("NFKD", str(name))
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    if not name:
        return "x"
    if name[0].isdigit():
        return f"x_{name}"
    return name


def clean_names(columns):
    """Clean headers and make duplicate names unique, as janitor does."""
    cleaned = [clean_name(column) for column in columns]
    counts = {}
    unique = []
    for name in cleaned:
        counts[name] = counts.get(name, 0) + 1
        unique.append(name if counts[name] == 1 else f"{name}_{counts[name]}")
    return unique


def select_columns(columns):
    selected = list(METADATA_COLUMNS)
    selected.extend(
        column
        for pattern in MEASURE_PATTERNS
        for column in columns
        if pattern.fullmatch(column) and column not in selected
    )
    missing = [column for column in METADATA_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"Required metadata columns missing: {missing}")
    return selected


def normalize_value(value):
    """Apply stringr::str_replace(value, 'NA', 'Na') to one cell."""
    if pd.isna(value):
        return value
    return re.sub("NA", "Na", str(value), count=1)


def tidy_workbook():
    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(f"Raw workbook not found: {RAW_DATA_FILE}")

    workbook = pd.ExcelFile(RAW_DATA_FILE)
    habitat_sheets = [
        sheet for sheet in workbook.sheet_names if SHEET_PATTERN.fullmatch(sheet)
    ]
    if not habitat_sheets:
        raise ValueError("No workbook sheets matched the required LTER habitat pattern")

    cleaned_sheets = []
    for sheet in habitat_sheets:
        # Read as text so values like UK and Na remain literal, not inferred numbers/NA.
        frame = pd.read_excel(
            workbook,
            sheet_name=sheet,
            dtype=str,
            keep_default_na=False,
            na_values=[""],
        )
        frame = frame.iloc[:, :COLUMN_LIMIT]
        # The Rmd cleans names to snake case, then removes every underscore.
        frame.columns = [
            name.replace("_", "") for name in clean_names(frame.columns)
        ]
        if frame.columns.has_duplicates:
            duplicates = frame.columns[frame.columns.duplicated()].tolist()
            raise ValueError(
                f"Header cleanup created duplicate columns in sheet {sheet}: "
                f"{duplicates}"
            )
        cleaned_sheets.append(frame)

    coral_df_raw = pd.concat(cleaned_sheets, ignore_index=True, sort=False)
    selected = select_columns(coral_df_raw.columns)
    coral_df = coral_df_raw.loc[:, selected].copy()

    coral_df = coral_df.rename(
        columns={
            column: re.sub(r"^note([0-9]{4})extra$", r"note_extra\1", column)
            for column in coral_df.columns
            if re.fullmatch(r"note[0-9]{4}extra", column)
        }
    )

    # Gather year-specific measurements into key/value rows, then recover year
    # and measure names to match pivot_longer() followed by pivot_wider().
    measure_columns = [
        column
        for column in coral_df.columns
        if re.fullmatch(
            r"(?:l|w|h|obs|note)[0-9]{4}|note_extra[0-9]{4}", column
        )
    ]
    if not measure_columns:
        raise ValueError("No year-coded measurement columns were found")

    long_df = coral_df.reset_index(names="_source_row").melt(
        id_vars=["_source_row", *METADATA_COLUMNS],
        value_vars=measure_columns,
        var_name="key",
        value_name="value",
    )
    measure_order = {column: order for order, column in enumerate(measure_columns)}
    long_df["_measure_order"] = long_df["key"].map(measure_order)
    long_df = long_df.sort_values(
        ["_source_row", "_measure_order"], kind="stable"
    )
    long_df["year"] = long_df["key"].str.extract(r"([0-9]{4})", expand=False)
    long_df["key"] = long_df["key"].str.replace(
        r"_*[0-9]{4}", "", n=1, regex=True
    )

    index_columns = [*METADATA_COLUMNS, "year"]
    cell_columns = [*index_columns, "key"]
    # Some source rows repeat exactly; collapse only identical cells and reject
    # conflicting values rather than silently choosing one.
    duplicate_values = long_df.groupby(cell_columns, dropna=False)["value"]
    conflicting_cells = duplicate_values.nunique(dropna=False)
    if conflicting_cells.gt(1).any():
        raise ValueError("Repeated coral/year/measure cells contain different values")
    long_df = long_df.drop_duplicates(subset=cell_columns, keep="first")
    row_order = long_df[index_columns].drop_duplicates()
    wide_df = long_df.pivot(
        index=index_columns,
        columns="key",
        values="value",
    ).reindex(pd.MultiIndex.from_frame(row_order))
    wide_df = wide_df.reindex(columns=list(OUTPUT_MEASURES))
    wide_df.columns.name = None
    coral_df_tidy = wide_df.reset_index().rename(columns=OUTPUT_MEASURES)

    coral_df_tidy["habitat"] = coral_df_tidy["habitat"].str.upper()
    coral_df_tidy["taxa"] = coral_df_tidy["taxa"].str.title()
    coral_df_tidy["observer"] = coral_df_tidy["observer"].str.upper()
    coral_df_tidy["site"] = coral_df_tidy["site"].str.upper()
    coral_df_tidy["transect"] = coral_df_tidy["transect"].str.upper()
    # Match the Rmd's global str_replace: replace only the first "NA" per cell.
    coral_df_tidy = coral_df_tidy.apply(lambda column: column.map(normalize_value))
    coral_df_tidy["transect"] = coral_df_tidy["transect"].str.replace(
        r"^([PT])([0-9])(_.*)?$",
        lambda match: f"{match.group(1)}0{match.group(2)}"
        f"{match.group(3) or ''}",
        regex=True,
    )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    coral_df_tidy.to_csv(OUTPUT_FILE, index=False, na_rep="")
    print(f"Wrote {len(coral_df_tidy):,} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    tidy_workbook()