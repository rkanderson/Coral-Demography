# Raw Data Directory

This folder is intentionally empty when you first clone the repository.  
To run the code yourself, you will need to download the raw data files from the following public Google Drive folder:

**Google Drive (Public):**  
https://drive.google.com/drive/folders/1favHx0D02mEY4kVfh4P8MtAxdwUYI09D?usp=drive_link

The Drive contains two directories:

- `Coral_Data_Raw_2013-2023`
- `Coral_Data_Raw_2024`

Follow the steps below to populate this `raw_data/` directory correctly.

---

## Instructions

### 1. Download the Data
Navigate into each of the two directories on Google Drive:

1. **`Coral_Data_Raw_2013-2023`**
2. **`Coral_Data_Raw_2024`**

Inside each folder you will see files following patterns like:

- `coral_raw_wide_2013-2023_v3.xlsx`
- `coral_raw_wide_2024_v2.xlsx`
- `data_raw_2024_sheets_v2.zip`
- etc.

### 2. Identify the Most Recent Version
For each dataset, **download only the file with the highest version number** (e.g., `_v3` is newer than `_v2`).

### 3. Remove Version Suffixes
After downloading, **remove the version suffix** (`_v#`) from the filename or directory name.

#### Examples
- `coral_raw_wide_2013-2023_v3.xlsx` →  
  **`coral_raw_wide_2013-2023.xlsx`**

- `coral_raw_wide_2024_v2.xlsx` →  
  **`coral_raw_wide_2024.xlsx`**

### 4. If the File is a ZIP Archive
Some data are provided as zipped directories, such as:

- `data_raw_2024_sheets_v2.zip`

For these:

1. Unzip the archive.
2. Rename the resulting directory to remove the version suffix.

Example:

- `data_raw_2024_sheets_v2.zip` → unzip → directory `data_raw_2024_sheets_v2/`  
  Rename to: **`data_raw_2024_sheets/`**

### 5. Place All Files in This Folder
Move all cleaned files and directories directly into this `raw_data/` directory so the project code can locate them.

---

## Summary of What You Should End Up With

Your `raw_data/` directory should contain unversioned raw data files, for example:

```
raw_data/
├── coral_raw_wide_2013-2023.xlsx
└── data_raw_2024_sheets/
```

No files should include `_v1`, `_v2`, `_v3`, etc.

---

If you have any issues or questions about obtaining the data, please open an issue on the repository.

