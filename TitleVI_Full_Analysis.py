import arcpy as ap
import os
from datetime import datetime
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection
import pandas as pd


# ************ VARIABLES ************

root_dir = r'C:\Users\wkjenkins\Documents\local_gis\trapeze\AutomationExports'

# ***********************************

# WORKING DIRECTORIES
gdb = f"DataStore.gdb"
ap.env.workspace = os.path.join(root_dir, gdb)
working_gdb = os.path.join(root_dir, gdb)

# TIME VARIABLES
year = datetime.today().strftime('%Y')[2:4]
month = datetime.today().strftime('%m')
day = datetime.today().strftime('%d')
date = datetime.today().strftime(f'{year}{month}{day}')

# AGOL / Enterprise Settings
user = input('AGOL Username: ')
password = input("Password: ")
portal = 'https://metroas08.metrostlouis.org/arcgis/home/'

gis = GIS(url = portal, username = user, password = password)

# FILE NAMES
bs = 'MetroBusStops'
bs_id = 'b2abfd6d336a471996f60659bb37e70d'
bsbl = 'MetroBusStopsByLine'
bsbl_id = 'f23490b874b44642b4a6bc4e10c0ae4c'

stop_files = [[bs, bs_id],
              [bsbl, bsbl_id]]


# ACS FILES
acs_gdb = rf"C:\Users\wkjenkins\Documents\local_gis\titlevi\Final_2017.gdb"
minority = os.path.join(acs_gdb, "Minority17_Final")
lep = os.path.join(acs_gdb, "LEP17_Final")
poverty = os.path.join(acs_gdb, "LEP17_Final")
senior = os.path.join(acs_gdb, "Senior17_Final")
no_car = os.path.join(acs_gdb, "NoCar17_Final")

acs_list = [[minority, ], [lep, ],[poverty, ], [senior, ], [no_car, ]]

for item in stop_files:
    name = f'{item[0]}_{date}'
    csv = f'exports/{item[0]}.csv'
    loc = os.path.join(root_dir, csv)
    gdb_loc = os.path.join(working_gdb, name)
    fc = os.path.join(working_gdb, name)

    print("")
    print("**************************************")
    print(f'STARTING {name} PROCESSING')
    print("**************************************")
    print("")

    if ap.Exists(name):
        ap.Delete_management(name)
        print(f'Deleted {name} from {working_gdb}')
    else:
        print("Nothing to Delete!!! Moving on with script.")

    ap.management.XYTableToPoint(loc, name, 'GPS_LON', 'GPS_LAT', "", ap.SpatialReference(4326))

    print("")
    print(f'{name} Created in GDB!!!')






# START OF PATTERNS / ROUTE PROCESSING

## PATTTERNS / ROUTE VARIABLES


# **** CODE DEFINITIONS ****
# PATTERNS => DEFAULT EXPORT FROM SQL DATABASE
# PATTERNS POINTS => DEFAULT EXPORT OF PATTERNS PLOTTED AS POLYPOINT FILES
# PATTERNS GROUP => GROUP PATTERNS DATA BY 'SHAPE_ID'. GROUPS ALL OF THE NODES TOGETHER
# PATTERNS LINE => PATTERN POINTS PLOTTED AS LINES GROUPED BY 'SHAPE_ID' USING 'SEQUENCE_ID'
# ROUTES BY DIRECTION => PATTERNS BY LINE GROUPED BY 'ROUTE_ABBR' AND 'DIR'
# ROUTES =>
#



# DEFAULT EXPORT NAME AND LOCATION
patterns_name = 'MetroPatterns'
patterns_csv = os.path.join(root_dir, f'exports\{patterns_name}.csv')

# PATTERNS POINTS
patterns_xy = f'{patterns_name}_XY_{date}'
patterns_xy_loc = os.path.join(gdb, patterns_xy)

# PATTERNS LINE
patterns_line = f'{patterns_name}_Line_{date}'
patterns_line_loc = os.path.join(gdb, patterns_line)

# PATTERNS ATTRIBUTE TABLES
patterns_group = f'{patterns_name}_group_{date}'
patterns_group_csv = os.path.join(root_dir, f'exports/{patterns_group}.csv')

# ROUTES BY DIRECTION
routes_dir_line = f'MetroBusRoutes_dir_{date}'
routes_dir_loc = os.path.join(gdb, routes_dir_line)
routes_line = f'MetroBusRoutes_{date}'
routes_loc = os.path.join(gdb, routes_line)
routes_csv = f'Routes_{date}.csv'
routes_csv_loc = os.path.join(root_dir, f'exports\{routes_csv}')


# ROUTE BUFFER
routes_buffer = f'Routes_ADA_buffer_{date}'
routes_buffer_loc = os.path.join(working_gdb, routes_buffer)


# PATTERNS GROUP
patterns_pd = pd.read_csv(os.path.join(root_dir, patterns_csv))
patterns_pd = patterns_pd.groupby(['ROUTEABBR', 'LINENAME', 'PUBNUM', 'LINENUM', 'SHAPE_ID', 'DIR_NAME']).mean()
patterns_pd.drop(['SHAPE_LAT', 'SHAPE_LON', 'SHAPE_PT_SEQUENCE'], axis=1)
print('Unique Routes table created')

if ap.Exists(patterns_group_csv):
    ap.Delete_management(patterns_group_csv)
    print(f'Deleted {patterns_group} from exports')
else:
    print("Nothing to Delete!!! Moving on with script.")

patterns_pd.to_csv(patterns_group_csv)
print(f'{patterns_group} exported')



# PATTERNS POINTS

# CHECK FOR FILE AND DELETE IF IT EXISTS
if ap.Exists(patterns_xy):
    ap.Delete_management(patterns_xy)
    print(f'Deleted {patterns_xy} from {working_gdb}')
else:
    print("Nothing to Delete!!! Moving on with script.")

# TURN CSV TO POINTS FEATURE CLASS
ap.management.XYTableToPoint(patterns_csv, patterns_xy, 'SHAPE_LON', 'SHAPE_LAT', "", ap.SpatialReference(4326))
print("Created Points file from CSV file")

# CHECK FOR FILE AND DELETE IF IT EXISTS
if ap.Exists(patterns_line):
    ap.Delete_management(patterns_line)
    print(f'Deleted {patterns_line} from {working_gdb}')
else:
    print("Nothing to Delete!!! Moving on with script.")

ap.PointsToLine_management(patterns_xy, patterns_line, 'SHAPE_ID', 'SHAPE_PT_SEQUENCE')
print("Created Line file from Point file")


# ADD IN PATTERNS GROUP ATTRIBUTES TO PATTERNS LINE

ap.JoinField_management(patterns_line, 'SHAPE_ID', patterns_group_csv, 'SHAPE_ID', ['ROUTEABBR', 'DIR_NAME', 'LINENAME', 'PUBNUM', 'LINENUM', 'DIR_NAME'])
print("Added fields to Patterns")


# CREATE ROUTES DIRECTION AND ROUTES FILES

# DELETE DUPLICATE ROUTE DIRECTION FILE
if ap.Exists(routes_dir_line):
    ap.Delete_management(routes_dir_line)
    print(f'Deleted {routes_dir_line} from {working_gdb}')
else:
    print("Nothing to Delete!!! Moving on with script.")

# CREATE ROUTE DIR SHAPEFILE
ap.Dissolve_management(patterns_line, routes_dir_line, ['ROUTEABBR', 'LINENAME', 'PUBNUM', 'LINENUM', 'DIR_NAME_1'])
print('Created Routes Dir Lines')


# DELETE DUPLICATE ROUTE FILE
if ap.Exists(routes_line):
    ap.Delete_management(routes_line)
    print(f'Deleted {routes_line} from {working_gdb}')
else:
    print("Nothing to Delete!!! Moving on with script.")

# CREATE ROUTE SHAPEFILE
ap.Dissolve_management(patterns_line, routes_line, ['ROUTEABBR', 'LINENAME', 'PUBNUM', 'LINENUM'])
print('Created Routes Lines')

ap.Buffer_analysis(routes_line, routes_buffer, "0.75 Miles", "FULL", "ROUND", "ALL")



# ROUTE BUFFER FEATURE SERVICE CONFIGURATION
route_buffer_properties = {'title': f'ADA Route Buffers',
                           'description': f'ADA Route buffers from {month}/{day}/{year}. This file is the most up to '
                                          f'date file that has been buffered 3/4 of a mile for the entire system. '
                                          f'The population estimates are coming from the 2017 ACS data from the US '
                                          f'Census.',
                           'tags': 'metro, transit, ada, population, acs, buffer, metrobus, routes',
                           'type': 'Feature Service'}

routes_buffer_item = gis.content.add(item_properties=route_buffer_properties,
                                     data=routes_buffer_loc)
routes_buffer_layer_item = routes_buffer_item.publish()


print("done")
