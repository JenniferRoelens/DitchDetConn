'''
Created in 2017
@author: Jennifer Roelens
'''

import os
import arcpy
from arcpy import env
arcpy.env.overwriteOutput = True


"""
Parameter settings
------------------
filter_size = distance in meters, 
                size of the smoothing window
filter_shape = "Circle" or "Rectangle", 
                shape of the smoothing window
thresResRel = "otsu" or "std1", 
                threshold used for thresholding the Relative Elevation Attribute
thresLength = "lengthfup" [used in paper] or "lengthstd", 
                threshold used for removing small linear elements
conn = 4 or 8, 
                the way raster cells are connected to define clustered raster cells
shiftDist = using the original point clouds, 
                distance that will be looked at from original vertex to find lowest points to shift
connBuffer = distance in meters,
                when defining variables from the possible connecting segments, size of buffer that is used
"""

filter_size = 3
filter_shape = "Circle"
thresResRel = 'otsu'
thresLength = 'lengthfup'
conn = 8
shiftDist = 2
connBuffer = 2

"""
workspace
---------
Define workspace
"""
# workspace will be cleared for saving space
workspace = "C:\\Users\\u0099505\\workdir\\"

"""
Folder structure for DetConn is as follows:
-------------------------------------------
inputFolder: 
    defines where the input files are located
outputFolder: 
    defines where files will be written
def_geodatabase: 
    defines where files dependent on a ArcGIS database will be written
LiDARFolder: 
    defines where the .las files are located
PointTBX: 
    defines where the CreatePointsLines toolbox is located 
    (download from https://www.arcgis.com/home/item.html?id=a2a41c8345e24ab6a9dd2ae215710b39)

End folders with \\
"""

inputFolder = "E:\\DataFolderCh2\\SA2\\"
outputFolder = "C:\\Users\\u0099505\\Documents\\output\\210817_VHA_1_" + filter_shape + "_" + str(filter_size) + "\\"
def_geodatabase = "C:\\Users\\u0099505\\Documents\\ArcGIS\\Default.gdb\\"
LiDARFolder ="E:\\3_LiDAR_Vlaanderen\\Hasselt\\original\\"
PointTBX = "C:\\Users\\u0099505\\Documents\\"

"""
Input file structure for DetConn is as follows:
----------------------------------------------
DTMfile: 
    DTM filename in input folder [raster, res. 1m]
LandCoverfile: 
    Land cover filename in input folder [raster, res. 1m, check DetConn_CrFiles line 52 to input your own gridcodes]
Roadsfile: 
    Road dataset filename in input folder [.shp]
RGBfile: 
    RGB orthophto filename in input folder [raster, res. 0.20m]
Intensityfile: 
    LiDAR intensity filename in input folder [raster, res.1m, optional, "", but will be created in DetConn_CrFiles]
StudyAreafile: 
    Study area filename in input folder [.shp, optional, "" when clipping is not needed]
VHAfile: 
    Already existing digital network filename in input folder [.shp, optional, ""]
DitchNetworkfile: 
    Ditch network filename in input folder for validation [.shp, optional, ""]
openDitchNetworkfile: 
    Open Ditch network filename in input folder for validation [.shp, optional, ""]
"""

DTMfile = "GeoTIFF\\" + "DHMVIIDTMRAS1m_k25.tif"
LandCoverfile ="BBK1_12_Kbl25\\GeoTIFF\\BBK1_12_Kbl25.tif"
Roadsfile = "Wbn.shp"
RGBfile = "Explanatory\\RGB14_258n7n.tif"
Intensityfile = "Intensityras"
StudyAreafile = "studyArea_checked.shp"
VHAfile = "VHA.shp"
DitchNetworkfile = "ditchnetwork.shp"
openDitchNetworkfile ="openDitchNetwork.shp"

"""
GIS settings
"""
env.workspace = workspace
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3d")
arcpy.env.overwriteOutput = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(31370)

"""
CODE
"""
print "Setting input..."

# Create input files
inputDTM = inputFolder + DTMfile
inputLandCover = inputFolder + LandCoverfile
inputRoads = inputFolder + Roadsfile
inputRGB = inputFolder + RGBfile
inputIntensity = inputFolder + Intensityfile
inputStudyArea = inputFolder + StudyAreafile
VHA = inputFolder + VHAfile
inputDitchNetwork = inputFolder + DitchNetworkfile
inputOpenDitchNetwork = inputFolder + openDitchNetworkfile

# Create output folder if necessary
if not os.path.exists(outputFolder):
    os.makedirs(outputFolder)
    
if conn == 8:
    connmat = [[1,1,1],[1,1,1],[1,1,1]]
if conn ==4:
    connmat = [[0,1,0],[1,1,1],[0,1,0]]

print "Finished setting input"