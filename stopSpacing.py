from census import Census
from us import states
import pandas as pd
from arcgis import GIS
import arcpy

from helpers import * 

# takes in Routes By Direction from the open data store as input
# creates a couple of databases 1 to split the gdb

year = '18'
root_dir = r"C:\Users\wkjenkins\gis\titlevi\20210119\new_output"
gdb = r"C:\Users\wkjenkins\gis\titlevi\20210119\new_output\final.gdb"
routes_gdb = r"C:\Users\wkjenkins\gis\titlevi\20210119\arcpro\routes.gdb"

arcpy.env.workspace = gdb
arcpy.ClearWorkspaceCache_management()

routes_dir = os.path.join(gdb, 'MetroBusRoutes_dir__200120') # ! are these route geometries? Routes by direction
routesRoute_field = "RouteAbbr"

route_types = os.path.join(gdb, 'RouteTypes') # ! what are these again? like, local/express/frequent etc.? Defined in the MetroReimagined service standards (Frequent, community, express and local?)
routesTypes_field = "RouteAbbre"

# get fresh GDB's in this location to re-run stop spacing
replaceGDB(root_dir, f'routes_{year}.gdb')
replaceGDB(root_dir, f'routes_split_{year}.gdb')

arcpy.env.workspace = gdb

# join routes with route type information
arcpy.AddJoin_management(routes_dir, routesRoute_field, route_types, routesTypes_field)


# redefine route direction byy 1 and 0 rather than character combinations,
# then split route by direction for separate analysis
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

arcpy.CalculateField_management(routes_dir, 'NewDir', "direction(!DirName!)", "PYTHON3", dirRouteBlock) # use code block above to cal the field
split_gdb = arcpy.SplitByAttributes_analysis(routes_dir, os.path.join(root_dir, f'routes_split_{year}.gdb'), ["RouteAbbr", "NewDir"])[0] # ! I can't tell whether this give me two files, or what happens

replaceGDB(root_dir, f'stops_split_{year}.gdb')

# the same as above, for stops
# ! can stops be defined with multiple directions depending on the route? 
# They are defined in the route directions the join is done by route and direction
if 'NewDir' in arcpy.Describe(os.path.join(gdb, "MetroBusStopsByLine__200120")).fields:
    arcpy.DeleteField_management(os.path.join(gdb, "MetroBusStopsByLine__200120"), 'NewDir')

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
        return 2''' # ! any reason it isn't -1 like above?

# ! Define this above?
# calculation of creating a commonality of directional flags
arcpy.AddField_management(os.path.join(gdb, "MetroBusStopsByLine__200120"), 'NewDir', 'text')
arcpy.CalculateField_management(os.path.join(gdb, "MetroBusStopsByLine__200120"), 'NewDir', "dirCalc(!Dir!)", "PYTHON3", dirBlock)

# split all of the routes by direction into different feature classes within the stops_split(year).gdb by route and direction
arcpy.SplitByAttributes_analysis(os.path.join(gdb, "MetroBusStopsByLine__200120"), os.path.join(root_dir, f'stops_split_{year}.gdb'), ['RouteCode', 'NewDir'])

# ! I am not 100% on what this loop does
# the GDB that is pointing at the split routes by direction and loops through each 
# of the routes by direction in order to split the routes by points along the rout
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


# I ENDED UP JUST VISUALIZING THE DATA AND LEAVING IIT UP TO THE AUDIENCE
# TO TAKE IT ANOTHER STEP FURTHER YOU COULD JUST PERFORM A DISSOVLE AND RUN
# CALCULATIONS THAT WAY. PUTTING TOGETHER ANYTHING THAT WOULD MAKE SOMETHING
# "PASSING" OR "FAILING" ON THAT BIG OF A SCALE ESPECIALLY WITH CONSIDERING
# THE TYPE OF LAND USE WILL NOT PRODUCE GREAT RESULTS. WHAT WE HAD TALKED ABOUT
# IS A STANDARD FOR INSIDE AND OUTSIDE OF THE CITY. SO YOU WOULD NEED TO BREAK IT 
# UP THAT WAY




# ALTERNATIVE WAY OF CALCULATING

# merge all spilt route in gdb to the same feature class
# calculate length

# reclassify routes
# use isPassing Calc to flag each seg by route type and length

# dissolve routes by passing and not passing. 
# calc total length, passing length, failing length, passing segments and failing segments

# future development add in road classifications for density




# determine whether spacing between stops meets the service standard

def isPassing(type, length):
    if type == "Frequent":
        if length > 0.25 & length < 0.33:
            return 1
        else:
            return 0
    elif type == "Local":
        if length <= 0.25:
            return 1
        else:
            return 0
    elif type == "Community":
        if length <= 0.25:
            return 1
        else:
            return 0
    else:
       return 2