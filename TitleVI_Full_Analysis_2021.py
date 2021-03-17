# ! should all of these be defined in one place? (I'm actually asking)
import arcpy as ap
import os
import shutil

from helpers import *

# import functions from each of the helper files
from medHHInc import *
from senior import *
from idRoutes import *
from lowCar import *
from minority import *
from lep import *
from poverty import *
from tni import *

# *******GLOBAL VARIABLES*****
# year = str(input('What Year? "YY": '))
year = '13'
root_dir = r"C:\Users\wkjenkins\gis\titlevi\20210119\new_output"

# api key to access census data using the Census package
census_key = '926b40d26ccd30996f8a0222ce5d4458240a7ac2'

# ACS GDB's ---> USE STANDARD ACS BLOCKGOUP AND TRACT FILES GDB FILES (https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-data.html)
## Download format f"https://www2.census.gov/geo/tiger/TIGER_DP/20{year}ACS/ACS_20{year}_5YR_BG_29.gdb.zip"
census_url = f"https://www2.census.gov/geo/tiger/TIGER_DP/20{year}ACS/ACS_20{year}_5YR_BG_29.gdb.zip"
bg_mergegdb = rf"C:\Users\wkjenkins\gis\local_layers\ACS_20{year}_5YR_BG\merge.gdb"
tracts_mergegdb = rf"C:\Users\wkjenkins\gis\local_layers\ACS_20{year}_5YR_TRACT\merge.gdb"

places = r'C:\Users\wkjenkins\gis\titlevi\20210119\python_input\MO_IL_Places_2017.shp'
routes = r'C:\Users\wkjenkins\gis\titlevi\20210119\python_input\MetroBusRoutes_COA_190917.shp' # ------> Select Routes file
region = r'C:\Users\wkjenkins\gis\titlevi\20210119\python_input\Region.shp'


# INPUT GEOMETRY FILES - names of GDB's
bg_file = f"ACS_20{year}_5YR_BG" # census blockgroups
tracts_file = f"ACS_20{year}_5YR_TRACT" # census tracts

# DB TABLES - Feature class names
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

# ! briefly -- why is this here?
ap.ClearWorkspaceCache_management()


# # Call each of the major functions to create fature classes with
# # statistics for each of the demographics outlined in each function.

# replace the output GDB with an empty one at the start
# replaceGDB(root_dir, final_gdb) # from helpers.py

# medHHInc(year, root_dir, bg_mergegdb, region, places, bg_file, inc_file, final_gdb_loc)

# senior(year, root_dir, bg_mergegdb, region, places, bg_file, senior_file, final_gdb_loc)

# poverty(year, root_dir, bg_mergegdb, region, places, bg_file, pov_file, final_gdb_loc)

# ! why does lep use the census key and the other functions do not?
lep(year, root_dir, bg_mergegdb, region, places, bg_file, lep_file, final_gdb_loc, census_key, tracts_mergegdb, tracts_file)

# minority(year, root_dir, bg_mergegdb, region, places, bg_file, race_file, hisp_file, final_gdb_loc)

# lowCar(year, root_dir, tracts_mergegdb, region, places, tracts_file, commute_file, final_gdb_loc)

# idRoutes(year, root_dir, routes, final_gdb_loc)

# tni(year, root_dir, final_gdb_loc)