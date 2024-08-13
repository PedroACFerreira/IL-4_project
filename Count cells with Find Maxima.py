#@ File    (label = "Input directory", style = "directory") srcFile
#@ File    (label = "Output directory", style = "directory") dstFile
#@ String  (label = "File extension", value=".tif") ext
#@ String  (label = "File name contains", value = "") containString
#@ boolean (label = "Keep directory structure when saving", value = true) keepDirectories

# See also Process_Folder.ijm for a version of this code
# in the ImageJ 1.x macro language.

# -Dpython.console.encoding=UTF-8

import os
from ij import IJ, ImagePlus
from ij import WindowManager as WM 


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
 
def process(srcDir, dstDir, currentDir, fileName, keepDirectories):
  print "Processing:"
   
  # Opening the image
  print "Open image file", fileName
  IJ.open(currentDir + "\\" + fileName)
  #imp = IJ.openImage(os.path.join(currentDir, fileName))

  windows = WM.getImageTitles()
  number = len(windows)
  IJ.selectWindow(windows[0])
  IJ.run("Properties...", "channels=1 slices=1 frames=1 pixel_width=0.09 pixel_height=0.09 voxel_depth=1")
  IJ.run("Duplicate...", " ");
  IJ.run("8-bit");
  IJ.run("Threshold...","BlackBackground = true");
  IJ.setThreshold(0, 254)
  IJ.run("Convert to Mask")
  IJ.run("Close")
  IJ.run("Create Selection")
  
  IJ.run("Set Measurements...", "area redirect=None decimal=3")
  IJ.run("Measure")
  IJ.saveAs("Results", dstDir + "\\" + fileName.split(".")[0] + "_area.txt" )
  IJ.run("Clear Results")
  IJ.selectWindow(windows[0])
  IJ.run("Restore Selection")
  IJ.run("Despeckle")
  IJ.run("Despeckle")
  IJ.run("Remove Outliers...", "radius=11 threshold=50 which=Bright")
  IJ.run("Gaussian Blur...", "sigma=4")
  IJ.run("Find Maxima...", "prominence=30 strict exclude output=Count")
  IJ.saveAs("Results", dstDir + "\\" + fileName.split(".")[0] + ".txt" )
  IJ.run("Clear Results")
	
  windows = WM.getImageTitles()
  number = len(windows)
  for i in range(number):
	  IJ.selectWindow(windows[i])
	  IJ.run("Close")


 
run()
