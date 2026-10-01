"""Tidy the raw 2024 coral observation workbooks."""

from pathlib import Path
import re
import unicodedata

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data_raw" / "data_raw_2024_sheets"
OUTPUT_FILE = PROJECT_ROOT / "data_outputs" / "coral_data_tidy_2024_for_update.csv"
TEST_MODE = False
TEST_WORKBOOK = "LTER1_BR_P01_P10_2024.xlsx"
WORKBOOK_PATTERN = re.compile(r"^LTER.*2024\.xlsx$")
RENAME_RULES = {
    re.compile(r"^l24$"): "l2024",
    re.compile(r"^w24$"): "w2024",
    re.compile(r"^h24$"): "h2024",
    re.compile(r"^(?:dynamics|dyn|dynamic)$"): "dynam",
}
OUTPUT_COLUMNS = [
    "site",
    "habitat",
    "transect",
    "taxa",
    "x",
    "y",
    "z",
    "year",
    "length",
    "width",
    "height",
    "observer",
    "note",
    "note_extra",
]


def clean_name(name):
    """Normalize a worksheet header to lowercase ASCII snake case."""
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
    """Normalize headers and suffix repeated names to make them unique."""
    cleaned = [clean_name(column) for column in columns]
    counts = {}
    unique = []
    for name in cleaned:
        counts[name] = counts.get(name, 0) + 1
        unique.append(name if counts[name] == 1 else f"{name}_{counts[name]}")
    return unique


def workbook_paths():
    """Return matching 2024 workbooks, or the single test workbook in test mode."""
    if TEST_MODE:
        return [RAW_DATA_DIR / TEST_WORKBOOK]
    return sorted(
        path
        for path in RAW_DATA_DIR.iterdir()
        if path.is_file() and WORKBOOK_PATTERN.fullmatch(path.name)
    )


def read_workbook(path):
    """Read a workbook's first sheet with row 2 as headers.

    Values are kept as strings, fully blank rows are omitted, and known header
    variants are renamed to the standard 2024 column names.
    """
    frame = pd.read_excel(
        path,
        sheet_name=0,
        header=1,
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    frame = frame.dropna(how="all")
    frame.columns = clean_names(frame.columns)

    renamed_columns = []
    for column in frame.columns:
        renamed_columns.append(
            next(
                (replacement for pattern, replacement in RENAME_RULES.items()
                 if pattern.fullmatch(column)),
                column,
            )
        )
    frame.columns = renamed_columns
    if frame.columns.has_duplicates:
        duplicates = frame.columns[frame.columns.duplicated()].tolist()
        raise ValueError(f"Header cleanup created duplicate columns in {path.name}: {duplicates}")
    return frame


def tidy_workbooks():
    """Validate, combine, and write the 2024 observations in tidy format.

    The output uses the established 14-column schema, with notes and dynamics
    combined into the ``note`` field.
    """
    if not RAW_DATA_DIR.is_dir():
        raise FileNotFoundError(f"Raw workbook directory not found: {RAW_DATA_DIR}")

    paths = workbook_paths()
    if not paths:
        raise FileNotFoundError(f"No 2024 workbooks found in {RAW_DATA_DIR}")
    missing_paths = [path for path in paths if not path.is_file()]
    if missing_paths:
        raise FileNotFoundError(f"Raw workbook not found: {missing_paths[0]}")

    data_raw_2024 = pd.concat(
        [read_workbook(path) for path in paths],
        ignore_index=True,
        sort=False,
    )
    required_columns = [
        "site", "hab", "tran", "taxa", "x", "y", "z",
        "l2024", "w2024", "h2024", "notes", "dynam",
    ]
    missing_columns = [
        column for column in required_columns if column not in data_raw_2024.columns
    ]
    if missing_columns:
        raise ValueError(f"Required 2024 columns missing: {missing_columns}")

    notes = data_raw_2024["notes"].fillna("NA")
    dynamics = data_raw_2024["dynam"].fillna("NA")
    notes_w_dynam = notes.astype(str) + ", " + dynamics.astype(str)

    data_2024_tidy = data_raw_2024[
        ["site", "hab", "tran", "taxa", "x", "y", "z", "l2024", "w2024", "h2024"]
    ].copy()
    data_2024_tidy = data_2024_tidy.rename(
        columns={
            "hab": "habitat",
            "tran": "transect",
            "l2024": "length",
            "w2024": "width",
            "h2024": "height",
        }
    )
    data_2024_tidy["year"] = 2024
    data_2024_tidy["observer"] = "TBD"
    data_2024_tidy["note"] = notes_w_dynam
    data_2024_tidy["note_extra"] = pd.NA
    data_2024_tidy = data_2024_tidy.loc[:, OUTPUT_COLUMNS]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data_2024_tidy.to_csv(OUTPUT_FILE, index=False, na_rep="")
    print(f"Wrote {len(data_2024_tidy):,} rows to {OUTPUT_FILE}")


if __name__ == "__main__":
    tidy_workbooks()
