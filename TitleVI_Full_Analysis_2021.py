import arcpy as ap
import os
import shutil

from helpers import *

from medHHInc import *
from senior import *
from idRoutes import *
from lowCar import *
from minority import *
from lep import *
from poverty import *

# *******GLOBAL VARIABLES*****
# year = str(input('What Year? "YY": '))
year = '13'
root_dir = r"C:\Users\wkjenkins\gis\titlevi\20210119\new_output"

# ACS GDB's ---> USE STANDARD ACS BLOCKGOUP AND TRACT FILES GDB FILES (https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-data.html)
## Download format f"https://www2.census.gov/geo/tiger/TIGER_DP/20{year}ACS/ACS_20{year}_5YR_BG_29.gdb.zip"
census_url = f"https://www2.census.gov/geo/tiger/TIGER_DP/20{year}ACS/ACS_20{year}_5YR_BG_29.gdb.zip"
bg_mergegdb = rf"C:\Users\wkjenkins\gis\local_layers\ACS_20{year}_5YR_BG\merge.gdb"
tracts_mergegdb = rf"C:\Users\wkjenkins\gis\local_layers\ACS_20{year}_5YR_TRACT\merge.gdb"

places = r'C:\Users\wkjenkins\gis\titlevi\20210119\python_input\MO_IL_Places_2017.shp'
routes = r'C:\Users\wkjenkins\gis\titlevi\20210119\python_input\MetroBusRoutes_COA_190917.shp' # ------> Select Routes file
region = r'C:\Users\wkjenkins\gis\titlevi\20210119\python_input\Region.shp'


# GEOMETRY FILES
bg_file = f"ACS_20{year}_5YR_BG"
tracts_file = f"ACS_20{year}_5YR_TRACT_Region"

# DB TABLES
senior_file = "X01_AGE_AND_SEX"
race_file = "X02_RACE"
hisp_file = "X03_HISPANIC_OR_LATINO_ORIGIN"
commute_file = "X08_COMMUTING"
lep_file = "X16_LANGUAGE_SPOKEN_AT_HOME"
pov_file = "X17_POVERTY"
inc_file = "X19_INCOME"

# # DELETE AND CREATE NEW FINAL_{year}.gdb

# # FINAL GDB
final_gdb = f'Final_{year}.gdb'
final_gdb_loc = os.path.join(root_dir, final_gdb)

ap.ClearWorkspaceCache_management()

replaceGDB(root_dir, final_gdb)

medHHInc(year, root_dir, bg_mergegdb, region, places, bg_file, inc_file, final_gdb_loc)

senior(year, root_dir, bg_mergegdb, region, places, bg_file, senior_file, final_gdb_loc)

poverty(year, root_dir, bg_mergegdb, region, places, bg_file, pov_file, final_gdb_loc)

lep(year, root_dir, bg_mergegdb, region, places, bg_file, lep_file, final_gdb_loc)

minority(year, root_dir, bg_mergegdb, region, places, bg_file, race_file, hisp_file, final_gdb_loc)

lowCar(year, root_dir, tracts_mergegdb, region, places, tracts_file, commute_file, final_gdb_loc)

idRoutes(year, root_dir, routes, final_gdb_loc)
