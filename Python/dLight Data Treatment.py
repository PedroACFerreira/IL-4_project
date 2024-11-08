import pandas as pd
import numpy as np
import os
import time

# Record start time to measure script execution time
start_time = time.time()

# Define different periods for averaging
Periods = [1, 5, 10, 60, 300, 600]
PeriodsStr = ["Average " + str(i) for i in Periods]  # Generate names for each period

# Timestamps used for processing
stamps = [0.006157, 0.687411, 0.979926, 0.957001, 0.446389, 0.105885, 0.07332, 0.857667]
counter = -1

# Define directory, list files in directory, and conditions to filter animals
directory = r''
dir_list = os.listdir(directory)
Animals = []
Conditions = ["Sal", "IL-4"]
MaxTime = 3600  # Maximum time to consider (in seconds)

# Loop through files and process any ending with 'df_F.csv'
for filename in dir_list:
    if filename.endswith('df_F.csv'):
        # Read data and calculate z-scores using the Robust Z-Score method
        df = pd.read_csv(directory + '\\' + filename, usecols=[0, 1], names=['Time', 'F/F'],
                         float_precision="round_trip")

        # Calculate median and MAD for z-score calculation
        median = df['F/F'].median()
        df["AB"] = (df['F/F'] - median).abs()
        MAD = df["AB"].median()

        # Calculate z-score and save back to the same column
        df["Z"] = 0.6745 * (df['F/F'] - median) / MAD
        df['F/F'] = df["Z"]
        df = df.drop(columns=['AB', "Z"])

        # Save updated file with '_z-score.csv' suffix
        df.to_csv(directory + '\\' + filename.strip(".csv") + "_z-score.csv", sep=',', encoding='utf-8', index=False,
                  header=False)

# List files again to look for processed '_z-score.csv' files
dir_list = os.listdir(directory)
for filename in dir_list:
    if filename.endswith('z-score.csv'):
        # Read processed z-score file
        df = pd.read_csv(directory + '\\' + filename, usecols=[0, 1], names=['Time', 'ΔF/F'],
                         float_precision="round_trip")
        counter += 1

        # Initialize variables for averaging by sub-groups within data
        a, b, tempc, c, realpos = 0, 0, [], [], 0

        # Divide data into sections based on row count and timestamps
        while a < df.shape[0] / 460:
            dfcrop = df["Time"].iloc[b:b + 470]
            pos = dfcrop.sub(1 + stamps[counter] + a).abs().values.argmin()
            realpos += pos
            tempc.append(realpos)
            a += 1
            b = realpos

        # Remove duplicates from tempc and add unique values to c
        [c.append(item) for item in tempc if item not in c]

        # Initialize columns for averaging
        for i in Periods:
            df["Average " + str(i)] = np.nan

        # Calculate averages based on position intervals within data
        for i in range(len(c)):
            if i == 0:
                df["Average 1"].iloc[c[i]] = df["ΔF/F"].iloc[0:(c[i] + 1)].astype('float64').mean()
            else:
                df["Average 1"].iloc[c[i]] = df["ΔF/F"].iloc[(c[i - 1] + 2):c[i]].astype('float64').mean()

        df = df[df['Average 1'].notna()]
        df = df.reset_index()

        # Calculate averages for each defined period
        for step in Periods[1:]:
            for i in range(1, df.shape[0] // step + 1):
                df["Average " + str(step)].iloc[i * step - 1] = df["Average 1"].iloc[((i - 1) * step):i * step].mean()

        # Limit data to MaxTime and save to Excel
        df = df.drop(columns=['ΔF/F', "index"])
        df.drop(df.index[MaxTime:], inplace=True)
        writer = pd.ExcelWriter(directory + '\\' + filename.strip(".csv") + "_treated.xlsx", engine="xlsxwriter")
        df.to_excel(writer, sheet_name="dF_F Averages", startrow=1, header=False, index=False)

        # Formatting in Excel file
        workbook = writer.book
        worksheet = writer.sheets["dF_F Averages"]
        (max_row, max_col) = df.shape
        column_settings = [{"header": column} for column in df.columns]
        worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})
        cell_format = workbook.add_format({'align': 'center'})
        cell_format.set_num_format(2)
        worksheet.set_column(0, max_col - 1, 0, cell_format)
        worksheet.autofit()

        # Prepare data for Graphpad
        df2 = df.drop(columns=['Time']).apply(lambda x: pd.Series(x.dropna().values))
        df2.to_excel(writer, sheet_name="Graphpad", startrow=1, header=False, index=False)
        worksheet2 = writer.sheets["Graphpad"]
        (max_row, max_col) = df2.shape
        column_settings = [{"header": column} for column in df2.columns]
        worksheet2.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})
        worksheet2.set_column(0, max_col - 1, 0, cell_format)
        worksheet2.autofit()
        writer.close()

# Prepare to collect averages from all Excel files
counter = -1
dir_list = os.listdir(directory)
Averages = [[] for _ in Periods]

# Gather averages from each treated Excel file
for filename in dir_list:
    if filename.endswith('.xlsx') and filename != "Averages All.xlsx":
        Animals.append(filename.strip(" - df_F_treated.xlsx"))

for filename in dir_list:
    if filename.endswith('.xlsx') and filename != "Averages All.xlsx":
        counter += 1
        df = pd.read_excel(directory + '\\' + filename, sheet_name="Graphpad")
        for i, period in enumerate(Periods):
            Averages[i].append(df["Average " + str(period)].dropna().values.tolist())

# Save combined averages to a new Excel file
writer = pd.ExcelWriter(directory + '\\' + "Averages All.xlsx", engine="xlsxwriter")
workbook = writer.book

for SheetNo, avg_data in enumerate(Averages):
    df = pd.DataFrame({str(i): pd.Series(avg) for i, avg in enumerate(avg_data)})
    df.columns = Animals

    # Organize columns by condition
    AnimalsOrder = []
    for cond in Conditions:
        cond_matches = [animal for animal in Animals if cond in animal]
        AnimalsOrder += cond_matches[::-1]

    df = df[AnimalsOrder]

    # Adjust table formatting for Excel
    df.insert(0, "Timestamps", [(i + 1) * Periods[SheetNo] / 86400 for i in range(df.shape[0])])
    df.to_excel(writer, sheet_name=PeriodsStr[SheetNo], startrow=1, header=False, index=False)
    worksheet = writer.sheets[PeriodsStr[SheetNo]]
    worksheet.add_table(0, 0, df.shape[0], df.shape[1] - 1, {"columns": [{"header": col} for col in df.columns]})
    cell_format.set_num_format(2)
    worksheet.set_column(0, df.shape[1] - 1, 0, cell_format)
    worksheet.autofit()

writer.close()

# Print execution time
execution_time = time.time() - start_time
print("Execution time:", execution_time)
