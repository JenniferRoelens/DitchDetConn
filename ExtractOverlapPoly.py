'''
Created on 12 jun. 2017

@author: u0099505
'''
import arcpy
from arcpy import sa
import numpy

def Extract(raster, polygons, outputFolder, polyfid_column):
    arcpy.Dissolve_management(polygons, outputFolder + "polydissolve.shp")
    rasvalues = sa.ExtractByMask(raster, outputFolder + "polydissolve.shp")
    arcpy.RasterToPoint_conversion(rasvalues, outputFolder + "raspoints.shp")
    arcpy.SpatialJoin_analysis(polygons, outputFolder + "raspoints.shp", outputFolder + "spatjoinpolygons.shp", "JOIN_ONE_TO_MANY")
    pnts = arcpy.da.TableToNumPyArray(outputFolder + "spatjoinpolygons.dbf", (polyfid_column, 'GRID_CODE'))  # @UndefinedVariable
    polynr = len(numpy.unique(pnts[polyfid_column]))
    pnts_mean = numpy.zeros((polynr, 1))
    pnts_std = numpy.zeros((polynr, 1))
    pnts_var = numpy.zeros((polynr, 1))
    pnts_rng = numpy.zeros((polynr, 1))
    for i in range(polynr):
        idx = pnts[polyfid_column] == i
        pnts_mean[i] = numpy.mean(pnts['GRID_CODE'][idx])
        pnts_std[i] = numpy.std(pnts['GRID_CODE'][idx])
        pnts_var[i] = numpy.var(pnts['GRID_CODE'][idx])
        pnts_rng[i] = numpy.ptp(pnts['GRID_CODE'][idx])
    return pnts_mean, pnts_std, pnts_var, pnts_rng