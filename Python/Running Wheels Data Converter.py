import sys
from os import getcwd, path, remove, environ, mkdir, listdir
from datetime import datetime
from tkinter import Tk, Frame, Label, Button, BOTTOM, Checkbutton, IntVar
from tkinter import filedialog
from glob import glob
from shutil import copyfile
from time import sleep, localtime
import pandas as pd
from traceback import format_exc
from importlib import util

if '_PYIBoot_SPLASH' in environ and util.find_spec("pyi_splash"):
    import pyi_splash
    pyi_splash.update_text('UI Loaded ...')
    pyi_splash.close()
    print('Splash screen closed.')

main = Tk()
main.title("RW Magic Converter by NCBL")
main.geometry("800x290")
main.iconbitmap(sys.executable)

root = Frame(main)
root.pack(side="top", expand=True, fill="both")
tdays = 0
days = 0
def browsefunc(x):
    if x==2:
        filename = filedialog.askdirectory()
        labels[2] = filename
    elif x==1:
        filename = filedialog.askopenfilename()
        labels[1] = filename
    else:
        filename = filedialog.askopenfilename()
        labels[0] = filename
    buttons[x].config(text=filename)

def getdata(in1,in2,out):

    if out.replace("/","\\") == path.join(path.join(environ['USERPROFILE']), 'Desktop'):
        newdir = path.join(path.join(environ['USERPROFILE']), 'Desktop') + "/RW Converted"
        if not path.isdir(newdir):
            mkdir(newdir)
        out = newdir.replace("/","\\")

    try:
        promptlabel = Label(main)
        promptlabel.pack(expand=True)
        main.geometry("200x50")

        print("Parsing...")
        promptlabel.config(text="Parsing...")
        main.update()
        parse_file(in1,in2)
        print("Writing with lines...")
        promptlabel.config(text="Writing with lines...")
        main.update()
        write_cages(out)
        print("Writing in a column...")
        promptlabel.config(text="Writing in a column...")
        main.update()
        write_cages_column(out)
        print("Joining files...")
        promptlabel.config(text="Joined files")
        main.update()
        join_files(out,check2.get(),check4.get())
        print("Adjusting for schedule...")
        promptlabel.config(text="Adjusting for schedule...")
        main.update()
        adjust_days(out,check.get(),check2.get(),check3.get())
        print("Finished and wrote to files!")
        promptlabel.config(text="Finished and wrote to files!")
        main.update()
        sleep(1)
        promptlabel.config(text="Have a nice day! \nBy NCBL")
        main.update()
        sleep(1)
        main.destroy()

    except Exception:

        err = format_exc()
        main.geometry("600x400")
        main.resizable(True, True)
        print(err)
        promptlabel.config(text=err)
        close = Button(main, text="Close", command=lambda: main.destroy())
        close.pack(side = BOTTOM)
        close.pack(expand=True)
        copy = Button(main, text="Copy to clipboard", command=lambda: [main.clipboard_clear(),main.clipboard_append(err),main.update()])
        copy.pack(side = BOTTOM)
        copy.pack(expand=True)
        main.update()

# number of seconds of time bin
TIME_BIN = 360

cages = {}
time_format = "%Y-%m-%d %H:%M:%S:%f"


def get_timestamp(line):
    # convert string to actual datetime
    time = datetime.strptime(line.split("\"")[1], time_format)
    return time.timestamp()

def parse_file(in1,in2):
    content = []

    copyfile(in1, getcwd() + "/Temp1")
    ins = ["/Temp1"]
    if in2 != "":
        print("Both Files were opened...")
        copyfile(in2, getcwd() + "/Temp2")
        ins.append("/Temp2")

    counter = 0


    for i in ins:
        try:
            with open(getcwd() + i) as f:
                content = f.readlines()
        except:
            print("There is no file with the given name!")
            return

        if len(content) == 0:
            print("File is empty.")

        # structure of data will be as follows, in which each
        # array will represent a line for the CSV :
        """
        cages: {
            0: [
                [value1, value2],
                [value3, value4]
            ],
            1: [
                [value5, value6],
                [value7, value8]
            ]
        }
        """

        # iterate over every line and try to fetch cage information
        day = -1

        line_index = 0
        position_index = 0
        base_timestamp = -1
        acount = 0

        for line in content:

            curr_day = line.split(" ")[0].split("-")[2].strip()

            # initialize first day
            if day == -1:
                day = curr_day

            curr_time = get_timestamp(line)

            if acount == 0:
                global beggining_time
                time = line.split(",")[0].split(" ")[1].split(":")
                beggining_time.append(int(time[0])*3600+int(time[1])*60+int(time[2]))
                acount = 1

            # initialize first timestamp
            if base_timestamp == -1:
                base_timestamp = curr_time

            # it's a new day, so we need to be pushing to a new line for the cage
            if curr_day != day:
                day = curr_day
                line_index = line_index + 1
                # reset the time, since it's a new day

                position_index = 0
                base_timestamp = curr_time

                # add new empty array
                if counter == 0:
                    for cage in cages:
                        cages[cage].append([0])
                else:
                    for cage in [i for i in cages if "_2" in i]:
                        cages[cage].append([0])

            # get the current cage for the line
            if counter == 0:
                curr_cage = line.split("Cage")[1].split(":")[0].strip()
            else:
                curr_cage = line.split("Cage")[1].split(":")[0].strip() + "_2"

            # if the cage is not in the cages array, add it
            if curr_cage not in cages:
                cages[curr_cage] = [[0]]

            # get the reading for the cage
            curr_reading = int(line.split(":")[4].split(".")[0].strip())

            previous_reading = cages[curr_cage][line_index][position_index]

            # if it's within the time bin range, add the current value
            # to the previously stored one
            if base_timestamp + TIME_BIN > curr_time:
                curr_reading = curr_reading + previous_reading
            # if it's passed the time, pass to a new position
            else:
                position_index = position_index + 1
                # base timestamp advances amount specified by time bin
                base_timestamp = base_timestamp + TIME_BIN

                # add a new position to all cages
                if counter == 0:
                    for cage in cages:
                        cages[cage][line_index].append(0)
                else:
                    for cage in [i for i in cages if "_2" in i]:
                        cages[cage][line_index].append(0)

            cages[curr_cage][line_index][position_index] = curr_reading
        counter += 1

    global days
    days = len(cages[next(iter(cages))])

    for cage in cages:
        if len(cages[cage][0]) < len(cages[cage][1]):
            pad = len(cages[cage][1]) - len(cages[cage][0])
            for i in range(pad):
                cages[cage][0].insert(0,0)
        if len(cages[cage][-1]) < len(cages[cage][1]):
            pad = len(cages[cage][1]) - len(cages[cage][-1])
            for i in range(pad):
                cages[cage][-1].append(0)

    remove(getcwd() + "/Temp1")
    if in2 != "":
        remove(getcwd() + "/Temp2")

def write_cages(out):
    # iterate over every cage
    for cage in cages:
        # create csv
        cage_filepath = out +  "/Cage_" + cage + ".csv"

        # check if file already exists, if so, delete
        if path.exists(cage_filepath):
            remove(cage_filepath)

        cage_file = open(cage_filepath, 'x')

        cage_lines = cages[cage]
        for line in cage_lines:
            # remove array brackets from string
            cage_line = str(line)[1:len(str(line))-1]
            cage_file.write(cage_line)
            cage_file.write("\n")

        cage_file.close()

def write_cages_column(out):
    # iterate over every cage
    for cage in cages:
        # create csv
        cage_filepath = out + "/Cage_" + cage + "_single_column.csv"

        # check if file already exists, if so, delete
        if path.exists(cage_filepath):
            remove(cage_filepath)

        cage_file = open(cage_filepath, 'x')

        cage_lines = cages[cage]
        for line in cage_lines:
            for value in line:
                # remove array brackets from string
                # cage_line = str(line)[1:len(str(line))-1]
                cage_file.write(str(value))
                cage_file.write("\n")
        
        cage_file.close()

beggining_time = []
def adjust_days(out, check, check2, check3):

    dir_list = listdir(out)

    ids = []

    if check == 0:
        day = 6 * 3600
        night = 18 * 3600
    else:
        day = 7 * 3600
        night = 19 * 3600

    counter = -1
    global tdays
    # acount = 0

    for filename in dir_list:

        daycounter = -1

        # if filename.endswith('2_single_column.csv'):
        #
        #     time = beggining_time[1]-360
        #     if time > day-360 and time < night-360:
        #         daycounter += 1
        #         acount = 1
        # else:
        #     time = beggining_time[0]-360
        #     if time > day-360 and time < night-360:
        #         daycounter += 1
        #         acount = 1

        if filename.endswith('_single_column.csv'):
            time = -360
            ids.append([[""]])

            counter += 1

            # if acount == 1:
            #     acount = 0
            #     ids[counter].append([filename.split('_s')[0], "", ""])
            #     daycounter += 1
            #     ids[counter][daycounter].append("Day " + str(daycounter))

            with open(out + '\\' + filename) as f:
                lines = f.readlines()

            for i in lines:
                time += 360

                if time == day:
                    ids[counter].append([filename.split('_s')[0],"","","",""])
                    daycounter += 1
                    ids[counter][daycounter+1].append("Day " + str(daycounter))

                if time == 86400:
                    time = 0

                if daycounter >= 0:
                    if time < day or time >= night:
                        ids[counter][daycounter+1].append(int(i.strip('\n')))

                tdays = daycounter


    if check3 == 0:
        for filename in dir_list:
            if filename.endswith('_single_column.csv'):
                remove(out+"\\"+filename)


    if check == 0:
        adjusted = [["Cage","ID","Gender","Condition","Treatment","Day"]+((",".join(["%02d:%02d" % (divmod(i * 6, 60)) + "h" for i in range(180,240)]))).split(',')+((",".join(["%02d:%02d" % (divmod(i * 6, 60)) + "h" for i in range(60)]))).split(',')]
    else:
        adjusted = [["Cage","ID","Gender","Condition", "Treatment", "Day"] + ((",".join(["%02d:%02d" % (divmod(i * 6, 60)) + "h" for i in range(190, 240)]))).split(',') + ((",".join(["%02d:%02d" % (divmod(i * 6, 60)) + "h" for i in range(70)]))).split(',')]

    for i in ids:
        for i in i[1:days+1]:
            adjusted.append(i)


    adjus_sum = [["Cage","ID","Gender","Condition","Treatment"]+(",".join(["Day " + str(i) for i in range(tdays)])).split(',')]
    adjus_sum_raw = [["Cage","ID","Gender","Condition","Treatment"]+(",".join(["Day " + str(i) for i in range(tdays)])).split(',')]
    counter=-1
    curr = 1

    for i in adjusted[1:]:
        if counter == -1:
            adjus_sum.append([i[0],"","","",""])
            adjus_sum_raw.append([i[0],"","","",""])
        adjus_sum[curr].append(sum(i[6:])*40.84/100000)
        adjus_sum_raw[curr].append(sum(i[6:]))
        counter += 1
        if counter >= tdays - 1:
            curr += 1
            counter=-1

    df = pd.DataFrame( columns = adjusted[0],data = adjusted[1:])
    writer = pd.ExcelWriter(out + '\\' + 'Final Adjusted.xlsx', engine="xlsxwriter", engine_kwargs={'options': {'strings_to_numbers': True}})
    df.to_excel(writer, sheet_name="Data", startrow=1, header=False, index=False)

    workbook = writer.book
    worksheet = writer.sheets["Data"]

    # Get the dimensions of the dataframe.
    (max_row, max_col) = df.shape

    # Create a list of column headers, to use in add_table().
    column_settings = [{"header": column} for column in df.columns]

    # Add the Excel table structure. Pandas will add the data.
    worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

    # Make the columns wider for clarity.
    cell_format = workbook.add_format({'align': 'center'})
    cell_format.set_num_format(2)
    worksheet.set_column(0, max_col - 1, 12.67, cell_format)

    df = pd.DataFrame(columns = adjus_sum[0],data = adjus_sum[1:])
    df.to_excel(writer, sheet_name="Sums Kms", startrow=1, header=False, index=False)

    workbook = writer.book
    worksheet = writer.sheets["Sums Kms"]

    # Get the dimensions of the dataframe.
    (max_row, max_col) = df.shape

    # Create a list of column headers, to use in add_table().
    column_settings = [{"header": column} for column in df.columns]

    # Add the Excel table structure. Pandas will add the data.
    worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

    # Make the columns wider for clarity.
    cell_format = workbook.add_format({'align': 'center'})
    cell_format.set_num_format(2)
    worksheet.set_column(0, max_col - 1, 12.67, cell_format)

    if check2 == 1:
        df = pd.DataFrame(columns=adjus_sum_raw[0], data=adjus_sum_raw[1:])
        df.to_excel(writer, sheet_name="Sums Raw", startrow=1, header=False, index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sums Raw"]

        # Get the dimensions of the dataframe.
        (max_row, max_col) = df.shape

        # Create a list of column headers, to use in add_table().
        column_settings = [{"header": column} for column in df.columns]

        # Add the Excel table structure. Pandas will add the data.
        worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

        # Make the columns wider for clarity.
        cell_format = workbook.add_format({'align': 'center'})
        cell_format.set_num_format(2)
        worksheet.set_column(0, max_col - 1, 12.67, cell_format)

    f.close()
    writer.close()


def join_files(out,check2,check4):

    files = [i for i in listdir(out) if ".csv" in i and "single" not in i]

    if "Final Data.xlsx" in listdir(out):
        remove(out+"/Final Data.xlsx")

    if check4 == 0:


        final = ["Cage ID,ID,Gender,Condition,Treatment," + ",".join(["%02d:%02d" % (divmod(i*6, 60))+"h" for i in range(240)])]
        daysums = ["Cage ID,ID,Gender,Condition,Treatment," + ",".join(["Day " + str(i) for i in range(days)]) + ",Total"]
        daysums_conv = [daysums[0]]

        sumcounter = 1
        daysums_total = 0
        daysums_conv_total = 0
        for filename in files:
            daysums.append(filename.strip(".csv") + ",,,,")
            daysums_conv.append(filename.strip(".csv") + ",,,,")
            with open(out + "\\" + filename) as f:
                data = f.readlines()
            for i in range(len(data)):
                data[i] = data[i].strip("\n")
                sums = str(sum(map(int, data[i].split(","))))
                daysums[sumcounter] += "," + sums
                daysums_total += float(sums)
                daysums_conv[sumcounter] += "," + str(float(sums)*40.84/100000)
                daysums_conv_total += float(sums)*40.84/100000
                data[i] = filename.strip(".csv") + ",,,,," + data[i]
                final.append(data[i])
            daysums[sumcounter] += "," + str(daysums_total)
            daysums_conv[sumcounter] += "," + str(daysums_conv_total)
            sumcounter +=1
            daysums_total = 0
            daysums_conv_total = 0

    # Write first sheet with all time bins for all cages
        df = pd.DataFrame(columns=final[0].split(","),data=[row.split(",") for row in final[1:]])
        writer = pd.ExcelWriter(out + '/Final Data.xlsx', engine="xlsxwriter", engine_kwargs={'options': {'strings_to_numbers': True}})
        df.to_excel(writer, sheet_name="Data", startrow=1, header=False, index=False)

        workbook = writer.book
        worksheet = writer.sheets["Data"]

        # Get the dimensions of the dataframe.
        (max_row, max_col) = df.shape

        # Create a list of column headers, to use in add_table().
        column_settings = [{"header": column} for column in df.columns]

        # Add the Excel table structure. Pandas will add the data.
        worksheet.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

        # Make the columns wider for clarity.
        cell_format = workbook.add_format({'align': 'center'})
        cell_format.set_num_format(2)
        worksheet.set_column(0, max_col - 1, 12.67, cell_format)

    # Write second sheet with all value sums
        if check2 == 1:
            df2 = pd.DataFrame(columns=daysums[0].split(","),data=[row.split(",") for row in daysums[1:]])
            df2.to_excel(writer, sheet_name="Sums Raw", startrow=1, header=False, index=False)

            worksheet2 = writer.sheets["Sums Raw"]

            # Get the dimensions of the dataframe.
            (max_row, max_col) = df2.shape

            # Create a list of column headers, to use in add_table().
            column_settings = [{"header": column} for column in df2.columns]

            # Add the Excel table structure. Pandas will add the data.
            worksheet2.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

            # Make the columns wider for clarity.
            worksheet2.set_column(0, max_col - 1, 12.67, cell_format)

    # Write second sheet with all value sums converted to cm

        df3 = pd.DataFrame(columns=daysums_conv[0].split(","),data=[row.split(",") for row in daysums_conv[1:]])
        df3.to_excel(writer, sheet_name="Sums Kms", startrow=1, header=False, index=False)

        worksheet3 = writer.sheets["Sums Kms"]

        # Get the dimensions of the dataframe.
        (max_row, max_col) = df3.shape

        # Create a list of column headers, to use in add_table().
        column_settings = [{"header": column} for column in df3.columns]

        # Add the Excel table structure. Pandas will add the data.
        worksheet3.add_table(0, 0, max_row, max_col - 1, {"columns": column_settings})

        # Make the columns wider for clarity.
        worksheet3.set_column(0, max_col - 1, 12.67, cell_format)

        writer.close()

    for filename in files:
        remove(out + "\\" + filename)

check = IntVar()
check2 = IntVar()
check3 = IntVar()
check4 = IntVar()
check4.set(1)

input1 = Button(root, text="Input 1", command=lambda:browsefunc(0)).grid(row=0, column=0, padx = 5, pady = 5, sticky= "ew")
input2 = Button(root, text="Input 2", command=lambda:browsefunc(1)).grid(row=1, column=0, padx = 5, pady = 5, sticky= "ew")
output = Button(root, text="Output directory", command=lambda:browsefunc(2)).grid(row=2, column=0, padx = 5, pady = 5, sticky= "ew")
checkbox = Checkbutton(root, text='Schedule = 6h-18h',variable=check, onvalue=1, offvalue=0, command=lambda:checkbox_text(check))
checkbox.grid(row=3, column=0, padx = 5, pady = 5, sticky= "w",columnspan=2)
checkbox2 = Checkbutton(root, text='Include raw wheel turns?',variable=check2, onvalue=1, offvalue=0)
checkbox2.grid(row=3, column=2, padx = 5, pady = 5, sticky= "ew")
checkbox3 = Checkbutton(root, text='Adjusted to schedule only?',variable=check4, onvalue=1, offvalue=0)
checkbox3.grid(row=4, column=0, padx = 5, pady = 5, sticky= "w", columnspan=2)
checkbox4 = Checkbutton(root, text='Include invidual single column .csv?',variable=check3, onvalue=1, offvalue=0)
checkbox4.grid(row=4, column=2, padx = 5, pady = 5, sticky= "ew")
run = Button(root, text="Run", command=lambda:[root.destroy(),main.update(),getdata(labels[0],labels[1],labels[2])]).grid(row=5, column=0, padx = 5, pady = 5, sticky= "ew", columnspan=3)

try:
    if localtime().tm_isdst == 1:
        checkbox.select()
        check.set(1)
        checkbox.config(text='Day-night = 7h-19h')
except:
    pass
def checkbox_text(var):
    if var.get() == 1:
        checkbox.config(text='Day-night = 7h-19h')
    else:
        checkbox.config(text='Day-night = 6h-18h')

if path.isdir(path.join(path.join(environ['USERPROFILE']), 'Desktop')+"\\RW Data"):
    def_path = path.join(path.join(environ['USERPROFILE']), 'Desktop')+"\\RW Data\\*.txt"
else:
    def_path = getcwd() + '/*.txt'

list_of_files = glob(def_path) # * means all if need specific format then *.csv
try:
    latest_file = max(list_of_files, key=path.getmtime)
    creation_time = path.getctime(latest_file)
    list_of_files.remove(latest_file)
except:
    latest_file = ""

pathlabel = Label(root)
pathlabel.grid(row=0, column=1, padx = 5, pady = 5, columnspan=2)
pathlabel.config(text=latest_file)

try:
    latest_file = max(list_of_files, key=path.getmtime)
    if creation_time-path.getctime(latest_file) > 60:
        latest_file = ""

except:
    latest_file = ""

pathlabel2 = Label(root)
pathlabel2.grid(row=1, column=1, padx = 5, pady = 5, columnspan=2)
pathlabel2.config(text=latest_file)

pathlabel3 = Label(root)
pathlabel3.grid(row=2, column=1, padx = 5, pady = 5, columnspan=2)
pathlabel3.config(text=getcwd())

pathlabel4 = Label(root)
pathlabel4.grid(row=6, column=0, padx = 5, pady = 5, columnspan=3, sticky= "ew")
pathlabel4.config(text="This will erase files from previous runs from the output folder!")

buttons = [pathlabel,pathlabel2,pathlabel3]
in1 = pathlabel.cget("text")
in2 = pathlabel2.cget("text")
out = pathlabel3.cget("text")
labels = [in1,in2,out]

root.grid_columnconfigure((1), weight=1)

root.mainloop()




