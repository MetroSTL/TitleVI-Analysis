import arcpy as ap
import os
import shutil

from helpers import *

# Uses census inputs to calculate totals and percentage of seniors (over 65) in each census block group.
# Then, determine which blockgroups are greater than the regional average for senior percentage.
def senior(year, root_dir, bg_mergedgdb, region, places, bg_file, sen_file, final_gdb_loc):
    gdb = f"Senior{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year
    ap.ClearWorkspaceCache_management()

    outputgdb = ap.env.workspace
    working_file = f"Senior{year}_working"

    bg = os.path.join(bg_mergedgdb, bg_file)
    working_gdb = os.path.join(root_dir, gdb)

    # Working feature class locations
    sen_table = os.path.join(bg_mergedgdb, sen_file)
    cw_file = f"Senior{year}_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = f"Senior{year}_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = f"Senior{year}_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = f"Senior{year}_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    twrw_places_file = f"Senior{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    final_file = f"Senior{year}_Final"
    final = os.path.join(outputgdb, final_file)


    # CREATE WORKING GDB
    replaceGDB(root_dir, gdb)


    fields_list = ['B01001e1', 'B01001e20', 'B01001e21', 'B01001e22', 'B01001e23', 'B01001e24', 'B01001e25', 'B01001e44', 'B01001e45', 'B01001e46', 'B01001e47', 'B01001e48', 'B01001e49']

    # Clip blockgroups by the region shape, and keep only fields of interest
    # clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file, join_table, fields_list)
    clipPolygons(bg_mergedgdb, bg_file, region, os.path.join(root_dir, gdb), working_file)
    joinAndCalcFields(working_file, bg_mergedgdb, os.path.join(root_dir, gdb), 'GEOID_Data', sen_file, 'GEOID', fields_list)


    ap.env.workspace = outputgdb

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ['TPop', 'DOUBLE'],
                                           ["TSenior", "DOUBLE"], # count
                                           ["PSenior", "Double"], # percent
                                           ["SeniorDens", "DOUBLE"], # density
                                           ["CoAbvSenior", "SHORT"],   # is the bg above county senior percentage
                                           ["RegAbvSenior", "SHORT"]]) # is the bg above region senior percentage 

    ap.CalculateFields_management(working_file, 'PYTHON3', [['TPop', '!B01001e1!'],
                                                            ['TSenior', # all population over 65
                                                             '!B01001e44! + !B01001e45! + !B01001e46! + !B01001e47! + !B01001e48! + !B01001e49! + !B01001e20! + !B01001e21! + !B01001e22! + !B01001e23! + !B01001e24! + !B01001e25!'],
                                                            ['PSenior', '!TSenior! / !TPop!'],
                                                            ['SeniorDens', '!TSenior!/!SqMiles!']])


    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["TPop", "SUM"],
                                                          ["SqMiles", "SUM"],
                                                          ["TSenior", "SUM"]])
    print("")
    print("---------------------------")
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [["TPop", "SUM"],
                                                  ["SqMiles", "SUM"],
                                                  ["TSenior", "SUM"]])
    print("")
    print("---------------------------")
    print("Dissolve Region Stats")

    # define and compute county calculation fields
    ap.management.AddFields(cw, [["CoSqMiles", "DOUBLE"], # square miles
                                 ["CoTPop", "DOUBLE"], # total pop
                                 ["CoTSenior", "DOUBLE"], # senior pop
                                 ["CoPSenior", "Double"], # senior percentage
                                 ["CoSeniorDens", "DOUBLE"], # seniors per sq mile
                                 ["CoAbvSenior", "DOUBLE"]]) # is the bg above county senior percentage

    ap.CalculateFields_management(cw, "PYTHON", [["CoSqMiles", "!SUM_SqMiles!"],
                                                 ["CoTPop", "!SUM_TPop!"],
                                                 ["CoTSenior", "!SUM_TSenior!"],
                                                 ["CoPSenior", "!CoTSenior! / !CoTPop!"],
                                                 ["CoSeniorDens", "!CoTSenior! / !CoSqMiles!"]])

    print("")
    print("---------------------------")
    print(cw_file + " fields calculated !!!")

    # define and region county calculation fields
    ap.management.AddFields(rw, [["RegSqMiles", "DOUBLE"],
                                 ["RegTPop", "DOUBLE"],
                                 ["RegTSenior", "DOUBLE"],
                                 ["RegPSenior", "Double"],
                                 ["RegSeniorDens", "DOUBLE"],
                                 ["RegAbvSenior", "DOUBLE"]])

    ap.CalculateFields_management(rw, "PYTHON", [["RegSqMiles", "!SUM_SqMiles!"],
                                                 ["RegTPop", "!SUM_TPop!"],
                                                 ["RegTSenior", "!SUM_TSenior!"],
                                                 ["RegPSenior", "!RegTSenior! / !RegTPop!"],
                                                 ["RegSeniorDens", "!RegTSenior! / !RegSqMiles!"]])
    print("")
    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    # SPATIAL JOIN TRACTS FILE WITH COUNTY FILE
    ap.SpatialJoin_analysis(working_file, cw, twcw)
    print("")
    print("---------------------------")
    print("County Spaital Join")

    # SPATIAL JOIN TRACTS FILE WITH REGION FILE
    ap.SpatialJoin_analysis(twcw, rw, twrw)
    print("")
    print("---------------------------")
    print("Region Spaital Join")

    # identify blockgroups as greater than county and regional average
    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoAbvSenior 'ifBlock(!PSenior!, !CoPSenior!)';RegAbvSenior 'ifBlock(!PSenior!, !RegPSenior!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("")
    print("---------------------------")
    print("Above Senior Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, places, twrw_places)
    print("---------------------------")
    print("Places Spaital Join")

    # remove these unnecessary fields in the cleanup stage
    delete_fields = ['B01001e20', 'B01001e21', 'B01001e22', 'B01001e23', 'B01001e24', 'B01001e25', 'B01001e44', 'B01001e45',
            'B01001e46', 'B01001e47', 'B01001e48', 'B01001e49', 'B01001e1', 'Join_Count', 'TARGET_FID',
            'Join_Count_1', 'TARGET_FID_1', 'Join_Count_12', 'TARGET_FID_12', 'COUNTYFP_1', 'SUM_TPop', 'SUM_SqMiles',
            'SUM_TSenior', 'Shape_Length_1', 'Shape_Area_1', 'CoAbvSenior_1', 'SUM_TPop_1', 'SUM_SqMiles_1',
            'SUM_TSenior_1', 'Shape_Length_12', 'Shape_Area_12', 'RegSqMiles', 'RegAbvSenior_1', 'STATEFP_1', 'PLACEFP',
            'PLACENS', 'AFFGEOID', 'GEOID_1', 'LSAD', 'ALAND_1', 'AWATER_1']

    cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)