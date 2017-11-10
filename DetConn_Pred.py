'''
Created in 2017
@author: Jennifer Roelens

'''

import DetConn_Input as inp
import numpy
import arcpy
from arcpy import sa
import angleSeg
import ExtractOverlapPoly as EP

'''
CODE
'''

# Make buffers
#-------------
polygons = inp.outputFolder + "all_lines_buffer" + ".shp"
arcpy.Buffer_analysis(inp.outputFolder  + "all_lines" + ".shp", polygons, str(inp.connBuffer) + " Meters")

# Clip polygons for mask
#-----------------------
polygons_clip = inp.outputFolder + "all_lines_buffer_clip" + ".shp"
arcpy.Clip_analysis(polygons, inp.inputStudyArea, polygons_clip)

# Create raster predictor variables
#--------------------------------
print 'Create raster variables'
arcpy.Curvature_3d(inp.outputFolder + "DTM" + ".tif", inp.outputFolder + "Curv", 1, inp.outputFolder + "ProfileCurv", inp.outputFolder + "PlanCurv")
FilledRas = sa.Fill(inp.outputFolder + "DTM" + ".tif")
FillRas = FilledRas - arcpy.Raster(inp.outputFolder + "DTM" + ".tif")
slopeRas = sa.Slope(inp.outputFolder + "DTM" + ".tif", 'DEGREE')
lowerLeft = arcpy.Point(slopeRas.extent.XMin, slopeRas.extent.YMin)
cellSize = slopeRas.meanCellWidth
slopeArr = arcpy.RasterToNumPyArray(slopeRas)
slopeRadArr = slopeArr/360*2*numpy.pi
planCurvArr = arcpy.RasterToNumPyArray(inp.outputFolder + "PlanCurv")
tanCurvArr = numpy.zeros(slopeArr.shape)
for i in range(0, slopeArr.shape[0]) :
    for j in range(0, slopeArr.shape[1]):
        if slopeArr[i,j] > -1:
            tanCurvArr[i,j] = numpy.multiply(planCurvArr[i,j],slopeRadArr[i,j])
tanCurvArrRas = arcpy.NumPyArrayToRaster(tanCurvArr, lowerLeft, cellSize)
tanCurvArrRas.save(inp.outputFolder + "TanCurv")
FillRas.save(inp.outputFolder + "Fill")

# Extract shapefile predictor variables
#--------------------------------------
print 'Create shape variables'
linesBuffer = arcpy.da.TableToNumPyArray(polygons, "*")  # @UndefinedVariable
linesBuffer_sort = numpy.sort(linesBuffer, order = 'ORIG_FID')  
length = linesBuffer_sort['LENGTH_3D']
dz = linesBuffer_sort['dz']
slope = numpy.tanh(dz/length)
arcpy.SpatialJoin_analysis(inp.outputFolder + "all_lines.shp", inp.outputFolder + "Ditches.shp", inp.outputFolder + "inter_line_ditch.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL")                 
arcpy.AddField_management(inp.outputFolder + "inter_line_ditch.shp", "dangle", "DOUBLE")
inter_line_ditch = arcpy.da.TableToNumPyArray(inp.outputFolder + "inter_line_ditch.shp", "*")  # @UndefinedVariable
inter_line_ditch_sor = inter_line_ditch

orientD = []
orientC = []
for i in range(0,len(inter_line_ditch_sor)):
    if numpy.round(inter_line_ditch_sor['START_X_1'][i], 2) == numpy.around(inter_line_ditch_sor['START_X'][i],2):
        p1s = (inter_line_ditch_sor['START_X_1'][i], inter_line_ditch_sor['START_Y_1'][i]) 
        p1e = (inter_line_ditch_sor['END_X_1'][i], inter_line_ditch_sor['END_Y_1'][i])
    else:
        p1s = (inter_line_ditch_sor['END_X_1'][i], inter_line_ditch_sor['END_Y_1'][i])
        p1e = (inter_line_ditch_sor['START_X_1'][i], inter_line_ditch_sor['START_Y_1'][i]) 
    p2s = (inter_line_ditch_sor['START_X'][i], inter_line_ditch_sor['START_Y'][i]) 
    p2e = (inter_line_ditch_sor['END_X'][i], inter_line_ditch_sor['END_Y'][i]) 
    orient2 = 180 + numpy.arctan2((p2e[1] - p2s[1]),(p2e[0] - p2s[0])) * (180 / numpy.pi)  
    v = (p1e[0] - p1s[0], p1e[1] - p1s[1])
    w = (p2e[0] - p2s[0], p2e[1] - p2s[1])
    da = angleSeg.inner_angle(v,w)
    if da > 90:
        da = 180 - da
    inter_line_ditch_sor['dangle'][i] = da
    orientC = numpy.append(orientC, orient2)

dangle = inter_line_ditch_sor['dangle']

# Extract all info from possible connections
#-------------------------------------------

print 'Extract information from possible connections'
profcurv_mean, profcurv_std, profcurv_var, profcurv_rng = EP.Extract(inp.outputFolder + "ProfileCurv", polygons_clip, inp.outputFolder,'ORIG_FID')
tancurv_mean, tancurv_std, tancurv_var, tancurv_rng = EP.Extract(inp.outputFolder + "TanCurv", polygons_clip, inp.outputFolder,'ORIG_FID')
fill_mean, fill_std, fill_var, fill_rng = EP.Extract(inp.outputFolder + "Fill", polygons_clip, inp.outputFolder,'ORIG_FID')
rea_mean, rea_std, rea_var, rea_rng = EP.Extract(inp.outputFolder + 'mean', polygons_clip, inp.outputFolder,'ORIG_FID')
int_mean, int_std, int_var, int_rng = EP.Extract(inp.inputFolder + "Intensityras", polygons_clip, inp.outputFolder,'ORIG_FID')
r_mean, r_std, r_var, r_rng = EP.Extract(inp.workspace + 'extract_1c1', polygons_clip, inp.outputFolder,'ORIG_FID')
g_mean, g_std, g_var, g_rng = EP.Extract(inp.workspace + 'extract_1c2', polygons_clip, inp.outputFolder,'ORIG_FID')
b_mean, b_std, b_var, b_rng = EP.Extract(inp.workspace + 'extract_1c3', polygons_clip, inp.outputFolder,'ORIG_FID')
predvar = numpy.column_stack([length, slope, dangle, orientC, profcurv_mean, profcurv_std, profcurv_var, profcurv_rng,tancurv_mean, tancurv_std, tancurv_var, tancurv_rng, fill_mean, fill_std, fill_var, fill_rng, rea_mean, rea_std, rea_var, rea_rng, int_mean, int_std, int_var, int_rng, r_mean, r_std, r_var, r_rng, g_mean, g_std, g_var, g_rng, b_mean, b_std, b_var, b_rng])
conn = linesBuffer['conn']
predconn = numpy.column_stack([predvar,conn])
varnames = ['length', 'slope', 'dangle', 'orient', 'profcurv_mean', 'profcurv_std', 'profcurv_var', 'profcurv_rng', 'tancurv_mean',
            'tancurv_std', 'tancurv_var', 'tancurv_rng', 'fill_mean', 'fill_std', 'fill_var', 'fill_rng', 'rea_mean',
            'rea_std', 'rea_var', 'rea_rng', 'int_mean', 'int_std', 'int_var', 'int_rng', 'r_mean', 'r_std', 'r_var',
            'r_rng', 'g_mean', 'g_std', 'g_var', 'g_rng', 'b_mean', 'b_std', 'b_var', 'b_rng']

# Save predictor variables
#-------------------------
numpy.savetxt(inp.outputFolder + 'predictors_conn.txt', predconn,  delimiter=',', header="length, slope, dangle, 'orient', profcurv_mean, profcurv_std, profcurv_var, profcurv_rng, tancurv_mean, tancurv_std, tancurv_var, tancurv_rng, fill_mean, fill_std, fill_var, fill_rng, rea_mean, rea_std, rea_var, rea_rng, int_mean, int_std, int_var, int_rng,r_mean, r_std, r_var, r_rng, g_mean, g_std, g_var, g_rng, b_mean, b_std, b_var, b_rng, conn", comments='')
numpy.savetxt(inp.outputFolder + 'predictors.txt', predvar,  delimiter=',', header="length, slope, dangle, 'orient', profcurv_mean, profcurv_std, profcurv_var, profcurv_rng, tancurv_mean, tancurv_std, tancurv_var, tancurv_rng, fill_mean, fill_std, fill_var, fill_rng, rea_mean, rea_std, rea_var, rea_rng, int_mean, int_std, int_var, int_rng, r_mean, r_std, r_var, r_rng, g_mean, g_std, g_var, g_rng, b_mean, b_std, b_var, b_rng", comments='')
numpy.savetxt(inp.outputFolder + 'conn.txt', conn, delimiter=',', comments='', header="conn")

print "Finished"