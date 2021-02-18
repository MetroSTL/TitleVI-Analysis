import arcpy as ap
import os
import shutil

from helpers import *

def minority(year, root_dir, bg_mergegdb, region, places, bg_file, race_file, hisp_file, final_gdb_loc):
    gdb = f"Minority{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year

    ap.ClearWorkspaceCache_management()

    outputgdb = ap.env.workspace
    working_file = f"Minority{year}_working"

   #  race_table = os.path.join(bg_mergegdb, race_file)
   #  hisp_table = os.path.join(bg_mergegdb, hisp_file)
   #  bg = os.path.join(bg_mergegdb, bg_file)
   #  working_gdb = os.path.join(root_dir, gdb)

    # Working file locations
    cw_file = f"Minority{year}_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = f"Minority{year}_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = f"Minority{year}_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = f"Minority{year}_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    twrw_places_file = f"Minority{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    final_file = f"Minority{year}_Final"
    final = os.path.join(outputgdb, final_file)

    delete_fields = ["Join_Count", "Join_Count_1", "TARGET_FID_12", "Target_FID", "Target_FID_1", "Join_Count_12",
                     "Geoid_1", "B02001e1", "B02001e2", "B02001e3", "B02001e4", "B02001e5", "B02001e6", "B02001e7",
                     "B02001e8", "B02001e9", "B02001e10", "B03002e13", "SUM_TPop", "SUM_TMinority", "SUM_SqMiles",
                     "SUM_TPop_1", "SUM_TMinority_1", "SUM_SqMiles_1", "GEOID_12_13", "PLACENS", "PLACEFP", "STATEFP_1",
                     "SHAPE_LENGTH_12", "SHAPE_AREA_12", "SHAPE_LENGTH_1", "SHAPE_LENGTH_1", "COUNTYFP_1", "GEOID_12", "SUM_TWhite",
                     "SUM_TBlack", "SUM_TNativeAm", "SUM_TAsian", "SUM_TPacIsland", "SUM_TOther", "SUM_THispanic",
                     "SUM_TWhite_1", "SUM_TBlack_1", "SUM_TNativeAm_1", "SUM_TAsian_1", "SUM_TPacIsland_1", "SUM_TOther_1", "SUM_THispanic_1"]

    replaceGDB(root_dir, gdb)

    race_fields_list = ["B02001e1", "B02001e3", "B02001e4", "B02001e5", "B02001e6", "B02001e7", "B02001e8"]
    hisp_fields_list = ["B03002e13"]

    # clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file, join_table, fields_list)
    clipPolygons(bg_mergegdb, bg_file, region, os.path.join(root_dir, gdb), working_file)
    # joinAndCalcFields(fc, census_gdb, output_gdb, key, table, table_key, fields_list)
    joinAndCalcFields(working_file, bg_mergegdb, os.path.join(root_dir, gdb), 'GEOID_Data', race_file, 'GEOID', race_fields_list)
    joinAndCalcFields(working_file, bg_mergegdb, os.path.join(root_dir, gdb), 'GEOID_Data', hisp_file, 'GEOID', hisp_fields_list)


    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ["TPop", "DOUBLE"],
                                           ["TMinority", "DOUBLE"],
                                           ["PMinority", "DOUBLE"],
                                           ["MinorityDens", "DOUBLE"],
                                           ["CoMinBG", "SHORT"],
                                           ["RegMinBG", "SHORT"],
                                           ["TBlack", "DOUBLE"],
                                           ["TNativeAm", "DOUBLE"],
                                           ["TAsian", "DOUBLE"],
                                           ["TPacIsland", "DOUBLE"],
                                           ["TOther", "DOUBLE"],
                                           ["THispanic", "DOUBLE"],
                                           ["TTwoOrMore", "DOUBLE"],
                                           ["PWhite", "DOUBLE"],
                                           ["PBlack", "DOUBLE"],
                                           ["PNativeAm", "DOUBLE"],
                                           ["PNative", "DOUBLE"],
                                           ["PAsian", "DOUBLE"],
                                           ["PPacIsland", "DOUBLE"],
                                           ["POther", "DOUBLE"],
                                           ["PTwoOrMore", "DOUBLE"],
                                           ["PHispanic", "DOUBLE"]])

    ap.CalculateFields_management(working_file, "PYTHON3", [["SqMiles", "!shape.area@squaremiles!"],
                                                            ["TPop", "!B02001e1!"],
                                                            ["TMinority", "!B02001e3! + !B02001e4! + !B02001e5! + !B02001e6! + !B02001e7! + !B02001e8! + !B03002e13!"],
                                                            ["PMinority", "!TMinority! / !TPop!"],
                                                            ["MinorityDens", "!TMinority! / !SqMiles!"],
                                                            ["TBlack", "!B02001e3!"],
                                                            ["TNativeAm", "!B02001e4!"],
                                                            ["TAsian", "!B02001e5!"],
                                                            ["TPacIsland", "!B02001e6!"],
                                                            ["TOther", "!B02001e7!"],
                                                            ["TTwoOrMore", "!B02001e8!"],
                                                            ["THispanic", "!B03002e13!"],
                                                            ["PBlack", "!TBlack! / !TPop!"],
                                                            ["PNativeAm", "!TNativeAm! / !TPop!"],
                                                            ["PAsian", "!TAsian! / !TPop!"],
                                                            ["PPacIsland", "!TPacIsland! / !TPop!"],
                                                            ["POther", "!TOther! / !TPop!"],
                                                            ["PTwoOrMore", "!TTwoOrMore! / !TPop!"],
                                                            ["PHispanic", "!THispanic! / !TPop!"]])

    print("---------------------------")
    print("Finished calculating Minority Calcs")

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["TPop", "SUM"],
                                                          ["TMinority", "SUM"],
                                                          ["SqMiles", "SUM"],
                                                          ["TBlack", "SUM"],
                                                          ["TNativeAm", "SUM"],
                                                          ["TAsian", "SUM"],
                                                          ["TPacIsland", "SUM"],
                                                          ["TOther", "SUM"],
                                                          ["THispanic", "SUM"]])
    print("---------------------------")
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [["TPop", "SUM"],
                                                  ["TMinority", "SUM"],
                                                  ["SqMiles", "SUM"],
                                                  ["TBlack", "SUM"],
                                                  ["TNativeAm", "SUM"],
                                                  ["TAsian", "SUM"],
                                                  ["TPacIsland", "SUM"],
                                                  ["TOther", "SUM"],
                                                  ["THispanic", "SUM"]])
    print("---------------------------")
    print("Dissolve Region Stats")

    ap.management.AddFields(cw, [["CoTPop", "Double"],
                                 ["CoTMinority", "Double"],
                                 ["CoPMinority", "Double"],
                                 ["CoSqMiles", "Double"],
                                 ["CoMinorityDens", "Double"],
                                 ["CoTBlack", "DOUBLE"],
                                 ["CoTNativeAm", "DOUBLE"],
                                 ["CoTAsian", "DOUBLE"],
                                 ["CoTPacIsland", "DOUBLE"],
                                 ["CoTOther", "DOUBLE"],
                                 ["CoTHispanic", "DOUBLE"],
                                 ["CoPWhite", "DOUBLE"],
                                 ["CoPBlack", "DOUBLE"],
                                 ["CoPNativeAm", "DOUBLE"],
                                 ["CoPAsian", "DOUBLE"],
                                 ["CoPPacIsland", "DOUBLE"],
                                 ["CoPOther", "DOUBLE"],
                                 ["CoPHispanic", "DOUBLE"]])

    ap.CalculateFields_management(cw, "PYTHON", [["CoTPop", "!SUM_TPop!"],
                                                 ["CoTMinority", "!SUM_TMinority!"],
                                                 ["CoPMinority", "!CoTMinority! / !CoTPop!"],
                                                 ["CoSqMiles", "!SUM_SqMiles!"],
                                                 ["CoMinorityDens", "!CoTMinority! / !CoSqMiles!"],
                                                 ["CoTBlack", "!SUM_TBlack!"],
                                                 ["CoTNativeAm", "!SUM_TNativeAm!"],
                                                 ["CoTAsian", "!SUM_TAsian!"],
                                                 ["CoTPacIsland", "!SUM_TPacIsland!"],
                                                 ["CoTOther", "!SUM_TOther!"],
                                                 ["CoPBlack", "!SUM_TBlack! / !SUM_TPop!"],
                                                 ["CoPNativeAm", "!SUM_TNativeAm! / !SUM_TPop!"],
                                                 ["CoPAsian", "!SUM_TAsian! / !SUM_TPop!"],
                                                 ["CoPPacIsland", "!SUM_TPacIsland! / !SUM_TPop!"],
                                                 ["CoPOther", "!SUM_TOther! / !SUM_TPop!"],
                                                 ["CoPHispanic", "!SUM_TOther! / !SUM_TPop!"]])

    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    ap.management.AddFields(rw, [["RegTPop", "Double"],
                                 ["RegTMinority", "Double"],
                                 ["RegPMinority", "Double"],
                                 ["RegSqMiles", "Double"],
                                 ["RegMinorityDens", "Double"],
                                 ["RegTBlack", "DOUBLE"],
                                 ["RegTNativeAm", "DOUBLE"],
                                 ["RegTAsian", "DOUBLE"],
                                 ["RegTPacIsland", "DOUBLE"],
                                 ["RegTOther", "DOUBLE"],
                                 ["RegTHispanic", "DOUBLE"],
                                 ["RegPBlack", "DOUBLE"],
                                 ["RegPNativeAm", "DOUBLE"],
                                 ["RegPAsian", "DOUBLE"],
                                 ["RegPPacIsland", "DOUBLE"],
                                 ["RegPOther", "DOUBLE"],
                                 ["RegPHispanic", "DOUBLE"]])

    ap.CalculateFields_management(rw, "PYTHON", [["RegTPop", "!SUM_TPop!"],
                                                 ["RegTMinority", "!SUM_TMinority!"],
                                                 ["RegPMinority", "!RegTMinority! / !RegTPop!"],
                                                 ["RegSqMiles", "!SUM_SqMiles!"],
                                                 ["RegMinorityDens", "!RegTMinority! / !RegSqMiles!"],
                                                 ["RegTBlack", "!SUM_TBlack!"],
                                                 ["RegTNativeAm", "!SUM_TNativeAm!"],
                                                 ["RegTAsian", "!SUM_TAsian!"],
                                                 ["RegTPacIsland", "!SUM_TPacIsland!"],
                                                 ["RegTOther", "!SUM_TOther!"],
                                                 ["RegTHispanic", "!SUM_THispanic!"],
                                                 ["RegPBlack", "!SUM_TBlack! / !SUM_TPop!"],
                                                 ["RegPNativeAm", "!SUM_TNativeAm! / !SUM_TPop!"],
                                                 ["RegPAsian", "!SUM_TAsian! / !SUM_TPop!"],
                                                 ["RegPPacIsland", "!SUM_TPacIsland! / !SUM_TPop!"],
                                                 ["RegPOther", "!SUM_TOther! / !SUM_TPop!"],
                                                 ["RegPHispanic", "!SUM_THispanic! / !SUM_TPop!"]])

    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    # SPATIAL JOIN TRACTS FILE WITH RegUNTY FILE
    ap.SpatialJoin_analysis(working_file, cw, twcw)
    print("---------------------------")
    print("County Spaital Join")

    # SPATIAL JOIN TRACTS FILE WITH REGION FILE
    ap.SpatialJoin_analysis(twcw, rw, twrw)
    print("---------------------------")
    print("Region Spaital Join")


    # NEW WAY OF CALCULATION USING PERCENTAGE
    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoMinBG 'ifBlock(!PMinority!, !CoPMinority!)';RegMinBG 'ifBlock(!PMinority!, !RegPMinority!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)

    # OLD WAY OF CALCULATION USING DENSITY
    # ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
    #                               fields="CoMinBG 'ifBlock(!MinorityDens!, !CoMinorityDens!)';RegMinBG 'ifBlock(!MinorityDens!, !RegMinorityDens!)'",
    #                               code_block="""def ifBlock(area, region):
    #   if area > region:
    #      return 1
    #   else:
    #      return 0
    #      """)
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, places, twrw_places)
    print("---------------------------")
    print("Places Spaital Join")


    # for field in delete_fields:
    #     ap.DeleteField_management(twrw_places, field)
    #     print("---------------------------")
    #     print(field + " DELETED")
    #     print("---------------------------")
    #
    # print("Minority_Final feature class created - Script Complete!!!")
    #
    # ap.ClearWorkspaceCache_management()
    #
    # deleteFeatureClass(final_file, final_gdb_loc)
    #
    # # CREATE FINAL FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(final_file, final_gdb_loc, final_file)
    # print("---------------------------")

    cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)