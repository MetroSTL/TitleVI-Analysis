import arcpy as ap
import os
import shutil

from helpers import *

# ! is this one less updated? since it's only used in TNI?


def medHHInc(year, root_dir, bg_mergegdb, region, places, bg_file, inc_file, final_gdb_loc):

    gdb = f"MedHHInc{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year
    ap.ClearWorkspaceCache_management()
    outputgdb = ap.env.workspace


    # LOCAL VARIABLES
    inc_table = os.path.join(bg_mergegdb, inc_file)
    working_file = f"MedHHInc{year}_working"
    cw_file = f"MedHHInc{year}_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = f"MedHHInc{year}_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = f"MedHHInc{year}_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = f"MedHHInc{year}_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    final_file = f"MedHHInc{year}_Final"
    twrw_places_file = f"MedHHInc{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)


    # TODO: UPDATE THIS

    delete_fields = ['B19001e1', 'B19049e1', 'COUNTYFP_1', 'SUM_THH', 'SUM_SqMiles', 'MEDIAN_MedHHInc',
                     'Shape_Length_1', 'Shape_Area_1', 'SUM_THH_1', 'SUM_SqMiles_1', 'MEDIAN_MedHHInc_1',
                     'Shape_Length_12', 'Shape_Area_12', 'STATEFP_1', 'PLACEFP', 'PLACENS', 'AFFGEOID', 'GEOID_12',
                     'LSAD', 'ALAND_1', 'AWATER_1', 'TARGET_FID_12', 'Join_Count_12', 'TARGET_FID_12', 'TARGET_FID', 'Join_Count']

    replaceGDB(root_dir, gdb)

    fields_list = ['B19001e1','B19049e1']
    
    clipPolygons(bg_mergegdb, bg_file, region, os.path.join(root_dir, gdb), working_file)
    joinAndCalcFields(working_file, bg_mergegdb, os.path.join(root_dir, gdb), 'GEOID_Data', inc_file, 'GEOID', fields_list)
    

    ap.env.workspace = outputgdb
    ap.management.AddFields(working_file, [["THH", "DOUBLE"],
                                           ["MedHHInc", "Double"],
                                           ["CoBelMedInc", "DOUBLE"],
                                           ["RegBelMedInc", "DOUBLE"]])

    ap.CalculateFields_management(working_file, "PYTHON3", [["THH", "!B19001e1!"],
                                                            ["MedHHInc", "!B19049e1!"]])


    # get rid of all of the census fields
    ap.DeleteField_management(working_file, fields_list)

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["THH", "SUM"],
                                                          ["SqMiles", "SUM"],
                                                          ["MedHHInc", "MEDIAN"]])
    print("")
    print("---------------------------")
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [
        ["THH", "SUM"],
        ["SqMiles", "SUM"],
        ["MedHHInc", "MEDIAN"]])
    print("")
    print("---------------------------")
    print("Dissolve Region Stats")

    ap.management.AddFields(cw, [["CoTHH", "DOUBLE"],
                                 ["CoMedHHInc", "DOUBLE"]])

    ap.CalculateFields_management(cw, "PYTHON", [["CoTHH", "!SUM_THH!"],
                                                 ["CoMedHHInc", "!Median_MedHHInc!"]])

    print("")
    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    ap.management.AddFields(rw, [["RegTHH", "DOUBLE"],
                                 ["RegMedHHInc", "DOUBLE"]])

    ap.CalculateFields_management(rw, "PYTHON", [["RegTHH", "!SUM_THH!"],
                                                 ["RegMedHHInc", "!Median_MedHHInc!"]])
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

    print("")

    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",fields="CoBelMedInc 'ifBlock(!MedHHInc!, !CoMedHHInc!)';RegBelMedInc 'ifBlock(!MedHHInc!, !RegMedHHInc!)'",code_block='''def ifBlock(area, region):
      if area < region:
         return 1
      else:
         return 0''')
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, places, twrw_places)
    print("")
    print("---------------------------")
    print("Places Spaital Join")


    # for field in delete_fields:
    #     try:
    #         ap.DeleteField_management(twrw_places, field)
    #         print("")
    #         print("---------------------------")
    #         print(field + " DELETED")
    #         print("---------------------------")
    #     except:
    #         print(field + ' does not exist')
    #
    # ap.ClearWorkspaceCache_management()
    #
    # deleteFeatureClass(final_file, final_gdb_loc)
    #
    # # CREATE FINAL FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    # print("")
    # print("---------------------------")
    # print("MedHHInc_Final feature class created - Script Complete!!!")

    cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)