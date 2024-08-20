#Decorators required for the settings prompt

#@ File    (label = "Input Directory", style = "directory") srcFile
#@ File    (label = "Output Directory", style = "directory") dstFile
#@ String  (label = "Name to save as", value = "Data") savename
#@ String  (label = "Image Name Contains", value = "") containString
#@ String  (label = "Image Extension", value=".tif") ext
#@ Double (label = "Pixel Width", value="0.22") PW
#@ Double  (label = "Pixel Height", value="0.22") PH
#@ String (label = "Outer background",choices={"Bright","Dark"}, style="radioButtonHorizontal") OBG
#@ String (label = "Cell color",choices={"Bright","Dark"}, style="radioButtonHorizontal") BG
#@ String (visibility=MESSAGE, value="Check these values manually beforehand", required=false) msg
#@ Integer  (label = "Find Maxima Threshold", value="30") PR
#@ String (label = "Remove Outliers",choices={"Yes", "No"}, style="radioButtonHorizontal") OT
#@ Integer  (label = "Outliers Radius", value="10") OTR


#Import the required packages
import os
from ij import IJ, ImagePlus
from ij import WindowManager as WM 
from ij.measure import ResultsTable

#Get file names from prompt
def run():
  srcDir = srcFile.getAbsolutePath()
  dstDir = dstFile.getAbsolutePath()
  for root, directories, filenames in os.walk(srcDir):
    filenames.sort();
    for filename in filenames:
      # Check for file extension
      if not filename.endswith(ext):
        continue
      # Check for file name pattern
      if containString not in filename:
        continue
      process(srcDir, dstDir, root, filename)

#Function to calculate slice area and count number of cells. It will iterate over all files selected previously
Columns = ["FileName","Condition","Gender","Count","Area (um2)","Density(cell/cm2)"]
Final = []

def process(srcDir, dstDir, currentDir, fileName):
  print "Processing:"
   
  # Opening the image
  print "Open image file", fileName
  IJ.open(currentDir + "\\" + fileName)
 
  # Get a list of the open windows and select the first, our image
  windows = WM.getImageTitles()
  number = len(windows)
  IJ.selectWindow(windows[0])
  
  # Set the proper voxel properties, you can get this from zen, so imagej knows how to convert pixel to cm. 
  # Change pixel_width and pixel_height to the appropriate values
  IJ.run("Properties...", "channels=1 slices=1 frames=1 pixel_width=" + str(PW) + " pixel_height=" + str(PH) + " voxel_depth=1")
  IJ.run("Duplicate...", " "); # Duplicate the image
  IJ.run("8-bit"); # Convert the duplicated image to 8-bit = grey, so we can do a threshold
  IJ.run("Threshold...","BlackBackground = " + BG); # Get everything that is not the background. If the background is black, change to True
  # Do this manually once so you know the values that select everything but the background, meaning, whole image red, background white
  # You can find this at Image > Adjust > Threshold   (Not Color Threshold)
  
  if OBG == "Bright":
  	IJ.setThreshold(0, 254)  
  else:
  	IJ.setThreshold(1, 255)  
  	
  #Conver to a mask to apply to the original image, and create a selection of the mask
  IJ.run("Convert to Mask")
  IJ.run("Close")
  IJ.run("Create Selection")
  
  # Grab the area and then save to a file in the destination directory with _area appended to the filename
  IJ.run("Set Measurements...", "area redirect=None decimal=3")
  IJ.run("Measure")
  
  # Reselect original window
  IJ.selectWindow(windows[0])
  
  # Apply the mask so it only calculates there
  IJ.run("Restore Selection")
  
  # Remove some noise from the image
  IJ.run("Despeckle")
  IJ.run("Despeckle")
  
  if OT:
 	if BG == "Dark":
 		OTBG = "Bright"
 	else:
 		OTBG = "Dark"
 		
  	IJ.run("Remove Outliers...", "radius=" + str(OTR) +" threshold=50 which=" + OTBG)
  	
  IJ.run("Gaussian Blur...", "sigma=4")
  
  # Calculate number of cells. Do this manually beforehand to estimate the correct value for prominence
  # If you want to exclude cells at the edges, add the word exclude after strict. If background is dark, remove light
  # You can find this function at Process > Find Maxima
  # Click preview selection, then change the prominence value until it detects what you want.  Do this with a couple of images to get a feel for the correct value
  
  if BG == "Dark":
  	FMBG = "light"
  else:
  	FMBG = "dark"
  	
  IJ.run("Find Maxima...", "prominence=" + str(PR) + " strict "+ FMBG + " output=Count")
  
  # Save results and then save to a file in the destination directory with _MLI appended to the filename
  table = ResultsTable.getResultsTable()
  Count=table.getValue("Count", 1)
  Area=table.getValue("Area", 0)
  Density=float(Count)/float(Area)
  Final.append([fileName.split(".")[0],"","",Count,Area,Density*1000000])
  
  IJ.run("Clear Results")
  
  # Close all windows before opening the next	
  windows = WM.getImageTitles()
  number = len(windows)
  for i in range(number):
	  IJ.selectWindow(windows[i])
	  IJ.run("Close")
	  
  IJ.run("Collect Garbage")
  
run()

tb = ResultsTable()
rt = tb.getResultsTable()

for line in Final:
	for val in range(len(line)):
		rt.addValue(Columns[val], line[val])
	if line != Final[-1]:
		rt.addRow()

rt.showRowIndexes(False)	

dstDir = dstFile.getAbsolutePath()
rt.saveAs(dstDir + "\\" + savename + ".csv")
IJ.run("Clear Results")
	
IJ.run("Collect Garbage")
	  
