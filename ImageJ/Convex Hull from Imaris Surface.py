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
  IJ.run("Bio-Formats Windowless Importer", "open=" + "[" + currentDir + "\\" + fileName + "]")
  #imp = IJ.openImage(os.path.join(currentDir, fileName))

  IJ.run("Split Channels");

  windows = WM.getImageTitles()
  number = len(windows)
  print number
  if number == 2:
	  IJ.selectWindow(windows[0])
	  IJ.run("Close")
	  IJ.selectWindow(windows[1])
  elif number == 3:
	  IJ.selectWindow(windows[0])
	  IJ.run("Close")
	  IJ.selectWindow(windows[1])
	  IJ.run("Close")
	  IJ.selectWindow(windows[2])
  elif number == 4:
	  IJ.selectWindow(windows[0])
	  IJ.run("Close")
	  IJ.selectWindow(windows[1])
	  IJ.run("Close")
	  IJ.selectWindow(windows[2])
	  IJ.run("Close")
	  IJ.selectWindow(windows[3])
  elif number == 5:
	  IJ.selectWindow(windows[0])
	  IJ.run("Close")
	  IJ.selectWindow(windows[1])
	  IJ.run("Close")
	  IJ.selectWindow(windows[2])
	  IJ.run("Close")
	  IJ.selectWindow(windows[3])
	  IJ.run("Close")
	  IJ.selectWindow(windows[4])
  elif number == 6:
	  IJ.selectWindow(windows[0])
	  IJ.run("Close")
	  IJ.selectWindow(windows[1])
	  IJ.run("Close")
	  IJ.selectWindow(windows[2])
	  IJ.run("Close")
	  IJ.selectWindow(windows[3])
	  IJ.run("Close")
	  IJ.selectWindow(windows[4])
	  IJ.run("Close")
	  IJ.selectWindow(windows[5])

  IJ.run("Measure Convex Volume...")
  IJ.saveAs("Results", dstDir + "\\" + fileName.split(".")[0] + ".txt" )
  IJ.run("Clear Results")
  IJ.selectWindow(windows[number-1])
  IJ.run("Close")
  reswin = WM.getNonImageTitles()
  IJ.selectWindow(reswin[0])
  IJ.run("Close")
  
run()
