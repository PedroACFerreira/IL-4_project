# The purpose of this script is to batch analyse microglia 3D images and calculate both the convex hull and 
# fractal dimension. The plugins required for this can be found at the following links:
#
# Convex Hull 3D - https://imagej.net/ij/plugins/3d-convex-hull/index.html
# To cite - Topical Neuroprotectin D1 Attenuates Experimental CNV and Induces Activated Microglia Redistribution.
#
# FractalCount 	- https://github.com/perchrh/ImageJFractalDimension/tree/master?tab=readme-ov-file
#				- https://imagej.net/ij/plugins/download/misc/FractalCount_.java
#	Save the file as FractalCount_.java in the plugins folder
#
# Also, this script was optimized for .ims files of microglia reconsctructed in Bitplane Imaris, where then the main
# channel (e.g. Alexa 488) was masked to only contain the microglia signal. For the script to be run as is, images 
# will need to have at least two channels, with the channel only containing the microglia being the second. It will
# only analyse the second channel specifically. For you to use the script in images configured in some other way, 
# change either the parameter where the Bio-Formats importer splits the channels, or change the
# "IJ.selectWindow(windows[1])" command to select the appropriate windows, with 1 being the second channel, 
# 2 the third, etc...
#
# This script is optimized for 3D image stacks, results from 2D images may not be as expected without optimization
#
# This script will produce .txt files for each image, for both measurements. This is easy to import to excel through 
# the "Import Data->From Folder" function. All rows will contain image file name.
#
# FractalCount is run with default settings, and after 3D projection with interpolation it provides what I can figure
# tro be the most correct estimate of the Fractal Dimension of the surface area of the microglia. You can tweak both
# the 3D Project or FractalCount settings to provide different results if you figure there is a better way of analysing
# this. BoneJ and FracLac also have other plugins for fractal dimension calculation, but they are tricky to get working# in 3d Imges. Fractal Dimension of 3D images must be between 2 and 3.
#
# Please mantain naming schemes and image structure between files. Do not include special characters in file names.
# This script was last tested with Fiji running Imagej 1.53f.
# The script is commented for ease of reading.
# 3D Project and FractalCount are not optimized for multi-core, script takes a long while to run. On a 5900X processor
# takes about 10-15min per image. With 300Mb microglia images from Imaris, it uses about 7-10Gb of RAM at any point.
#
# If you use this script, please cite
# Guedes and Ferreira et al, IL-4 shapes microglia-dependent pruning of the cerebellum during postnatal development
# https://doi.org/10.1016/j.neuron.2023.09.031
#
# Any questions contact pedroferreira@cnc.uc.pt or jpeca@uc.pt
#
#####################################################################################################################

#This is just to prevent some Jython character errors in the console
#-Dpython.console.encoding=UTF-8

#Necessary Packages
import csv
import os
from ij import IJ, ImagePlus
from ij import WindowManager as WM 

#ImageJ prompt to have the user specficy folders and file extension
#These decorators are necessary for the prompt where we specificy the folders where the script will run
#@ File    (label = "Input directory", style = "directory") srcFile
#@ File    (label = "Output directory", style = "directory") dstFile
#@ String  (label = "File extension", value=".ims") ext
#@ String  (label = "File name contains", value = "") containString
#@ boolean (label = "Keep directory structure when saving", value = true) keepDirectories
#@CommandService cs

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
      process(srcDir, dstDir, root, filename, keepDirectories)
 
#From here on it's the actual function that calculates fractal dimension and hull
def process(srcDir, dstDir, currentDir, fileName, keepDirectories):
  print "Processing:"

  #Creates new folders to save the data to
  if not os.path.exists(dstDir + "\\" + "Fractal"):
    os.makedirs(dstDir +  "\\Hull")
    os.makedirs(dstDir + "\\Fractal")
    
  # Opening the image
  print "Open image file", fileName
  # We use the Bio-Formats importer to open the image
  IJ.run("Bio-Formats Windowless Importer", "open=" + "[" + currentDir + "\\" + fileName + "] autoscale color_mode=Default view=Hyperstack stack_order=XYCZT series_1")
  # We split the channels so we only get the premasked channel with only the microglia
  IJ.run("Split Channels")
  
  # This selects the correct windows with the appropriate channel, number 1 for channel 2
  windows = WM.getImageTitles()
  number = len(windows)
  IJ.selectWindow(windows[1])
  
  # We set the slice to number 10 to avoid a possible first slice where no cell signal is present, so when we convert to
# 8-bit and set a threshold ImageJ doesn't get confused and consider the wrong background color for some of the slices.
# This script assumes a dark background. If you have a white background, change "BlackBackground = true" to false, and
# change threshold to 0-254

  IJ.run("Set Slice...","slice=10")
  IJ.run("8-bit") #Convert to 8-bit
  IJ.run("Threshold...","BlackBackground = true"); #Set a Threshold to convert the image to binary
  IJ.setThreshold(1, 255) # 1-255 will grab all non 0 pixels, in this case non-black
  IJ.run("Convert to Mask", "background=Dark black"); #Apply the threshold
  IJ.run("Close"); #Close that menu
  
# We use this to close any gaps inside the cell body so that the FractalCount plugin works properly 
  IJ.run("Fill Holes","Yes")
  
# We again select the right channel, and run measure convex folume, then saving the results to the appropriate .txt
  IJ.selectWindow(windows[1])
  IJ.run("Measure Convex Volume...")
  IJ.saveAs("Results", dstDir + "\\" + "Hull\\" + "Hull_" + fileName.split(".")[0] + ".txt" )
  IJ.run("Clear Results") #Important to clear results not to get duplicates

# Close all non image windows
  reswin = WM.getNonImageTitles()
  for i in range(0,(len(reswin))):
  	IJ.selectWindow(reswin[i])
  	IJ.run("Close")
	
  IJ.selectWindow(windows[1]) #Select Window

# This is to get voxel values
  imp = IJ.getImage()  
  cal = imp.getCalibration()


  IJ.selectWindow(windows[1])
#The settings here rotate the image around the Y-Axis and interpolate missing spaces between slices. This is the most
#computationally intensive part of the script. You can try to adjust the settings, but it will yield different results
  IJ.run("3D Project...", "projection=[Brightest Point] axis=Y-Axis slice=" + str(cal.pixelDepth) + " initial=0 total=360 rotation=1 lower=1 upper=255 opacity=0 surface=100 interior=50 interpolate")
  IJ.run("Make Binary", "method=Huang background=Dark calculate black")
  IJ.run("Find Edges", "stack")
  
  #Run FractalCount to estimate Fractal Dimension. These settings worked nicely in microglia, but your mileage may vary
  IJ.run("FractalCount ", "plot threshold=1 start=128 min=1 box=2 number=1")
  IJ.saveAs("Text", dstDir + "\\" +  "Fractal\\" + "Fractal_" + fileName.split(".")[0] + ".txt" )

 # At last, we close all windows to reset the script and run the next file
  reswin = WM.getNonImageTitles()
  for i in range(0,(len(reswin))):
  	IJ.selectWindow(reswin[i])
  	IJ.run("Close")

  windows = WM.getImageTitles()
  for i in range(0,(len(windows))):
  	IJ.selectWindow(windows[i])
  	IJ.run("Close")
  
# This is necessary to avoid RAM overflow, as sometimes ImageJ has trouble disposing of no longer required data in RAM
  IJ.run("Collect Garbage")
  
run()
