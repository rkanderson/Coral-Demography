import pandas as pd

r = pd.read_csv("../data_outputs/coral_tidy_dyn_2013-2025_FOR_COMPARISON.csv")
python = pd.read_csv("../data_outputs/coral_tidy_dyn_2013-2025.csv")



print("Same shape:", r.shape == python.shape)
print("Same columns:", r.columns.tolist() == python.columns.tolist())


# before doing a row-by-row comparison, ensure that the ordering is the same.
# order both dataframes by 'coral_number' first, and then by 'year'
r = r.sort_values(by=['coral_number', 'year']).reset_index(drop=True)
python = python.sort_values(by=['coral_number', 'year']).reset_index(drop=True)

# get the precise difference in the shapes/cols
# print("Shape difference:", r.shape[0] - python.shape[0], r.shape[1] - python.shape[1])
# print("Columns in R but not in Python:", set(r.columns) - set(python.columns))
# print("Columns in Python but not in R:", set(python.columns) - set(r.columns))


# Find any differences
# Normalize string columns to avoid dtype mismatches hiding their values in
# the comparison output. Preserve actual missing values as missing.
# string_columns = r.select_dtypes(include=['object', 'string']).columns.intersection(
# 	python.select_dtypes(include=['object', 'string']).columns
# )
# r[string_columns] = r[string_columns].astype('string')
# python[string_columns] = python[string_columns].astype('string')

r = r.set_index(["coral_number", "year"])
python = python.set_index(["coral_number", "year"])

# Report schema differences, then align rows and columns for compare().
print("Columns only in R:", sorted(set(r.columns) - set(python.columns)))
print("Columns only in Python:", sorted(set(python.columns) - set(r.columns)))

r, python = r.align(python, join="outer", axis=None)

comparison = r.compare(python, result_names=("r", "python")).reset_index()

print(comparison.to_string(index=False))
comparison.to_csv("../data_outputs/dynamics_comparison.csv", index=False)

# r = r.set_index(['coral_number', 'year'])
# python = python.set_index(['coral_number', 'year'])

# comparison = r.compare(python)

# print(comparison)
