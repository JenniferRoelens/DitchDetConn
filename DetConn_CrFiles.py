'''
Created in 2017
@author: Jennifer Roelens
'''

import DetConn_Input as inp
import arcpy
from arcpy import sa
arcpy.env.overwriteOutput = True

"""
CODE
"""
print 'Creating files...'

# Clear/setting up workspace
arcpy.ClearWorkspaceCache_management()

# Create intensity raster
if inp.Intensityfile is "":
    print "Create intensity raster from LAS files"
    arcpy.LASToMultipoint_3d(inp.LiDARFolder, inp.def_geodatabase + "IntensityOrig", "1", "", "LAST_RETURNS", "INTENSITY")
    arcpy.env.snapRaster = inp.inputDTM
    inp.Intensityfile = "Intensity1"
    inp.inputIntensity = inp.inputFolder + inp.Intensityfile
    arcpy.PointToRaster_conversion(inp.def_geodatabase + "IntensityOrig", "Intensity", inp.inputIntensity,"","","1")

# Clip data for the study area
if inp.inputStudyArea is not "":
    print "Clip for study area"
    DTMras = sa.ExtractByMask(inp.inputDTM, inp.inputStudyArea)
    LandCoverras = sa.ExtractByMask(inp.inputLandCover, inp.inputStudyArea)
    arcpy.Intersect_analysis([inp.inputRoads, inp.inputStudyArea], inp.outputFolder + "Roads.shp")
    RGBras = sa.ExtractByMask(inp.inputRGB, inp.inputStudyArea)
    Intensityras = sa.ExtractByMask(inp.inputIntensity, inp.inputStudyArea)
    Intensityras.save(inp.inputFolder + "Intensityras")
    
else:
    DTMras = arcpy.Raster(inp.inputDTM)
    LandCoverras = arcpy.Raster(inp.inputLandCover)
    arcpy.CopyFeatures_management(inp.inputRoads, inp.outputFolder + "Roads.shp")
    RGBras = arcpy.Raster(inp.inputRGB)
    Intensityras = arcpy.Raster(inp.inputFolder + "Intensityras")
    
print "Create mask"

arcpy.RasterToPolygon_conversion(LandCoverras, inp.outputFolder + "BBK_poly.shp")
arcpy.MakeFeatureLayer_management(inp.outputFolder + "BBK_poly.shp", "lyr") 
arcpy.SelectLayerByAttribute_management("lyr", "NEW_Selection", "GRIDCODE = 2 OR GRIDCODE = 7 OR GRIDCODE = 10 OR GRIDCODE = 11 OR GRIDCODE = 12")
arcpy.CopyFeatures_management("lyr", inp.outputFolder + "BBK_mask.shp")
arcpy.Union_analysis([inp.outputFolder + "Roads.shp", inp.outputFolder + "BBK_mask.shp"], inp.outputFolder + "Wbn_BBK_mask.shp")
arcpy.Buffer_analysis(inp.outputFolder + "Wbn_BBK_mask.shp", inp.outputFolder + "mask_buffer.shp", "15 Meters")
arcpy.Dissolve_management(inp.outputFolder + "mask_buffer.shp", inp.outputFolder + "mask_buffer_dissolve.shp")
arcpy.Intersect_analysis([inp.outputFolder + "mask_buffer_dissolve.shp", inp.inputStudyArea], inp.outputFolder + "mask.shp")
maskDTMras = sa.ExtractByMask(DTMras, inp.outputFolder + "mask.shp")

print "Convert to GIS files"
DTMras.save(inp.outputFolder + "DTM" + ".tif")
maskDTMras.save(inp.outputFolder + "maskDTM" + ".tif")

print 'Finished creating files'