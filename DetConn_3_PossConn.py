'''
Created in 2017
@author: Jennifer Roelens

# Run this file after the detection and shifting stage
# Find possible connections
# IMPORTANT!!!! When finishing this script, field data on if the connection is true or false should be added!
# See read me file 
'''

import DetConn_Input as inp
import os
import numpy
import pandas as pd
import arcpy
arcpy.env.overwriteOutput = True
from timeit import default_timer as timer
import angleSeg
startscript = timer()

'''
CODE
'''
print "Finding possible connections..."

# Define ditches by merging ditch segments on orientation and length
#-------------------------------------------------------------------
arcpy.Intersect_analysis([inp.outputFolder + "Lines_up" + ".shp", inp.outputFolder + "Lines_up" + ".shp"], inp.outputFolder + "Lines_up_Inter" + ".shp", "ALL", "0 Meters", "POINT")
arcpy.AddField_management(inp.outputFolder + "Lines_up_Inter" + ".shp", "da", "DOUBLE")
linesupinter = arcpy.da.TableToNumPyArray(inp.outputFolder + "Lines_up_Inter" + ".shp", "*")  # @UndefinedVariable

for i in range(0,len(linesupinter)):
    if round(linesupinter["Shape"][i,0],2) == round(linesupinter["START_X"][i],2):
        start_x = linesupinter["START_X"][i]
        start_y = linesupinter["START_Y"][i]
        start_z = linesupinter["START_Z"][i]
        linesupinter["START_X"][i] = linesupinter["END_X"][i]
        linesupinter["END_X"][i] = start_x
        linesupinter["START_Y"][i] = linesupinter["END_Y"][i]
        linesupinter["END_Y"][i] = start_y
        linesupinter["START_Z"][i] = linesupinter["END_Z"][i]
        linesupinter["END_Z"][i] = start_z
        
for i in range(0,len(linesupinter)):
    if round(linesupinter["Shape"][i,0],2) == round(linesupinter["START_X_1"][i],2):
        start_x_1 = linesupinter["START_X_1"][i]
        start_y_1 = linesupinter["START_Y_1"][i]
        start_z_1 = linesupinter["START_Z_1"][i]
        linesupinter["START_X_1"][i] = linesupinter["END_X_1"][i]
        linesupinter["END_X_1"][i] = start_x_1
        linesupinter["START_Y_1"][i] = linesupinter["END_Y_1"][i]
        linesupinter["END_Y_1"][i] = start_y_1
        linesupinter["START_Z_1"][i] = linesupinter["END_Z_1"][i]
        linesupinter["END_Z_1"][i] = start_z_1
       
for i in range(0,len(linesupinter)):
    p1s = (linesupinter['START_X'][i], linesupinter['START_Y'][i]) 
    p1e = (linesupinter['END_X'][i], linesupinter['END_Y'][i]) 
    v = (p1e[0] - p1s[0], p1e[1] - p1s[1])
    p2s = (linesupinter['START_X_1'][i], linesupinter['START_Y_1'][i]) 
    p2e = (linesupinter['END_X_1'][i], linesupinter['END_Y_1'][i]) 
    w = (p2e[0] - p2s[0], p2e[1] - p2s[1])
    if v == w:linesupinter['da'][i] = -1
    else:
        linesupinter['da'][i] = angleSeg.inner_angle(v,w)
        
linesupinter_new = linesupinter[linesupinter['da'] != -1]
linesupinter_new = linesupinter_new[linesupinter_new['da'] < 135]
linesupinter_new = linesupinter_new[linesupinter_new['LENGTH_3D'] > 5]
linesupinter_new = linesupinter_new[linesupinter_new['LENGTH_3_1'] > 5]

arcpy.da.NumPyArrayToFeatureClass(linesupinter_new, inp.outputFolder + "Lines_up_Inter_new" + ".shp", "Shape", arcpy.Describe(inp.outputFolder + "Lines_up" + ".shp").spatialReference)  # @UndefinedVariable    
arcpy.UnsplitLine_management(inp.outputFolder + "Lines_up" + ".shp", inp.outputFolder + "Lines_unsplit" + ".shp")
arcpy.SplitLineAtPoint_management(inp.outputFolder + "Lines_unsplit" + ".shp", inp.outputFolder + "Lines_up_Inter_new" + ".shp", inp.outputFolder + "Ditches" + ".shp")

# Set line direction governed by elevation difference
#----------------------------------------------------

arcpy.AddGeometryAttributes_management (inp.outputFolder + "Ditches" + ".shp", "LENGTH", "Meters", "SQUARE_METERS", "31370")
arcpy.MakeTableView_management(inp.outputFolder + "Ditches" + ".shp", "tempTableView")
arcpy.SelectLayerByAttribute_management("tempTableView", "NEW_SELECTION", "LENGTH = 0")
if int(arcpy.GetCount_management("tempTableView").getOutput(0)) > 0:
    arcpy.DeleteRows_management("tempTableView")
arcpy.AddGeometryAttributes_management (inp.outputFolder + "Ditches" + ".shp", "LINE_START_MID_END", "Meters", "SQUARE_METERS", "31370")
arcpy.AddField_management(inp.outputFolder + "Ditches"  + ".shp", "dz", "DOUBLE")
arcpy.CalculateField_management(inp.outputFolder + "Ditches"  + ".shp", "dz", "!START_Z! - !END_Z!", "PYTHON_9.3")
arcpy.MakeFeatureLayer_management(inp.outputFolder + "Ditches"  + ".shp", "lyrLines")
arcpy.SelectLayerByAttribute_management("lyrLines", "NEW_SELECTION", "dz < 0") 
arcpy.FlipLine_edit("lyrLines")
arcpy.SelectLayerByAttribute_management("lyrLines", "CLEAR_SELECTION")

# Create sinks based on ditch directions with an elevation difference of more then 0.1m that do not intersect with more than one ditch
#-------------------------------------------------------------------------------------------------------------------------------------
# Keep lowest point in the network as a sink --> First defined outlet
#-------------------------------------------------------------------
arcpy.FeatureVerticesToPoints_management(inp.outputFolder + "Ditches" + ".shp", inp.outputFolder + "Ditches_end" + ".shp", "END")
arcpy.SpatialJoin_analysis(inp.outputFolder + "Ditches_end" + ".shp", inp.outputFolder + "Ditches" + ".shp", inp.outputFolder + "SpatJoin" + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT")
arcpy.JoinField_management(inp.outputFolder + "Ditches_end" + ".shp", "FID", inp.outputFolder + "SpatJoin" + ".shp", "TARGET_FID", "Join_Count")
arcpy.AddGeometryAttributes_management(inp.outputFolder + "Ditches_end" + ".shp", "POINT_X_Y_Z_M")
data = arcpy.da.TableToNumPyArray(inp.outputFolder + "Ditches_end" + ".shp", "*")  # @UndefinedVariable
sqlExpr = "POINT_Z" + " = " + str(min(data['POINT_Z']))
arcpy.MakeFeatureLayer_management(inp.outputFolder + "Ditches_end" + ".shp", "temp")
arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "(dz <= -0.1 Or dz >= 0.1) And Join_Count = 1")
arcpy.SelectLayerByAttribute_management("temp", "ADD_TO_SELECTION", sqlExpr)
arcpy.CopyFeatures_management("temp", inp.outputFolder + "sinks" + ".shp")
arcpy.DeleteIdentical_management(inp.outputFolder + "sinks" + ".shp", ['Shape'])

# Create geometric network
#-------------------------
arcpy.CreateFeatureDataset_management(inp.def_geodatabase, "geodataNEW")
arcpy.FeatureClassToFeatureClass_conversion(inp.outputFolder + "Ditches" + ".shp", inp.def_geodatabase + "geodataNEW", "Ditches")
arcpy.CreateGeometricNetwork_management(inp.def_geodatabase + "geodataNEW", 'geodata_Net', "Ditches" + " SIMPLE_EDGE NO")
arcpy.SetFlowDirection_management(inp.def_geodatabase + "geodataNEW\\geodata_Net", "WITH_DIGITIZED_DIRECTION")

# Add geometric variables to points
#----------------------------------
arcpy.FeatureVerticesToPoints_management(inp.outputFolder + "Ditches" + ".shp", inp.outputFolder + "Ditches_vertBOTH" + ".shp", "BOTH_ENDS")
arcpy.AddGeometryAttributes_management(inp.outputFolder + "Ditches_vertBOTH" + ".shp", "POINT_X_Y_Z_M")

# Create folder for tracing
#--------------------------
newpath = inp.outputFolder + "Tracing" 
if not os.path.exists(newpath):
    os.makedirs(newpath)
traceFolder = newpath + "\\"

# Tracing the sinks upstream to find possible connections
#--------------------------------------------------------
possconnfiles = []    
sinks = arcpy.da.TableToNumPyArray(inp.outputFolder + "sinks" + ".shp", "*")  # @UndefinedVariable
for i in range(0,len(sinks)):
    print str(i)
    arcpy.MakeFeatureLayer_management(inp.outputFolder + "sinks" + ".shp", "temp")
    arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "FID = " + str(i))
    arcpy.CopyFeatures_management("temp", traceFolder + "sink" + str(i) + ".shp" )
    arcpy.TraceGeometricNetwork_management(inp.def_geodatabase + "geodataNEW\\geodata_Net", "Network_from_Main", traceFolder + "sink" + str(i) + ".shp", "FIND_CONNECTED")
    arcpy.CopyFeatures_management((arcpy.SelectData_management("Network_from_Main", "Ditches").getOutput(0)), traceFolder + "traced_lines_poss" + str(i) + ".shp")
    arcpy.CopyFeatures_management((arcpy.SelectData_management("Network_from_Main","geodata_Net" + "_Junctions").getOutput(0)), traceFolder + "traced_junctions_poss" + str(i) +".shp")
    arcpy.SymDiff_analysis(inp.outputFolder + "Ditches" + ".shp", traceFolder + "traced_lines_poss" + str(i) + ".shp", traceFolder + "symdiff_lines_poss" + str(i) + ".shp")
    arcpy.SymDiff_analysis(inp.outputFolder + "Ditches_vertBOTH" + ".shp", traceFolder + "traced_junctions_poss" + str(i) + ".shp", traceFolder + "symdiff_junc_poss" + str(i) + ".shp")
    arcpy.DeleteIdentical_management(traceFolder + "symdiff_junc_poss" + str(i) + ".shp", ["Shape"])    
    #arcpy.RemoveSpatialIndex_management(traceFolder + "symdiff_junc_poss" + str(i) + ".shp")
    arcpy.AddSpatialIndex_management(traceFolder + "symdiff_junc_poss" + str(i) + ".shp")
    # get endpoints
    arcpy.SpatialJoin_analysis(traceFolder + "traced_junctions_poss" + str(i) + ".shp", traceFolder + "traced_lines_poss" + str(i) + ".shp", traceFolder + "junc_poss" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT")    
    arcpy.MakeFeatureLayer_management(traceFolder + "junc_poss" + str(i) + ".shp", "temp")
    arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "Join_Count = 1")
    arcpy.CopyFeatures_management("temp", traceFolder + "end_junctions" + str(i) + ".shp")
    arcpy.Intersect_analysis([traceFolder + "end_junctions" + str(i) + ".shp", inp.outputFolder + "Ditches_vertBOTH" + ".shp"], traceFolder + "end_points" + str(i) + ".shp", "ALL", "0.01 Meters")
    arcpy.DeleteIdentical_management(traceFolder + "end_points" + str(i) + ".shp", ["Shape"])
    arcpy.GenerateNearTable_analysis(traceFolder + "end_points" + str(i) + ".shp", traceFolder + "symdiff_junc_poss" + str(i) + ".shp", traceFolder + "neartable" + str(i), "100 Meters", "LOCATION", "ANGLE", "ALL", 5)
    # get near points
    nrtable = arcpy.da.TableToNumPyArray(traceFolder + "neartable" + str(i), "*")  # @UndefinedVariable
    frompoints = arcpy.da.TableToNumPyArray(traceFolder + "end_points" + str(i) + ".shp", "*")  # @UndefinedVariable
    nearpoints = arcpy.da.TableToNumPyArray(traceFolder + "symdiff_junc_poss" + str(i) + ".shp", "*")  # @UndefinedVariable
    nrtablez = nrtable[(nearpoints['POINT_Z'][nrtable['NEAR_FID']] - frompoints['POINT_Z'][nrtable['IN_FID']])  > -0.1] 
    # delete connections to same ditch, keep closest
    val = numpy.stack([nrtablez['Rowid'],nearpoints['ORIG_FID'][nrtablez['NEAR_FID']], nrtablez['IN_FID'], nrtablez['NEAR_DIST']], axis = 1)
    sortval = val[val[:,3].argsort()[::1]]
    df = pd.DataFrame({'A': sortval[:,0], 'B': sortval[:,1], 'C': sortval[:,2], 'D': sortval[:,3]})
    df2 = df.drop_duplicates(subset = ['B','C'])
    uniquerow = df2.as_matrix(columns=None)
    nrtableunique = nrtablez[[x in uniquerow[:,0].astype(int) for x in nrtablez['Rowid']]]
    outlet = arcpy.da.TableToNumPyArray(traceFolder + "sink" + str(i) + ".shp","*")  # @UndefinedVariable
    nrtableunique = nrtableunique[frompoints['POINT_X'][nrtableunique['IN_FID']] != outlet['POINT_X']]
    if len(nrtableunique) != 0:
        frompoints_line = frompoints[nrtableunique['IN_FID']][['POINT_X', 'POINT_Y', 'POINT_Z', 'FID_Ditche']]
        nearpoints_line = nearpoints[nrtableunique['NEAR_FID']][['POINT_X', 'POINT_Y', 'POINT_Z', 'FID_Ditche']]
        frompoints_line['FID_Ditche'] = range(len(frompoints_line))
        nearpoints_line['FID_Ditche'] = range(len(frompoints_line))
        points_line = numpy.append(frompoints_line,nearpoints_line)
        points_line.dtype.names = ('POINT_X', 'POINT_Y', 'POINT_Z', 'Conn_FID')
        arcpy.da.NumPyArrayToFeatureClass(points_line, traceFolder + "poss_points" + str(i) + ".shp", ("POINT_X", "POINT_Y", "POINT_Z"), arcpy.Describe(inp.outputFolder + "Lines_up" + ".shp").spatialReference)  # @UndefinedVariable
        arcpy.PointsToLine_management(traceFolder + "poss_points" + str(i) + ".shp", traceFolder + "poss" + str(i) + ".shp", "Conn_FID")
        arcpy.SpatialJoin_analysis(traceFolder + "poss" + str(i) + ".shp", inp.outputFolder + "Ditches" + ".shp", traceFolder + "poss_jc" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT")
        arcpy.MakeFeatureLayer_management(traceFolder + "poss_jc" + str(i) + ".shp", "temp")
        arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "Join_Count = 2")
        arcpy.CopyFeatures_management("temp", traceFolder + "poss_jc2_" + str(i) + ".shp")
        arcpy.SpatialJoin_analysis(traceFolder + "poss_jc2_" + str(i) + ".shp", inp.inputStudyArea, traceFolder + "poss_jc3_" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CROSSED_BY_THE_OUTLINE_OF" )
        arcpy.MakeFeatureLayer_management(traceFolder + "poss_jc3_" + str(i) + ".shp", "temp2")
        arcpy.SelectLayerByAttribute_management("temp2", "NEW_SELECTION", "Join_Cou_1 = 0")
        arcpy.CopyFeatures_management("temp2", traceFolder + "lines" + str(i) + ".shp")
        possconnfiles.append(traceFolder + "lines" + str(i) + ".shp")

# Merge all the found possible connected segments and delete identical
#---------------------------------------------------------------------
arcpy.Merge_management(possconnfiles, inp.outputFolder  + "all_lines" + ".shp")
arcpy.DeleteIdentical_management(inp.outputFolder  + "all_lines" + ".shp", ["Shape"])

# Update the attribute columns
#-----------------------------
arcpy.AddGeometryAttributes_management(inp.outputFolder + "all_lines" + ".shp", ["LENGTH_3D", "LINE_START_MID_END"])
arcpy.AddField_management(inp.outputFolder + "all_lines" + ".shp", "dz", "DOUBLE")
arcpy.CalculateField_management(inp.outputFolder  + "all_lines" + ".shp", "dz", "!END_Z! - !START_Z!", "PYTHON")
arcpy.AddField_management(inp.outputFolder + "all_lines" + ".shp", "conn", "DOUBLE")

####################################################
# ADD FIELD DATA IN CONN COLUMN [1 = True, 0 = False
####################################################

print "Finished"