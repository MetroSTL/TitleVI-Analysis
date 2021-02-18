from census import Census
from us import states
import pandas as pd
from arcgis import GIS
import arcpy

from helpers import * 

# takes in Routes By Direction from the open data store as input
# creates a couple of databases 1 to split the gdb

year = '13'
root_dir = r"C:\Users\wkjenkins\gis\titlevi\20210119\new_output"
gdb = r"C:\Users\wkjenkins\gis\titlevi\20210119\new_output\final.gdb"
routes_gdb = r"C:\Users\wkjenkins\gis\titlevi\20210119\arcpro\routes.gdb"

arcpy.env.workspace = gdb
arcpy.ClearWorkspaceCache_management()

routes_dir = os.path.join(gdb, 'MetroBusRoutes_dir__200120')
routesRoute_field = "RouteAbbr"

route_types = os.path.join(gdb, 'RouteTypes')
routesTypes_field = "RouteAbbre"

replaceGDB(root_dir, f'routes_{year}.gdb')
replaceGDB(root_dir, f'routes_split_{year}.gdb')

arcpy.env.workspace = gdb
arcpy.AddJoin_management(routes_dir, routesRoute_field, route_types, routesTypes_field)

if 'NewDir' in arcpy.Describe(routes_dir).fields:
    arcpy.DeleteField_management(routes_dir, 'NewDir')

arcpy.AddField_management(routes_dir, 'NewDir', 'text')

dirRouteBlock = '''def direction(str):
    if str == "EB":
        return 0
    elif str == "WB":
        return 1
    elif str == "NB":
        return 1
    elif str == "SB":
        return 0
    elif str == "CL":
        return 1
    elif str == "CC":
        return 0
    else:
        return -1'''

arcpy.CalculateField_management(routes_dir, 'NewDir', "direction(!DirName!)", "PYTHON3", dirRouteBlock)
split_gdb = arcpy.SplitByAttributes_analysis(routes_dir, os.path.join(root_dir, f'routes_split_{year}.gdb'), ["RouteAbbr", "NewDir"])[0]

replaceGDB(root_dir, f'stops_split_{year}.gdb')


dirBlock = '''def dirCalc(str):
    if "EAST" in str :
        return "0"
    elif "WEST" in str:
        return "1"
    elif "NORTH" in str:
        return "1"
    elif "SOUTH" in str:
        return "0"
    elif "COUNTERCLOCKWIS" in str:
        return "0"
    elif "CLOCKWISE" in str:
        return "1"
    else:
        return 2'''



if 'NewDir' in arcpy.Describe(os.path.join(gdb, "MetroBusStopsByLine__200120")).fields:
    arcpy.DeleteField_management(os.path.join(gdb, "MetroBusStopsByLine__200120"), 'NewDir')

arcpy.AddField_management(os.path.join(gdb, "MetroBusStopsByLine__200120"), 'NewDir', 'text')
arcpy.CalculateField_management(os.path.join(gdb, "MetroBusStopsByLine__200120"), 'NewDir', "dirCalc(!Dir!)", "PYTHON3", dirBlock)

arcpy.SplitByAttributes_analysis(os.path.join(gdb, "MetroBusStopsByLine__200120"), os.path.join(root_dir, f'stops_split_{year}.gdb'), ['RouteCode', 'NewDir'])

arcpy.env.workspace = os.path.join(root_dir, f'routes_split_{year}.gdb')
for route in arcpy.ListFeatureClasses():
    arcpy.env.workspace = os.path.join(root_dir, f'routes_split_{year}.gdb')

    fea = os.path.join(split_gdb, route)
    searchRadius = "20 Meters"

    fea_pd = pd.DataFrame.spatial.from_featureclass(fea)

    route = fea_pd['RouteAbbr'][0]
    d = fea_pd['NewDir'][0]

    stop_split_loc = os.path.join(os.path.join(root_dir, f'stops_split_{year}.gdb'), f'T{route}_{d}')

    arcpy.SplitLineAtPoint_management(fea, stop_split_loc, os.path.join(split_gdb,f'T{route}_{d}_split'), searchRadius)

arcpy.env.workspace = split_gdb
split_route_list = arcpy.ListFeatureClasses('_split')

merge_routes_split = arcpy.Merge_management(split_route_list, os.path.join(gdb, f'RoutesSplit_{year}'))[0]


if 'LengthMiles' in arcpy.Describe(merge_routes_split).fields:
    arcpy.DeleteField_management(merge_routes_split, 'LengthMiles')

arcpy.CalculateField_management(merge_routes_split, 'LengthMiles', "!shape.length@miles!")