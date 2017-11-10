'''
Created in 2017
@author: Jennifer Roelens

'''

"""
Connectivity model settings
---------------------------
form = True or False
        If you manually want to put in the model, form = True and adapt formula and cut-off value in line 188 and 189
        If you want to extract it from the previous script, form = False
"""
form = True

import DetConn_Input as inp
if form != True:
    import DetConn_4_ProbModel as prob
    from DetConn_4_ProbModel import result as pbm
import os, shutil
import numpy
import pandas as pd
import arcpy
import angleSeg
import ExtractOverlapPoly as EP

'''
CODE
'''

if form != True:
    print pbm.summary()
    print prob.varrf
    print prob.ind

# Add new folder
#---------------
newpath = inp.outputFolder + "Tracing2_circle3_033_5" 
if not os.path.exists(newpath):
    os.makedirs(newpath)
else: 
    shutil.rmtree(newpath)
    os.makedirs(newpath)
traceFolder = newpath + "\\"

# Initialize first loop
#----------------------
h = 0
arcpy.CopyFeatures_management(inp.outputFolder + "Ditches_end" + ".shp", traceFolder + "sinks" + str(h) + ".shp")
arcpy.DeleteIdentical_management(traceFolder + "sinks" + str(h) + ".shp", ["Shape"])
#arcpy.CopyFeatures_management(inp.outputFolder + "sinks" + ".shp", traceFolder + "sinks" + str(h) + ".shp")
sinks = arcpy.da.TableToNumPyArray(traceFolder + "sinks" + str(h) + ".shp", "*")  # @UndefinedVariable
nrsinks = len(sinks)

i = 0
arcpy.CopyFeatures_management(inp.outputFolder + "Ditches" + ".shp", traceFolder + "Ditches" + str(h) + "_" + str(i) + ".shp")
arcpy.CopyFeatures_management(inp.outputFolder + "Ditches_vertBOTH" + ".shp", traceFolder + "Ditches_vertBOTH" + str(h) + "_" + str(i) + ".shp")

# Loop
#-----
while nrsinks != 0:
    print "nr_sinks = " + str(nrsinks)
    sqlExpr = "POINT_Z" + " = " + str(min(sinks['POINT_Z']))
    arcpy.MakeFeatureLayer_management(traceFolder + "sinks" + str(h) + ".shp", "temp")
    arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", sqlExpr)
    arcpy.CopyFeatures_management("temp", traceFolder + "outlet" + str(h) + ".shp")
    nrendpoints = 1
    i = 0
    while nrendpoints != 0:
        print "outlet = " + str(h) + " & loop = " + str(i) 
        # create new geometric network
        #-----------------------------
        arcpy.CreateFeatureDataset_management(inp.def_geodatabase, "geodataNEW" + str(h) + "_" + str(i))
        arcpy.FeatureClassToFeatureClass_conversion(traceFolder + "Ditches" + str(h) + "_" + str(i) + ".shp", inp.def_geodatabase + "geodataNEW" + str(h) + "_" + str(i), "Ditches" + str(h) + "_" + str(i))
        arcpy.CreateGeometricNetwork_management(inp.def_geodatabase + "geodataNEW" + str(h) + "_" + str(i), 'geodata_Net_' + str(h) + "_" + str(i), "Ditches" + str(h) + "_" + str(i) + " SIMPLE_EDGE NO")
        arcpy.SetFlowDirection_management(inp.def_geodatabase + "geodataNEW" + str(h) + "_" + str(i) + "\\geodata_Net_" + str(h) + "_" + str(i), "WITH_DIGITIZED_DIRECTION")
        # trace geometric network
        #------------------------
        arcpy.TraceGeometricNetwork_management(inp.def_geodatabase + "geodataNEW" + str(h) + "_" + str(i) + "\\geodata_Net_" + str(h) + "_" + str(i), "Network_from_Main" + str(h) + "_" + str(i), traceFolder + "outlet" + str(h) + ".shp", "FIND_CONNECTED")
        # Find endpoints
        #---------------
        arcpy.CopyFeatures_management((arcpy.SelectData_management("Network_from_Main" + str(h) + "_" + str(i), "Ditches" + str(h) + "_" + str(i)).getOutput(0)), traceFolder + "traced_lines_poss" + str(h) + "_" + str(i) + ".shp")
        arcpy.CopyFeatures_management((arcpy.SelectData_management("Network_from_Main" + str(h) + "_" + str(i), "geodata_Net_" + str(h) + "_" + str(i) + "_Junctions").getOutput(0)), traceFolder + "traced_junctions_poss" + str(h) + "_" + str(i) +".shp")
        arcpy.SymDiff_analysis(traceFolder + "Ditches" + str(h) + "_" + str(i) + ".shp", traceFolder + "traced_lines_poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "symdiff_lines_poss" + str(h) + "_" + str(i) + ".shp")
        arcpy.SymDiff_analysis(traceFolder + "Ditches_vertBOTH" + str(h) + "_" + str(i) + ".shp", traceFolder + "traced_junctions_poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "symdiff_junc_poss" + str(h) + "_" + str(i) + ".shp")
        arcpy.DeleteIdentical_management(traceFolder + "symdiff_junc_poss" + str(h) + "_" + str(i) + ".shp", ["Shape"])
        arcpy.AddSpatialIndex_management(traceFolder + "symdiff_junc_poss" + str(h) + "_" + str(i) + ".shp")
        arcpy.FeatureVerticesToPoints_management(traceFolder + "traced_lines_poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "junc_poss" + str(h) + "_" + str(i) + ".shp", 'DANGLE')
        if i == 0:
            arcpy.CopyFeatures_management(traceFolder + "junc_poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "end_junctions" + str(h) + "_" + str(i) + ".shp")
            arcpy.SpatialJoin_analysis(traceFolder + "end_junctions" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditches_vertBOTH" + str(h) + "_" + str(i) + ".shp", traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL")
            arcpy.DeleteIdentical_management(traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp", ["Shape"])
            arcpy.CopyFeatures_management(traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp", traceFolder + "searched_end_points" + str(h) + "_" + str(i) + ".shp")   
        else:
            arcpy.CopyFeatures_management(traceFolder + "junc_poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "end_junctions_prelim" + str(h) + "_" + str(i) + ".shp")
            arcpy.SpatialJoin_analysis(traceFolder + "end_junctions_prelim" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditches_vertBOTH" + str(h) + "_" + str(i) + ".shp", traceFolder + "end_points_prelim" + str(h) + "_" + str(i) + ".shp", "JOIN_ONE_TO_ONE","KEEP_ALL")
            arcpy.SpatialJoin_analysis(traceFolder + "end_points_prelim" + str(h) + "_" + str(i) + ".shp", traceFolder + "searched_end_points" + str(h) + "_" + str(i-1) + ".shp", traceFolder + "spatjoinend" + str(h) + "_" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL")
            arcpy.MakeFeatureLayer_management(traceFolder + "spatjoinend" + str(h) + "_" + str(i) + ".shp", "temp")
            arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "Join_Cou_1 = 0")
            arcpy.CopyFeatures_management("temp", traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp")
            arcpy.DeleteIdentical_management(traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp", ["Shape"])
            arcpy.Merge_management([traceFolder + "searched_end_points" + str(h) + "_" + str(i-1) + ".shp", traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp"], traceFolder + "searched_end_points" + str(h) + "_" + str(i) + ".shp")
        # Find possible connections
        #--------------------------
        arcpy.GenerateNearTable_analysis(traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp", traceFolder + "symdiff_junc_poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "neartable" + str(h) + "_" + str(i), "100 Meters", "LOCATION", "ANGLE", "ALL", 5)
        nrtable = arcpy.da.TableToNumPyArray(traceFolder + "neartable" + str(h) + "_" + str(i), "*")  # @UndefinedVariable
        frompoints = arcpy.da.TableToNumPyArray(traceFolder + "end_points" + str(h) + "_" + str(i) + ".shp", "*")  # @UndefinedVariable
        nearpoints = arcpy.da.TableToNumPyArray(traceFolder + "symdiff_junc_poss" + str(h) + "_" + str(i) + ".shp", "*")  # @UndefinedVariable
        nrtablez = nrtable[(nearpoints['POINT_Z'][nrtable['NEAR_FID']] - frompoints['POINT_Z'][nrtable['IN_FID']])  > -0.1] 
        val = numpy.stack([nrtablez['Rowid'],nearpoints['ORIG_FID'][nrtablez['NEAR_FID']], nrtablez['IN_FID'], nrtablez['NEAR_DIST']], axis = 1)
        sortval = val[val[:,3].argsort()[::1]]
        df = pd.DataFrame({'A': sortval[:,0], 'B': sortval[:,1], 'C': sortval[:,2], 'D': sortval[:,3]})
        df2 = df.drop_duplicates(subset = ['B','C'])
        uniquerow = df2.as_matrix(columns=None)
        nrtableunique = nrtablez[[x in uniquerow[:,0].astype(int) for x in nrtablez['Rowid']]]
        if i == 0:
            outlet = arcpy.da.TableToNumPyArray(traceFolder + "outlet" + str(h) + ".shp","*")  # @UndefinedVariable
            nrtableunique = nrtableunique[frompoints['POINT_X'][nrtableunique['IN_FID']] != outlet['POINT_X']]
        if len(nrtableunique) != 0:
            frompoints_line = frompoints[nrtableunique['IN_FID']][['POINT_X', 'POINT_Y', 'POINT_Z', 'ORIG_FID']]
            nearpoints_line = nearpoints[nrtableunique['NEAR_FID']][['POINT_X', 'POINT_Y', 'POINT_Z', 'ORIG_FID']]
            frompoints_line['ORIG_FID'] = range(len(frompoints_line))
            nearpoints_line['ORIG_FID'] = range(len(frompoints_line))
            points_line = numpy.append(frompoints_line, nearpoints_line)
            points_line.dtype.names = ('POINT_X', 'POINT_Y', 'POINT_Z', 'Conn_FID')
            arcpy.da.NumPyArrayToFeatureClass(points_line, traceFolder + "poss_points" + str(h) + "_" + str(i) + ".shp", ("POINT_X", "POINT_Y", "POINT_Z"), arcpy.Describe(inp.outputFolder + "Lines_up" + ".shp").spatialReference)  # @UndefinedVariable
            arcpy.PointsToLine_management(traceFolder + "poss_points" + str(h) + "_" + str(i) + ".shp", traceFolder + "poss" + str(h) + "_" + str(i) + ".shp", "Conn_FID")
            arcpy.SpatialJoin_analysis(traceFolder + "poss" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditches" + str(h) + "_" + str(i) + ".shp", traceFolder + "poss_jc" + str(h) + "_" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT" )
            arcpy.MakeFeatureLayer_management(traceFolder + "poss_jc" + str(h) + "_" + str(i) + ".shp", "temp")
            arcpy.SelectLayerByAttribute_management("temp", "NEW_SELECTION", "Join_Count = 2")
            arcpy.CopyFeatures_management("temp", traceFolder + "poss_jc2_" + str(h) + "_" + str(i) + ".shp")
            arcpy.SpatialJoin_analysis(traceFolder + "poss_jc2_" + str(h) + "_" + str(i) + ".shp", inp.inputStudyArea, traceFolder + "poss_jc3_" + str(h) + "_" + str(i) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "CROSSED_BY_THE_OUTLINE_OF" )
            arcpy.MakeFeatureLayer_management(traceFolder + "poss_jc3_" + str(h) + "_" + str(i) + ".shp", "temp2")
            arcpy.SelectLayerByAttribute_management("temp2", "NEW_SELECTION", "Join_Cou_1 = 0")
            arcpy.CopyFeatures_management("temp2", traceFolder + "lines" + str(h) + "_" + str(i) + ".shp")
            arcpy.AddGeometryAttributes_management(traceFolder + "lines" + str(h) + "_" + str(i) + ".shp", ["LENGTH_3D", "LINE_START_MID_END"])
            arcpy.AddField_management(traceFolder + "lines" + str(h) + "_" + str(i) + ".shp", "dz", "DOUBLE")
            arcpy.CalculateField_management(traceFolder + "lines" + str(h) + "_" + str(i) + ".shp", "dz", "!END_Z! - !START_Z!", "PYTHON")
            lines = arcpy.da.TableToNumPyArray(traceFolder + "lines" + str(h) + "_" + str(i) + ".shp", "*")  # @UndefinedVariable
            if len(lines) != 0: 
            # Get parameters
            #---------------
                polygons = traceFolder + "lines_buffer" + str(h) + "_" + str(i) + ".shp"
                arcpy.Buffer_analysis(traceFolder + "lines" + str(h) + "_" + str(i) + ".shp", polygons, str(inp.connBuffer) + " Meters")
                polygons_clip = traceFolder + "lines_buffer_clip" + str(h) + "_" + str(i) + ".shp"
                arcpy.Clip_analysis(polygons, inp.inputStudyArea, polygons_clip)      
                # Extract predictor variables
                #----------------------------
                print 'Extract information'
                linesBuffer = arcpy.da.TableToNumPyArray(polygons, "*")  # @UndefinedVariable
                linesBuffer_sort = numpy.sort(linesBuffer, order = 'ORIG_FID')
                length = linesBuffer_sort['LENGTH_3D']
                dz = linesBuffer_sort['dz']
                slope = numpy.tanh(dz/length)
                frompoints2 = frompoints[nrtableunique['IN_FID'][lines['Conn_FID']]]
                nearpoints2 = nearpoints[nrtableunique['NEAR_FID'][lines['Conn_FID']]]
                dangle = []
                orientC = []
                for j in range(0,len(linesBuffer_sort)):
                    if numpy.round(frompoints2['START_X'][j],2) == numpy.round(frompoints2['Shape'][j][0],2):
                        p1s = (frompoints2['START_X'][j], frompoints2['START_Y'][j]) 
                        p1e = (frompoints2['END_X'][j], frompoints2['END_Y'][j])
                    else:
                        p1s = (frompoints2['END_X'][j], frompoints2['END_Y'][j]) 
                        p1e = (frompoints2['START_X'][j], frompoints2['START_Y'][j])
                    v = (p1e[0] - p1s[0], p1e[1] - p1s[1])
                    p2s = (frompoints2['Shape'][j][0], frompoints2['Shape'][j][1])   
                    p2e = (nearpoints2['Shape'][j][0], nearpoints2['Shape'][j][1])
                    w = (p2e[0] - p2s[0], p2e[1] - p2s[1])
                    dangle1 = angleSeg.inner_angle(v,w)
                    if dangle1 >90:
                        dangle1 = 180 - dangle1
                    dangle = numpy.append(dangle, dangle1)
                    orient2 = 180 + numpy.arctan2((p2e[1] - p2s[1]),(p2e[0] - p2s[0])) * (180 / numpy.pi)  
                    orientC = numpy.append(orientC, orient2)
                profcurv_mean, profcurv_std, profcurv_var, profcurv_rng = EP.Extract(inp.outputFolder + "ProfileCurv", polygons_clip, inp.outputFolder,'ORIG_FID')
                tancurv_mean, tancurv_std, tancurv_var, tancurv_rng = EP.Extract(inp.outputFolder + "TanCurv", polygons_clip, inp.outputFolder,'ORIG_FID')
                fill_mean, fill_std, fill_var, fill_rng = EP.Extract(inp.outputFolder + "Fill", polygons_clip, inp.outputFolder,'ORIG_FID')
                rea_mean, rea_std, rea_var, rea_rng = EP.Extract(inp.outputFolder + 'mean', polygons_clip, inp.outputFolder,'ORIG_FID')
                int_mean, int_std, int_var, int_rng = EP.Extract(inp.inputFolder + "Intensityras", polygons_clip, inp.outputFolder,'ORIG_FID')
                r_mean, r_std, r_var, r_rng = EP.Extract(inp.workspace + 'extract_1c1', polygons_clip, inp.outputFolder,'ORIG_FID')
                g_mean, g_std, g_var, g_rng = EP.Extract(inp.workspace + 'extract_1c2', polygons_clip, inp.outputFolder,'ORIG_FID')
                b_mean, b_std, b_var, b_rng = EP.Extract(inp.workspace + 'extract_1c3', polygons_clip, inp.outputFolder,'ORIG_FID')
                predvar = numpy.column_stack([length, slope, dangle, orientC, profcurv_mean, profcurv_std, profcurv_var, profcurv_rng, tancurv_mean, tancurv_std, tancurv_var, tancurv_rng, fill_mean, fill_std, fill_var, fill_rng, rea_mean, rea_std, rea_var, rea_rng, int_mean, int_std, int_var, int_rng, r_mean, r_std, r_var, r_rng, g_mean, g_std, g_var, g_rng, b_mean, b_std, b_var, b_rng])
                # Run logistic model
                #-------------------
                if form == True:
                    probabilities = (numpy.exp((-0.2657 * predvar[:,2]) + (0.4445 * predvar[:,4]) + (28.5713 * predvar[:,12]))) / (1 + (numpy.exp((-0.2657 * predvar[:,2]) + (0.4445 * predvar[:,4]) + (28.5713 * predvar[:,12]))))
                    cut_off = 0.33
                else:
                    probabilities = pbm.predict(predvar[:,prob.ind])
                    cut_off = prob.cut_off
                numpy.savetxt(traceFolder + "probabilities" + str(h) + "_" + str(i) + ".txt", probabilities)
                conn = probabilities > cut_off                 
                # Get true connections
                #---------------------
                unique, un_idx, un_inv, un_cnt = numpy.unique(linesBuffer['START_X'], return_counts = True, return_index = True, return_inverse = True)
                lines_id = []
                for m in range(0, len(linesBuffer['START_X'])):
                    if un_cnt[un_inv[m]] == 0:
                        if probabilities[m] >= cut_off:
                            lines_id = numpy.append(lines_id, linesBuffer[m]['ORIG_FID'])
                    else:
                        probabilities_sub = probabilities[un_inv == un_inv[m]]
                        conn_sub = conn[un_inv == un_inv[m]]
                        prob_max = numpy.max(probabilities_sub)
                        if probabilities[probabilities == prob_max] >= cut_off:
                            lines_id = numpy.append(lines_id, linesBuffer[probabilities == prob_max]['ORIG_FID'])
                lines_id = numpy.unique(lines_id)
                lines_id.astype(int)
                if len(lines_id) != 0:
                    arcpy.MakeFeatureLayer_management(traceFolder + "lines" + str(h) + "_" + str(i) + ".shp", "temp3")
                    for k in lines_id:
                        sqlExpr = "FID = " + str(k)
                        arcpy.SelectLayerByAttribute_management("temp3", "ADD_TO_SELECTION", sqlExpr)
                    arcpy.CopyFeatures_management("temp3", traceFolder + "connection" + str(h) + "_" + str(i) + ".shp")
                    # Add to ditches database
                    #------------------------
                    arcpy.Merge_management([traceFolder + "Ditches" + str(h) + "_" + str(i) + ".shp", traceFolder + "connection" + str(h) + "_" + str(i) + ".shp"], traceFolder + "Ditch_conn" + str(h) + "_" + str(i) + ".shp")
                    # Define ditches again based on orientation and length
                    #-----------------------------------------------------
                    arcpy.Intersect_analysis([traceFolder + "Ditch_conn" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditch_conn" + str(h) + "_" + str(i) + ".shp"], traceFolder + "Ditch_conn_inter" + str(h) + "_" + str(i) + ".shp", "ALL", "0 Meters", "POINT")
                    arcpy.AddField_management(traceFolder + "Ditch_conn_inter" + str(h) + "_" + str(i) + ".shp", "da", "DOUBLE")
                    ditchconninter = arcpy.da.TableToNumPyArray(traceFolder + "Ditch_conn_inter" + str(h) + "_" + str(i) + ".shp", "*")  # @UndefinedVariable
                    for l in range(0,len(ditchconninter)):
                        if round(ditchconninter["Shape"][i,0],2) == round(ditchconninter["START_X"][l],2):
                            start_x = ditchconninter["START_X"][l]
                            start_y = ditchconninter["START_Y"][l]
                            start_z = ditchconninter["START_Z"][l]
                            ditchconninter["START_X"][l] = ditchconninter["END_X"][l]
                            ditchconninter["END_X"][l] = start_x
                            ditchconninter["START_Y"][l] = ditchconninter["END_Y"][l]
                            ditchconninter["END_Y"][l] = start_y
                            ditchconninter["START_Z"][l] = ditchconninter["END_Z"][l]
                            ditchconninter["END_Z"][l] = start_z 
                    for l in range(0,len(ditchconninter)):
                        if round(ditchconninter["Shape"][i,0],2) == round(ditchconninter["START_X_1"][l],2):
                            start_x_1 = ditchconninter["START_X_1"][l]
                            start_y_1 = ditchconninter["START_Y_1"][l]
                            start_z_1 = ditchconninter["START_Z_1"][l]
                            ditchconninter["START_X_1"][l] = ditchconninter["END_X_1"][l]
                            ditchconninter["END_X_1"][l] = start_x_1
                            ditchconninter["START_Y_1"][l] = ditchconninter["END_Y_1"][l]
                            ditchconninter["END_Y_1"][l] = start_y_1
                            ditchconninter["START_Z_1"][l] = ditchconninter["END_Z_1"][l]
                            ditchconninter["END_Z_1"][l] = start_z_1
                    for l in range(0,len(ditchconninter)):
                        p1s = (ditchconninter['START_X'][l], ditchconninter['START_Y'][l]) 
                        p1e = (ditchconninter['END_X'][l], ditchconninter['END_Y'][l]) 
                        v = (p1e[0] - p1s[0], p1e[1] - p1s[1])
                        p2s = (ditchconninter['START_X_1'][l], ditchconninter['START_Y_1'][l]) 
                        p2e = (ditchconninter['END_X_1'][l], ditchconninter['END_Y_1'][l]) 
                        w = (p2e[0] - p2s[0], p2e[1] - p2s[1])
                        if v == w:ditchconninter['da'][l] = -1
                        else: ditchconninter['da'][l] = angleSeg.inner_angle(v,w)
                    ditchconninter_new = ditchconninter[ditchconninter['da'] != -1]
                    ditchconninter_new = ditchconninter_new[ditchconninter_new['da'] < 135]
                    ditchconninter_new = ditchconninter_new[ditchconninter_new['LENGTH_3D'] > 5]
                    ditchconninter_new = ditchconninter_new[ditchconninter_new['LENGTH_3_1'] > 5]
                    arcpy.da.NumPyArrayToFeatureClass(ditchconninter_new, traceFolder + "Ditch_conn_inter_new" + str(h) + "_" + str(i) + ".shp", "Shape", arcpy.Describe(inp.outputFolder + "Lines_up" + ".shp").spatialReference)  # @UndefinedVariable    
                    arcpy.UnsplitLine_management(traceFolder + "Ditch_conn" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditch_conn_unsplit" + str(h) + "_" + str(i) + ".shp")
                    arcpy.SplitLineAtPoint_management(traceFolder + "Ditch_conn_unsplit" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditch_conn_inter_new" + str(h) + "_" + str(i) + ".shp", traceFolder + "Ditches" + str(h) + "_" + str(i+1) + ".shp")       
                    # Flow direction
                    #---------------
                    arcpy.AddGeometryAttributes_management (inp.outputFolder + "Ditches" + ".shp", "LENGTH", "Meters", "SQUARE_METERS", "31370")
                    arcpy.MakeTableView_management(inp.outputFolder + "Ditches" + ".shp", "tempTableView")
                    arcpy.SelectLayerByAttribute_management("tempTableView", "NEW_SELECTION", "LENGTH = 0")
                    if int(arcpy.GetCount_management("tempTableView").getOutput(0)) > 0:
                        arcpy.DeleteRows_management("tempTableView")
                    arcpy.AddGeometryAttributes_management(traceFolder + "Ditches" + str(h) + "_" + str(i+1) + ".shp", "LINE_START_MID_END", "Meters", "SQUARE_METERS", "31370")
                    arcpy.AddField_management(traceFolder + "Ditches" + str(h) + "_" + str(i+1) + ".shp", "dz", "DOUBLE")
                    arcpy.CalculateField_management(traceFolder + "Ditches" + str(h) + "_" + str(i+1) + ".shp", "dz", "!START_Z! - !END_Z!", "PYTHON_9.3")
                    arcpy.MakeFeatureLayer_management(traceFolder + "Ditches" + str(h) + "_" + str(i+1) + ".shp", "lyrLines")
                    arcpy.SelectLayerByAttribute_management("lyrLines", "NEW_SELECTION", "dz < 0") 
                    arcpy.FlipLine_edit("lyrLines")
                    arcpy.SelectLayerByAttribute_management("lyrLines", "CLEAR_SELECTION")
                    # Get ditch vertices
                    #-------------------
                    arcpy.FeatureVerticesToPoints_management(traceFolder + "Ditches" + str(h) + "_" + str(i+1) + ".shp", traceFolder + "Ditches_vertBOTH" + str(h) + "_" + str(i+1) + ".shp", "BOTH_ENDS")
                    arcpy.AddGeometryAttributes_management(traceFolder + "Ditches_vertBOTH" + str(h) + "_" + str(i+1) + ".shp", "POINT_X_Y_Z_M")
                else:
                    nrendpoints = 0 
            else: 
                nrendpoints = 0
        else: 
            nrendpoints = 0
        #Loop over network
        #-----------------
        i = i + 1    
    # Loop over sink
    #---------------
    arcpy.SymDiff_analysis(traceFolder + "Ditches" + str(h) + "_" + str(i-1) + ".shp", traceFolder + "traced_lines_poss" + str(h) + "_" + str(i-1) + ".shp", traceFolder + "Ditches" + str(h+1) + "_" + str(0) + ".shp")
    arcpy.DeleteField_management (traceFolder + "Ditches" + str(h+1) + "_" + str(0) + ".shp", ["FID_Ditche", "Id_1", "START_X_1", "START_Y_1", "START_Z_1", "START_M_1", "MID_X_1", "MID_Y_1", "MID_Z_1", "MID_M_1", "END_X_1", "END_Y_1", "END_Z_1", "END_M_1", "START_M_1", "dz_1", "Shape_Leng", "FID_traced", "Enabled", "LENGTH"])
    arcpy.FeatureVerticesToPoints_management(traceFolder + "Ditches" + str(h+1) + "_" + str(0) + ".shp", traceFolder + "Ditches_vertBOTH" + str(h+1) + "_" + str(0) + ".shp", "BOTH_ENDS")
    arcpy.AddGeometryAttributes_management(traceFolder + "Ditches_vertBOTH" + str(h+1) + "_" + str(0) + ".shp", "POINT_X_Y_Z_M")
    arcpy.FeatureVerticesToPoints_management(traceFolder + "Ditches" + str(h+1) + "_" + str(0) + ".shp", traceFolder + "Ditches_end" + str(h) + ".shp", "END")
    arcpy.SpatialJoin_analysis(traceFolder + "Ditches_end" + str(h) + ".shp", traceFolder + "Ditches" + str(h+1) + "_" + str(0) + ".shp", traceFolder + "SpatJoin" + str(h) + ".shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "", "INTERSECT")
    arcpy.JoinField_management(traceFolder + "Ditches_end" + str(h) + ".shp", "FID", traceFolder + "SpatJoin" + str(h) + ".shp", "TARGET_FID", "Join_Count")
    arcpy.AddGeometryAttributes_management(traceFolder + "Ditches_end" + str(h) + ".shp", "POINT_X_Y_Z_M")
    arcpy.MakeFeatureLayer_management(traceFolder + "Ditches_end" + str(h) + ".shp", "temp")
    arcpy.CopyFeatures_management(traceFolder + "Ditches_end" + str(h) + ".shp", traceFolder + "sinks" + str(h+1) + ".shp")
    sinks = arcpy.da.TableToNumPyArray(traceFolder + "sinks" + str(h+1) + ".shp", "*")  # @UndefinedVariable
    nrsinks = len(sinks)
    h = h + 1
        
print "Finished"