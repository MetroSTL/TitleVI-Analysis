import arcpy as ap
import os
import shutil

from helpers import *


def senior(year, root_dir, bg_mergedgdb, region, places, bg_file, sen_file, final_gdb_loc):
    gdb = f"Senior{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = f"Senior{year}_working"

    bg = os.path.join(bg_mergedgdb, bg_file)
    working_gdb = os.path.join(root_dir, gdb)

    # Working file locations
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

    list = ['B01001e20', 'B01001e21', 'B01001e22', 'B01001e23', 'B01001e24', 'B01001e25', 'B01001e44', 'B01001e45',
            'B01001e46', 'B01001e47', 'B01001e48', 'B01001e49', 'B01001e1', 'Join_Count', 'TARGET_FID',
            'Join_Count_1', 'TARGET_FID_1', 'Join_Count_12', 'TARGET_FID_12', 'COUNTYFP_1', 'SUM_TPop', 'SUM_SqMiles',
            'SUM_TSenior', 'Shape_Length_1', 'Shape_Area_1', 'CoAbvSenior_1', 'SUM_TPop_1', 'SUM_SqMiles_1',
            'SUM_TSenior_1', 'Shape_Length_12', 'Shape_Area_12', 'RegSqMiles', 'RegAbvSenior_1', 'STATEFP_1', 'PLACEFP',
            'PLACENS', 'AFFGEOID', 'GEOID_1', 'LSAD', 'ALAND_1', 'AWATER_1']

    # CREATE WORKING GDB
    replaceGDB(root_dir, gdb)

    # ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file,
    #                                          "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    # print("")
    # print("---------------------------")
    # print(working_file + " Created!!!")

    # ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=senior_table, join_field="GEOID",
    #                         fields="B01001e1;B01001e20;B01001e21;B01001e22;B01001e23;B01001e24;B01001e25;B01001e44;B01001e45;B01001e46;B01001e47;B01001e48;B01001e49")


    
    # print("")
    # print("---------------------------")
    # print("Finished calculating Senior Calcs")

    fields_list = ['B01001e1', 'B01001e20', 'B01001e21', 'B01001e22', 'B01001e23', 'B01001e24', 'B01001e25', 'B01001e44', 'B01001e45', 'B01001e46', 'B01001e47', 'B01001e48', 'B01001e49']

    # clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file, join_table, fields_list)
    clipPolygons(bg_mergedgdb, bg_file, region, os.path.join(root_dir, gdb), working_file)
    joinAndCalcFields(working_file, bg_mergedgdb, os.path.join(root_dir, gdb), 'GEOID_Data', sen_file, 'GEOID', fields_list)


    ap.env.workspace = outputgdb

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ['TPop', 'DOUBLE'],
                                           ["TSenior", "DOUBLE"],
                                           ["PSenior", "Double"],
                                           ["SeniorDens", "DOUBLE"],
                                           ["CoAbvSenior", "SHORT"],
                                           ["RegAbvSenior", "SHORT"]])

    ap.CalculateFields_management(working_file, 'PYTHON3', [['TPop', '!B01001e1!'],
                                                            ['TSenior',
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

    ap.management.AddFields(cw, [["CoSqMiles", "DOUBLE"],
                                 ["CoTPop", "DOUBLE"],
                                 ["CoTSenior", "DOUBLE"],
                                 ["CoPSenior", "Double"],
                                 ["CoSeniorDens", "DOUBLE"],
                                 ["CoAbvSenior", "DOUBLE"]])

    ap.CalculateFields_management(cw, "PYTHON", [["CoSqMiles", "!SUM_SqMiles!"],
                                                 ["CoTPop", "!SUM_TPop!"],
                                                 ["CoTSenior", "!SUM_TSenior!"],
                                                 ["CoPSenior", "!CoTSenior! / !CoTPop!"],
                                                 ["CoSeniorDens", "!CoTSenior! / !CoSqMiles!"]])

    print("")
    print("---------------------------")
    print(cw_file + " fields calculated !!!")

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

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    print("---------------------------")

    for field in list:
        ap.DeleteField_management(final_file, field)
        print("---------------------------")
        print(field + " DELETED")
        print("---------------------------")

    print("Senior_Final feature class created - Script Complete!!!")

    # CREATE FINAL FEATURE CLASS
    deleteFeatureClass(final_file, final_gdb_loc)
    ap.FeatureClassToFeatureClass_conversion(final_file, final_gdb_loc, final_file)
    print("---------------------------")
