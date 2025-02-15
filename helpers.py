import arcpy as ap
import os
import shutil

from helpers import *

# delete the feature class (file) from the gdb  
# specified in the filepath (loc), if it exists
def deleteFeatureClass(file, loc):
    org_loc = ap.env.workspace
    ap.env.workspace = loc
    if ap.Exists(file):
        ap.Delete_management(file)
        print(f'Deleted {file} from {loc}')
    else:
        print("Nothing to Delete!!! Moving on with script.")
    ap.env.workspace = org_loc

# deletes the folder and all files contained in the input path loc
def deleteFolder(loc):
    if os.path.exists(loc) and os.path.isdir(loc):
        shutil.rmtree(loc)
        print(f"{loc} DELETED!!!")

# Recalculates each column (fields) in table by weighting
# that field by the area of a (recently clipped) geometry.
def clipCalc(table, fields):
    for field in fields:
        ap.CalculateField_management(table, f"!{field}! * !sqmiles_coverage!", "PYTHON3")
        print(f"Recalculated {field}!!!")
    print("-------------------------------------------")
    print(" ")
    print(f"Finished Calculating Fields for {table}!!!")

# Clears out and replaces the input GDB with a new, blank one
def replaceGDB(root_dir, gdb):
    if os.path.exists(os.path.join(root_dir, gdb)):
        ap.ClearWorkspaceCache_management(os.path.join(root_dir, gdb))
        deleteFolder(os.path.join(root_dir,gdb))
    ap.CreateFileGDB_management(root_dir, gdb)
    print("GEODATABASE CREATED!!!")

# calculate area of polygons in a feature class (fc) and loading it in (field)
def calcSqMiles(fc, field):
    ap.CalculateField_management(fc, field, '!shape.area@squaremiles!', 'PYTHON3')

# makes a copy, then clips the input census_file based on the boundary_file,
# storing the output in the output_file of output_gdb. 
# New areas for clipped polygons are calculated, as well as the ratio of clipped to total area
def clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file):
    init_file = f'{census_file}_init' # ! does this just make a copy for safety?

    # copy files to new gdb
    ap.env.workspace = census_gdb
    ap.FeatureClassToFeatureClass_conversion(census_file, output_gdb, init_file)

    # switch to output gdb
    ap.env.workspace = output_gdb

    # rename fields
    ap.AddFields_management(init_file,[
        ['SqMiles','DOUBLE'],
        ['SqMiles_Clip','DOUBLE'],
        ['Coverage','DOUBLE']])

    # calculate the initial sq miles for the unclipped census polygons
    calcSqMiles(init_file, 'SqMiles')

    # clip and recalculate sq miles in SqMIiles_clip field
    ap.Clip_analysis(init_file, boundary_file, output_file)
    calcSqMiles(output_file, 'SqMiles_clip')

    # calculate percent coverage of clip
    ap.CalculateField_management(output_file, 'coverage', '!SqMiles_clip! / !SqMiles!', 'PYTHON3')


# join the input table to the input feature class, then calculate fields on joined fields list
# ! briefly - what is this function for? It feels like it serves a specific role in the other functions
def joinAndCalcFields(fc, census_gdb, output_gdb, key, table, table_key, fields_list):
    # add field - copy the table from the census loc to the output loc, then join
    org_loc = ap.env.workspace
    ap.env.workspace = census_gdb
    ap.TableToTable_conversion(table, output_gdb, table)
    ap.env.workspace = output_gdb
    ap.JoinField_management(fc, key, table, table_key, fields_list) # join


    # calculate field
    for field in fields_list:
        ap.CalculateField_management(fc, field, f"!{field}! * !coverage!") # ! not clear on what this line does... what is coverage?
        print(f"{field} calculated")
    ap.env.workspace = org_loc


# Remove working feature class and fields that do not need to be in the final output.
# Then, initialize the final feature class (final_file) in th final gdb (final_gdb_loc)
def cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields):
    deleteFeatureClass(final_file, final_gdb_loc)

    ap.FeatureClassToFeatureClass_conversion(twrw_places, ap.env.workspace, final_file)

    for field in delete_fields:
        ap.DeleteField_management(final_file, field)
        print("---------------------------")
        print(field + " DELETED")
        print("---------------------------")

    print("Minority_Final feature class created - Script Complete!!!")

    ap.ClearWorkspaceCache_management()

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(final_file, final_gdb_loc, final_file)
    print("---------------------------")

# does the field exist in the feature class? if not, initialize the field with input data type
def checkforfield(fc, field, type):
    if field not in ap.ListFields(fc, field):
        return
    else:
        ap.DeleteField_management(fc, field)
        ap.AddField_management(fc, field, type)
    