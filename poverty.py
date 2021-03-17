# ! are the imports needed if they are defined in main?

import arcpy as ap
import os
import shutil

from helpers import *

# Uses census inputs to calculate totals and percentage of low income groups in each census block group.
# Then, determine which blockgroups are greater than the regional and county average for low income percentage.
# Low income is defined as all households less than 150% of the poverty line.
def poverty(year, root_dir, bg_mergedgdb, region, places, bg_file, pov_file, final_gdb_loc):
    gdb = f"Poverty{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year

    ap.ClearWorkspaceCache_management()

    outputgdb = ap.env.workspace
    working_file = "Poverty_working"

    # ! can these go?
    pov_table = os.path.join(bg_mergedgdb, pov_file)
    bg = os.path.join(bg_mergedgdb, bg_file)
    working_gdb = os.path.join(root_dir, gdb)

    # Working feature class locations
    twrw_places_file = f"Poverty{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    cw_file = f"Poverty{year}_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = f"Poverty{year}_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = f"Poverty{year}_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = f"Poverty{year}_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    final_file = f"Poverty{year}_Final"
    final = os.path.join(outputgdb, final_file) # ! still needed?

    replaceGDB(root_dir, gdb)

    fields_list = ["B17010e1", "C17002e1", "C17002e2", "C17002e3", "C17002e4", "C17002e5"]

    # Clip blockgroups by the region shape, and keep only fields of interest
    # clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file, join_table, fields_list)
    clipPolygons(bg_mergedgdb, bg_file, region, os.path.join(root_dir, gdb), working_file)
    joinAndCalcFields(working_file, bg_mergedgdb, os.path.join(root_dir, gdb), 'GEOID_Data', pov_file, 'GEOID', fields_list)

    ap.env.workspace = outputgdb

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ["TFam", "DOUBLE"],
                                           ["TPov", "DOUBLE"],
                                           ['PPOV', "DOUBLE"],
                                           ["POVDens", "DOUBLE"],
                                           ["CoPovBG", "SHORT"],
                                           ["RegPovBG", "SHORT"]])
    print('Added Fields to working file')

   # compute median income from census fields
    ap.CalculateFields_management(working_file, "PYTHON3", [["SqMiles", "!shape.area@squaremiles!"],
                                                            ["TFam", "!C17002e1!"],
                                                            ["TPov", "!C17002e2! + !C17002e3! + !C17002e4! + !C17002e5!"], # all households less than 150% of the poverty line
                                                            ['PPov', "!TPov! / !TFam!"],
                                                            ["PovDens", "!TPov! / !SqMiles!"]])

    print("---------------------------")
    print("Finished calculating Median HH Inc Calcs")

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["TFam", "SUM"],
                                                          ["TPov", "SUM"],
                                                          ["SqMiles", "SUM"]])
    print("---------------------------")
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [["TFam", "SUM"],
                                                  ["TPov", "SUM"],
                                                  ["SqMiles", "SUM"]])
    print("---------------------------")
    print("Dissolve Region Stats")

    # define and compute county calculation fields
    ap.management.AddFields(cw, [["CoTFam", "DOUBLE"], # total families
                                 ["CoTPov", "DOUBLE"], # total low income families
                                 ["CoPPov", "DOUBLE"], # percent low income families
                                 ["CoSqMiles", "DOUBLE"], # square  miles
                                 ["CoPovDens", "DOUBLE"]]) # low income hh per square mile

    ap.CalculateFields_management(cw, "PYTHON", [["CoTFam", "!SUM_TFam!"],
                                                 ["CoTPov", "!SUM_TPov!"],
                                                 ["CoPPov", "!SUM_TPov!/!SUM_TFam!"],
                                                 ["CoSqMiles", "!SUM_SqMiles!"],
                                                 ["CoPovDens", "!CoTPov! / !CoSqMiles!"]])
    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    # define and compute region calculation fields
    ap.management.AddFields(rw, [["RegTFam", "DOUBLE"],
                                 ["RegTPov", "DOUBLE"],
                                 ["RegPPov", "DOUBLE"],
                                 ["RegSqMiles", "DOUBLE"],
                                 ["RegPovDens", "DOUBLE"]])

    ap.CalculateFields_management(rw, "PYTHON", [["RegTFam", "!SUM_TFam!"],
                                                 ["RegTPov", "!SUM_TPov!"],
                                                 ["RegPPov", "!SUM_TPov!/!SUM_TFam!"],
                                                 ["RegSqMiles", "!SUM_SqMiles!"],
                                                 ["RegPovDens", "!RegTPov! / !RegSqMiles!"]])
    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    # SPATIAL JOIN TRACTS FILE WITH COUNTY FEATURE CLASS
    ap.SpatialJoin_analysis(working_file, cw, twcw)
    print("---------------------------")
    print("County Spaital Join")

    # SPATIAL JOIN TRACTS FILE WITH REGION FILE
    ap.SpatialJoin_analysis(twcw, rw, twrw)
    print("---------------------------")
    print("Region Spaital Join")

    # identify blockgroups as greater than county and regional average
    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3", fields="CoPovBG 'ifBlock(!PPov!, !CoPPov!)';RegPovBG 'ifBlock(!PPov!, !RegPPov!)'", code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, places, twrw_places)
    print("---------------------------")
    print("Places Spaital Join")

   # ! is this handled in cleanup now?
    # # CREATE FINAL FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    # print("---------------------------")

    # for field in delete_fields:
    #     ap.DeleteField_management(final_file, field)
    #     print("---------------------------")
    #     print(field + " DELETED")
    #     print("---------------------------")
    #
    # print("Poverty_Final feature class created - Script Complete!!!")
    #
    # ap.ClearWorkspaceCache_management()
    #
    # deleteFeatureClass(final_file, final_gdb_loc)
    #
    # # CREATE FINAL FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(final_file, final_gdb_loc, final_file)
    # print("---------------------------")

    # remove these unnecessary fields in the cleanup stage
    delete_fields = ['GEOID_1','SUM_TFam','SUM_TPov','SUM_TFam','SUM_SqMiles','SUM_TFam_1','SUM_TPov_1','SUM_TFam_1','SUM_SqMiles_1', 
                     'Join_Count','TARGET_FID','Join_Count_1','TARGET_FID_1','Join_Count_12','TARGET_FID_12','B17010e1','C17002e1','C17002e2', 
                     'C17002e3','C17002e4','C17002e5','Shape_Length_12','Shape_Area_12','ALAND_1','AWATER_1','COUNTYFP_1','Shape_Length_1',
                     'Shape_Area_1','STATEFP_1','PLACEFP','PLACENS','AFFGEOID','GEOID_12','LSAD','Shape_Length_1','Shape_Area_1','COUTNYFP_1']

    cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)