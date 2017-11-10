'''
Created in 2017
@author: Jennifer Roelens

# Run this file after the detection stage if you want to shift the preliminary network to the depressions
# in the point clouds
'''

import DetConn_Input as inp
import os
import arcpy
from arcpy import sa
import numpy
from scipy import spatial as sp
import laspy
# laspy can be downloaded from the anaconda repository online

"""
CODE
"""
print 'Start shifting'

# Add toolbox
#------------
arcpy.AddToolbox(inp.PointTBX + "CreatePointsLines.tbx", 'test')

# Create preliminary network points
#----------------------------------
arcpy.SplitLine_management(inp.outputFolder + "thin_merge" + ".shp", inp.outputFolder + "thin_split" + ".shp")
arcpy.DeleteIdentical_management(inp.outputFolder + "thin_split" + ".shp", ['Shape'])
arcpy.CreatePointsLines_test(inp.outputFolder + "thin_split" + ".shp", "INTERVAL BY DISTANCE", "BEGINNING", "NO", "FID", "20", "BOTH", inp.outputFolder + "ThinPoints" + ".shp") # @UndefinedVariable

# Create preliminary network point buffers with the buffer equaling the search radius 
#------------------------------------------------------------------------------------
arcpy.Buffer_analysis(inp.outputFolder + "ThinPoints" + ".shp", inp.outputFolder + "ThinPointsBuff" + ".shp", str(inp.shiftDist) + ' Meters')
arcpy.Dissolve_management(inp.outputFolder + "ThinPointsBuff" + ".shp", inp.outputFolder + "ThinPointsBuffDissolve" + ".shp")
arcpy.MultipartToSinglepart_management(inp.outputFolder + "ThinPointsBuffDissolve" + ".shp", inp.outputFolder + "ThinPointsBuffSinglePart" + ".shp")

# Add field for elevation
#-------------------------
arcpy.AddField_management(inp.outputFolder + "ThinPoints" + ".shp", 'Z_shift', 'double')

# Get coordinates original vertices
#----------------------------------
print "Get coordinates original vertices"
sa.ExtractValuesToPoints(inp.outputFolder + "ThinPoints" + ".shp", inp.inputDTM, inp.outputFolder + "ThinPointsValues" + ".shp")
ThinPointsArr = arcpy.da.FeatureClassToNumPyArray(inp.outputFolder + "ThinPointsValues" + ".shp", '*' )  # @UndefinedVariable
o = numpy.array([ThinPointsArr['Shape'][:,0], ThinPointsArr['Shape'][:,1]])
ot = numpy.transpose(o, axes=None)
    
# Gather all ground and water LiDAR points inside the buffered points of the preliminary network
#-----------------------------------------------------------------------------------------------
xn = numpy.empty([0])
yn = numpy.empty([0])
zn = numpy.empty([0])

print "Loop through .las files to collect ground and water points"

for filename in os.listdir(inp.LiDARFolder):
    if filename.endswith(".las"):
        inFile = laspy.file.File(inp.LiDARFolder + filename, mode = "r")
        Points = inFile.points
        Points = Points['point']
        x = Points['X']/100.
        y = Points['Y']/100.
        z = Points['Z']/100.
        c = Points['raw_classification']
        # Is also possible using the whole LiDAR point dataset, so don't use the idxc steps
        idxc = c != 1
        x = x[idxc]
        y = y[idxc]
        z = z[idxc]
        n = numpy.array((x,y))
        nt = numpy.transpose(n, axes=None)
        zt = numpy.transpose(z, axes=None)
        tree = sp.KDTree(nt)
        treequery = tree.query_ball_point(ot, inp.shiftDist)
        treeq = numpy.delete(treequery,numpy.where([len(t) ==0 for t in treequery]))
        idxall = numpy.empty([0], dtype=int)
        for tr in treeq:
            idxall = numpy.append(idxall, tr)
        idx = numpy.unique(idxall)
        xn = numpy.append(xn, x[idx])
        yn = numpy.append(yn, y[idx])
        zn = numpy.append(zn, z[idx])

numpy.savetxt(inp.outputFolder + 'points.txt', numpy.transpose([xn,yn,zn]))
               
# Create tree for the gathered LiDAR points
#------------------------------------------
n = numpy.array((xn,yn))
nt = numpy.transpose(n, axes=None)
zt = numpy.transpose(zn, axes=None)
zshift = numpy.zeros(shape=(len(ot),1))
nshift = numpy.zeros(shape=(len(ot),2))
zi = numpy.arange(0, len(ot))

print "Find lowest point with r = buff_dist"

tree = sp.KDTree(nt)
treequery = tree.query_ball_point(ot, inp.shiftDist)

# Find the lowest point in the buffer to shift the line vertex to
#----------------------------------------------------------------
for i in zi:
    idx = treequery[i]
    if idx == []:
        znew = -999
        nnew = nt[i]
    else:
        ztnew = zt[idx]
        ntnew = nt[idx]
        zminidx = numpy.argmin(ztnew)
        if len([zminidx]) > 1:
            distidx = numpy.argmin(sp.distance.cdist(ntnew[zminidx],ot[[i]],'euclidean'))
            znew = ztnew[zminidx[distidx]]
            nnew = ntnew[zminidx[distidx]]
        else:
            znew = ztnew[zminidx]
            nnew = ntnew[zminidx] 
    zshift[i] = znew
    nshift[i] = nnew

for i in zi:
    line = ThinPointsArr[i]
    line['Shape'] = nshift[i]
    line['Z_shift'] = zshift[i]
    if line['Z_shift'] == -999:
        line['Z_shift'] = line['RASTERVALU']
    ThinPointsArr[i] = line

# Create new vertex file
#-----------------------
arcpy.da.NumPyArrayToFeatureClass(ThinPointsArr, inp.outputFolder + "ThinPoints_up3Z" + ".shp", # @UndefinedVariable
                                  ['Shape','Z_shift'], "31370")
arcpy.AddGeometryAttributes_management(inp.outputFolder + "ThinPoints_up3Z" + ".shp", "POINT_X_Y_Z_M")

# Shift line network using the new vertices (fixed previous ID)
#--------------------------------------------------------------
arcpy.PointsToLine_management(inp.outputFolder + "ThinPoints_up3Z" + ".shp", inp.outputFolder + "Lines_up" + ".shp", "mem_point_", "mem_point1")

# Restore geometry
#-----------------
print "Restore geometry"
arcpy.AddGeometryAttributes_management(inp.outputFolder + "Lines_up" + ".shp", "LENGTH_3D", "Meters", "SQUARE_METERS", "31370")
arcpy.MakeTableView_management(inp.outputFolder + "Lines_up" + ".shp", "temp")
arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "LENGTH_3D = 0")
if int(arcpy.GetCount_management("temp").getOutput(0)) > 0:
    arcpy.DeleteRows_management("temp")
arcpy.RepairGeometry_management(inp.outputFolder + "Lines_up" + ".shp")
arcpy.Integrate_management(inp.outputFolder + "Lines_up" + ".shp", "2 Meters")
arcpy.RepairGeometry_management(inp.outputFolder + "Lines_up" + ".shp")
arcpy.AddGeometryAttributes_management(inp.outputFolder + "Lines_up" + ".shp", "LINE_START_MID_END", "Meters", "SQUARE_METERS", "31370")

print "Finished"