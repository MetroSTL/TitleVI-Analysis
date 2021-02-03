import arcpy as ap
import os
import shutil

from helpers import *


def lowCar(year, root_dir, tracts_mergegdb, region, places, tracts_file, commute_file, final_gdb_loc):
    gdb = f"LowCar{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year
    ap.ClearWorkspaceCache_management()

    outputgdb = ap.env.workspace
    working_file = "LowCar_working"

    working_gdb = os.path.join(root_dir, gdb)

    cw = os.path.join(working_gdb, "NoCar_working_County")
    cw_file = f"NoCar{year}_Working_County"
    rw = os.path.join(working_gdb, "NoCar_working_Reg")
    rw_file = f"NoCar{year}_Working_Reg"
    twcw_file = f"NoCar{year}_working_CountyJoin"
    twcw = os.path.join(working_gdb, twcw_file)
    twrw_file = f"NoCar{year}_working_RegJoin"
    twrw = os.path.join(working_gdb, twrw_file)
    twrw_places_file = f"NoCar{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(working_gdb, twrw_places_file)
    final_file = f"NoCar{year}_final"

    delete_fields = ["Join_Count", "TARGET_FID", "Join_Count", "TARGET_FID", "B08201e2", "B08201e3", "B08201e1",
                     "B08201e2", "B08201e3", "SUM_THH", "SUM_TNoCar", "SUM_TOneCar", "SUM_SqMiles", "SUM_THH_1",
                     "SUM_TNoCar_1", "SUM_TOneCar_1", "SUM_SqMiles_1", "Shape_Length_12", "Shape_Area_12"]

    replaceGDB(root_dir, gdb)

    
    fields_list = ["B08201e1", "B08201e2", "B08201e3"]

    # clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file, join_table, fields_list)
    clipPolygons(tracts_mergegdb, tracts_file, region, os.path.join(root_dir, gdb), working_file)
    # joinAndCalcFields(fc, census_gdb, output_gdb, key, table, table_key, fields_list)
    joinAndCalcFields(working_file, tracts_mergegdb, os.path.join(root_dir, gdb), 'GEOID_Data', commute_file, 'GEOID', fields_list)


    # ADDING ALL OF THE FIELDS TO TRACTS WORKING
    ap.management.AddFields(working_file,
                            [["THH", "DOUBLE"],
                             ["TNoCar", "DOUBLE"],
                             ["TOneCar", "DOUBLE"],
                             ["TLowCar", "LONG"],
                             ["PNoCar", "DOUBLE"],
                             ["POneCar", "DOUBLE"],
                             ["PLowCar", "DOUBLE"],
                             ["NoCarDens", "DOUBLE"],
                             ["OneCarDens", "DOUBLE"],
                             ["LowCarDens", "DOUBLE"]

                             ])

    print("Added fields")

    # CALCULATE OUT TRACT CENSUS VALUES
    ap.CalculateFields_management(working_file, "PYTHON3",
                                  [["SqMiles", "!shape.area@squaremiles!"],
                                   ["THH", "!B08201e1!"],
                                   ["TNoCar", "!B08201e2!"],
                                   ["TOneCar", "!B08201e3!"],
                                   ['TLowCar', '!B08201e2! + !B08201e3!'],
                                   ['PNoCar', '!B08201e2!/!B08201e1!'],
                                   ['POneCar', '!B08201e3!/!B08201e1!'],
                                   ['PLowCar', '!TLowCar!/!B08201e1!']])
    print("Finished calculating Population, Total No Car, Total One Car, and Total Low Car")

    # CALCULATE OUT TRACT CENSUS DENSITIES
    ap.CalculateFields_management(working_file, "PYTHON3",
                                  [["NoCarDens", "!TNoCar!/!SqMiles!"],
                                   ['OneCarDens', '!TOneCar!/!SqMiles!'],
                                   ['LowCarDens', '!TLowCar! / !SqMiles!']])
    print("Finished calculating Population, Total No Car, and Total One Car")

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["THH", "SUM"],["TNoCar", "SUM"],["TOneCar", "SUM"],["TLowCar", "SUM"],["SqMiles", "SUM"]])
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [["THH", "SUM"],["TNoCar", "SUM"],["TOneCar", "SUM"],["TLowCar", "SUM"],["SqMiles", "SUM"]])
    print("Dissolve Region Stats")

    # ADD COUNTY VALUE FIELDS
    ap.management.AddFields(cw,
                            [["CoTHH", "DOUBLE"],
                             ["CoTNoCar", "DOUBLE"],
                             ["CoTOneCar", "DOUBLE"],
                             ["CoTLowCar", "DOUBLE"],
                             ["CoPNoCar", "DOUBLE"],
                             ["CoPOneCar", "DOUBLE"],
                             ["CoPLowCar", "DOUBLE"],
                             ["CoSqMiles", "DOUBLE"],
                             ["CoNoCarDens", "DOUBLE"],
                             ["CoOneCarDens", "DOUBLE"],
                             ["CoLowCarDens", "DOUBLE"],
                             ["CoAbvNoCar", "SHORT", '', '', '', 0],
                             ["CoAbvOneCar", "SHORT", '', '', '', 0],
                             ["CoAbvLowCar", "SHORT", '', '', '', 0]])

    print(cw_file + " fields added !!!")

    # ADD REGION VALUE FIELDS
    ap.management.AddFields(rw,
                            [["RegTHH", "DOUBLE"],
                             ["RegTNoCar", "DOUBLE"],
                             ["RegPNoCar", "DOUBLE"],
                             ["RegTOneCar", "DOUBLE"],
                             ["RegPOneCar", "DOUBLE"],
                             ["RegTLowCar", "DOUBLE"],
                             ["RegPLowCar", "DOUBLE"],
                             ["RegSqMiles", "DOUBLE"],
                             ["RegNoCarDens", "DOUBLE"],
                             ["RegOneCarDens", "DOUBLE"],
                             ["RegLowCarDens", "DOUBLE"],
                             ["RegAbvNoCar", "SHORT", '', '', '', 0],
                             ["RegAbvOneCar", "SHORT", '', '', '', 0],
                             ["RegAbvLowCar", "SHORT", '', '', '', 0]])

    print(rw_file + " fields added !!!")

    # CALCULATE COUNTY VALUES
    # ap.CalculateFields_management(cw, "PYTHON3",[["CoTHH", "!SUM_THH!"],["CoTNoCar", "!SUM_TNoCar!"],["CoTOneCar", "!SUM_TOneCar!"],["CoTLowCar", "!SUM_TLowCar!"],["CoSqMiles", "!SUM_SqMiles!"]])
    ap.CalculateFields_management(cw, "PYTHON3",[["CoTHH", "!SUM_THH!"],["CoTNoCar", "!SUM_TNoCar!"],["CoTOneCar", "!SUM_TOneCar!"],["CoTLowCar", "!SUM_TLowCar!"],["CoSqMiles", "!SUM_SqMiles!"]])

    print(cw_file + " fields calculated !!!")

    # CALCULATE REGIONAL VALUES
    ap.CalculateFields_management(rw, "PYTHON3",[["RegTHH", "!SUM_THH!"],["RegTNoCar", "!SUM_TNoCar!"],["RegTOneCar", "!SUM_TOneCar!"],["RegTLowCar", "!SUM_TLowCar!"],["RegSqMiles", "!SUM_SqMiles!"]])
    print(rw_file + " fields calculated !!!")

    # SPATIAL JOIN TRACTS FILE WITH COUNTY FILE
    ap.SpatialJoin_analysis(working_file, cw, twcw)
    print("County Spaital Join")

    # SPATIAL JOIN TRACTS FILE WITH REGION FILE
    ap.SpatialJoin_analysis(twcw, rw, twrw)
    print("Region Spaital Join")

    # CALCULATE OUT LOW CAR AND DENSITIES FOR COUNTYIES AND REGION ON TRACT FILE
    ap.CalculateFields_management(twrw, "PYTHON3",
                                  [["CoPNoCar", "!CoTNoCar!/!CoTHH!"],
                                   ["RegPNoCar", "!RegTNoCar!/!RegTHH!"],
                                   ["CoPOneCar", "!CoTOneCar!+!CoTHH!"],
                                   ["RegPOneCar", "!RegTOneCar!+!RegTHH!"],
                                   ["CoTLowCar", "!CoTOneCar!+!CoTNoCar!"],
                                   ["RegTLowCar", "!RegTOneCar!+!RegTNoCar!"],
                                   ["CoOneCarDens", "!CoTOneCar!/!CoSqMiles!"],
                                   ["RegOneCarDens", "!RegTOneCar!/!RegSqMiles!"],
                                   ["CoNoCarDens", "!CoTNoCar!/!CoSqMiles!"],
                                   ["RegNoCarDens", "!RegTNoCar!/!RegSqMiles!"],
                                   ["CoLowCarDens", "(!CoTOneCar! + !CoTNoCar!) / !CoSqMiles!"],
                                   ["RegLowCarDens", "(!RegTOneCar! + !RegTNoCar!) / !RegSqMiles!"]])
    print('Calculated County and Regional Statistics')

    # CALCULATE OUT ABOVE REGIONAL AND COUNTY AVERAGE DENSITIES FOR TRACTS
    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoAbvNoCar 'ifBlock(!PNoCar!, !CoPNoCar!)';RegAbvNoCar 'ifBlock(!PNoCar!, !RegPNoCar!)';CoAbvLowCar 'ifBlock(!PLowCar!, !CoPLowCar!)';RegAbvLowCar 'ifBlock(!PLowCar!, !RegPLowCar!)';CoAbvOneCar 'ifBlock(!POneCar!, !CoPOneCar!)';RegAbvOneCar 'ifBlock(!POneCar!, !RegPOneCar!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("Above Car Density Calculations Completed")

    ap.SpatialJoin_analysis(twrw, places, twrw_places)
    print("")
    print("---------------------------")
    print("Places Spaital Join")

    # CREATE FINAL FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    # print("NoCar_final feature class created - Script Complete!!!")

    # # FOR LOOP FOR CLEANING UP TABLE BY DELETING OUT ALL OF THE FIELDS IN THE DELETE_FIELDS LIST
    # for field in delete_fields:
    #     ap.DeleteField_management(final_file, field)
    #     print(field + " DELETED")
    #
    #
    # deleteFeatureClass(final_file, final_gdb_loc)
    # ap.ClearWorkspaceCache_management()
    #
    # # CREATE FINAL FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(final_file, final_gdb_loc, final_file)
    # print("---------------------------")

    cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)