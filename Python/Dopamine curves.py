import os
import pandas as pd
import numpy as np
import time

# Start timer for execution time measurement
start_time = time.time()

# Define directory where data files are stored
directory = r'C:\Users\pedro\OneDrive\dLight\OFT Results'
# List all files in the directory
dir_list = os.listdir(directory)

# List to store animal identifiers extracted from filenames
Animals = []
# Loop through files to collect animal names (exclude "Dopamine Curves.xlsx")
for filename in dir_list:
    if filename.endswith('.xlsx') and filename != "Dopamine Curves.xlsx":
        Animals.append(filename.strip(".xlsx"))

# Define conditions for grouping animals
Conditions = ["Sal", "IL-4"]
# Define maximum time threshold (seconds)
MaxTime = 3600

# Initialize list to store dopamine data for each animal
final = []

# Loop through each file in the directory
for filename in dir_list:
    if filename.endswith('.xlsx') and filename != "Dopamine Curves.xlsx":

        # Temporary lists to store movement and dopamine data
        mov = []
        mov_parsed = []
        dop = []
        counter = 0

        # Read the specific columns from each Excel file
        df = pd.read_excel(directory + '\\' + filename, "dF_F Aligned", usecols="B:D")

        # Detect movement by checking for non-zero values in the "Distance" column
        for idx, i in df["Distance"].items():
            if i != 0 and counter >= 5:
                try:
                    # If the next few rows have non-zero distances, add this index to movement
                    if df._get_value(idx, 'Distance') + df._get_value(idx + 1, 'Distance') + df._get_value(idx + 2,
                                                                                                           'Distance') != 0:
                        mov.append(idx)
                    counter = 0
                except:
                    counter = 0
            elif i != 0 and counter < 5:
                counter = 0
            elif i == 0:
                counter += 1

        # Filter out close movements to capture distinct movement events
        for i in range(0, len(mov) - 1):
            if mov[i] + 5 < mov[i + 1] and mov[i] > 60:
                mov_parsed.append(mov[i])

        # Collect dopamine data in a +/-5 frame window around each movement
        for loc in mov_parsed:
            temp = [loc]
            for i in range(-5, 6):
                temp.append(df._get_value(loc + i, 'dF/F'))
            dop.append(temp)

        # Append dopamine data for each animal to final list
        final.append(dop)

# Initialize lists to store average dopamine values
averages = [Animals]
temp = []

# Calculate average dopamine levels for each movement event
for i in range(len(final)):
    for a in final[i]:
        temp.append(sum(a[1:]) / len(a[1:]))  # Average dopamine value around each movement event
    averages.append(temp)
    temp = []

# Create Excel file to store dopamine data
writer = pd.ExcelWriter(directory + '\\' + "Dopamine Curves.xlsx", engine="xlsxwriter")
df2 = pd.DataFrame()

# Save each animal's dopamine data to a separate sheet in the Excel file
for i in range(len(final)):
    df = pd.DataFrame(final[i])
    df = df.transpose()
    df.columns = [str(round(x, 0)) for x in df.iloc[0]]
    df = df.drop(0)
    df2[Animals[i]] = df.mean(axis=1)  # Add animal averages to final dataframe

    # Write data to Excel
    df.to_excel(writer, sheet_name=Animals[i], startrow=1, header=False, index=False)

    # Format Excel sheet
    workbook = writer.book
    worksheet = writer.sheets[Animals[i]]
    (max_row, max_col) = df.shape
    column_settings = [{"header": column} for column in df.columns]
    worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})
    cell_format = workbook.add_format({'align': 'center'})
    cell_format.set_num_format(2)
    worksheet.set_column(0, max_col - 1, 0, cell_format)
    worksheet.autofit()

# Organize final averages data by conditions
df = df2
df.columns = Animals
AnimalsOrder = []

# Group animals by conditions and reorder columns accordingly
for cond in range(len(Conditions)):
    globals()[f'Cond{cond}'] = 0
    for animal in range(len(Animals)):
        if Conditions[abs(cond - len(Conditions)) - 1] in Animals[abs(animal - len(Animals)) - 1]:
            AnimalsOrder.insert(0, Animals[abs(animal - len(Animals)) - 1])
            globals()[f'Cond{cond}'] += 1

# Reorder the dataframe columns based on condition grouping
df = df[AnimalsOrder]

# Calculate padding to align columns by condition
CondsNo = [globals()[f'Cond{cond}'] for cond in range(len(Conditions))]
Max = max(CondsNo)
CondsPad = [abs(CondsNo[i] - Max) for i in range(len(Conditions))]

# Insert padding columns for alignment
for (i, a) in zip(CondsPad, range(len(CondsPad))):
    if i > 0:
        for col in range(i):
            df.insert(globals()[f'Cond{a}'], "", ['' for i in range(df.shape[0])], allow_duplicates=True)

# Save final averages data to Excel
df.to_excel(writer, sheet_name="Averages", startrow=1, header=False, index=False)
workbook = writer.book
worksheet = writer.sheets["Averages"]
(max_row, max_col) = df.shape
column_settings = [{"header": column} for column in df.columns]
worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})
cell_format = workbook.add_format({'align': 'center'})
cell_format.set_num_format(2)
worksheet.set_column(0, max_col - 1, 0, cell_format)
worksheet.autofit()

# Close the Excel writer
writer.close()

# Calculate and print execution time
end_time = time.time()
execution_time = end_time - start_time
print("Execution time:", execution_time)
