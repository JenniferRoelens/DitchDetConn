'''
Created in 2017
@author: Jennifer Roelens
'''

import DetConn_Input as inp
import DetConn_CrFiles as cr
import os
import arcpy
from arcpy import sa
from arcpy.sa.ParameterClasses import NbrCircle, NbrRectangle
arcpy.env.overwriteOutput = True
import numpy
from scipy import ndimage as nd
from skimage import filters
os.chdir(inp.workspace)

"""
CODE
"""
print "Start detection"

# Create filter based on DTM spatial resolution
#----------------------------------------------
print "Create filter"
if inp.filter_shape == "Circle":
    DTMsmoothedras = sa.FocalStatistics(cr.maskDTMras, NbrCircle(inp.filter_size,"MAP"), "MEAN")
if inp.filter_shape == "Rectangle":
    # 1 m resolution
    if inp.DTMfile  == "GeoTIFF\\" + "DHMVIIDTMRAS1m_k25.tif":
        DTMsmoothedras = sa.FocalStatistics(cr.maskDTMras, NbrRectangle(2*inp.filter_size+1,2*inp.filter_size+1,"MAP"), "MEAN")
    # 0.5 m resolution
    else: DTMsmoothedras = sa.FocalStatistics(cr.maskDTMras, NbrRectangle(2*inp.filter_size+0.5,2*inp.filter_size+0.5,"MAP"), "MEAN")
masksmoothedDTMras = sa.ExtractByMask(DTMsmoothedras, inp.outputFolder + "mask.shp")

# Calculate residual topography
#------------------------------
print "Calculate residual topography"
outMinus = sa.Minus(masksmoothedDTMras, cr.maskDTMras)
outmin = arcpy.RasterToNumPyArray(outMinus)
outMinus.save(inp.outputFolder + 'mean')

# Apply REA threshold
#----------------
print "Apply REA threshold"
idx = outmin[:,:] > -3000
numb = outmin[idx]
otsu = filters.threshold_otsu(outmin[idx])
std1 = numpy.std(outmin[idx])
std3 = numpy.std(outmin[idx])*3
reclass = numpy.zeros(outmin.shape)
idx2 = outmin[:,:] > eval(inp.thresResRel)
reclass[idx2] = 1

print 'REAthresh = ' + str(eval(inp.thresResRel)) 

# Filter noise
#-------------
print "Filter noise"
reclass_dist = nd.distance_transform_edt(reclass == 1)
reclass_dist_max = nd.maximum_filter(reclass_dist, (3,3))
conn = inp.connmat
labeled, nr_objects = nd.label(reclass > 0, conn)
unique, area = numpy.unique(labeled, return_counts = True)
width = 2*(nd.measurements.mean(reclass_dist_max, labels = labeled, index = numpy.unique(labeled)))
width[0] = area[0]
length = numpy.divide(area, width)
lengthstd = numpy.std(length[area!=1])
lengthfup = numpy.percentile(length[area!=1],75)+ (numpy.percentile(length[area!=1],75)-numpy.percentile(length[area!=1],25))
length_rec = numpy.zeros(length.shape)
idx = length[:] <= eval(inp.thresLength)
reclasslength = numpy.ones(labeled.shape)
remove_length = idx[labeled]
reclasslength[remove_length] = 0

print 'lengththresh = ' + str(eval(inp.thresLength)) 

# Convert to GIS files
#---------------------
print "Convert to GIS files"
masksmoothedDTMras.save(inp.outputFolder + "masksmoothed" + ".tif")
lowerLeft = arcpy.Point(masksmoothedDTMras.extent.XMin,masksmoothedDTMras.extent.YMin)
cellSize = DTMsmoothedras.meanCellWidth
outMinus.save(inp.outputFolder + "restopmask" + ".tif")
reclassras = arcpy.NumPyArrayToRaster(reclass, lowerLeft, cellSize)
reclassras.save(inp.outputFolder + "reclass_std" + ".tif")
reclasslengthras = arcpy.NumPyArrayToRaster(reclasslength, lowerLeft, cellSize)
reclasslengthrasint = sa.Int(reclasslengthras)
reclasslengthrasint.save(inp.outputFolder + "reclasslength_std" + ".tif")

# Vectorize detection result
#---------------------------
print "Vectorising"
reclassthin = sa.Thin(inp.outputFolder + 'reclasslength_std' + '.tif', 'ZERO', 'NO_FILTER', 'SHARP', 1)
arcpy.RasterToPolyline_conversion(reclassthin, inp.outputFolder + 'thin' + '.shp')

# Integrate detection result with already existing network
#---------------------------------------------------------
print "Merging and integrating"
if inp.VHAfile is not "":
    print "Integrate detection result with already existing network"
    arcpy.Merge_management([inp.VHA, inp.outputFolder + 'thin' + '.shp'], inp.outputFolder + 'thin_merge' + '.shp')
    #10 Meters = max accuracy VHA 2de order (2.5)
    arcpy.Snap_edit(inp.outputFolder + 'thin_merge' + '.shp', [[inp.VHA, "EDGE", "3 Meters"]])
    arcpy.Integrate_management(inp.outputFolder + 'thin_merge' + '.shp', 2)
    field_names = [f.name for f in arcpy.ListFields(inp.outputFolder + 'thin_merge' + '.shp')]
    field_names.remove('FID')
    field_names.remove('Shape')
    field_names.remove('ARCID')
    arcpy.DeleteField_management(inp.outputFolder + 'thin_merge' + '.shp', field_names)
    arcpy.CalculateField_management(inp.outputFolder + 'thin_merge' + '.shp', "ARCID", "!FID!", "PYTHON_9.3")
else: arcpy.Copy_management(inp.outputFolder + 'thin' + '.shp', inp.outputFolder + 'thin_merge' + '.shp')

print "Finished"