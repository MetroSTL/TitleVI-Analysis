import arcpy as ap
import os
import shutil

# *******GLOBAL VARIABLES*****
year = str(input('What Year? "YY": '))
root_dir = r"C:\Users\wkjenkins\Documents\local_gis\titlevi"

# ACS GDB's ---> USE STANDARD ACS BLOCKGOUP AND TRACT FILES GDB FILES (https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-data.html)
bg_mergegdb = f"W:\Research&Development\Data-Share\layers\ACS\ACS_20{year}_5YR_BG\merge.gdb"
tracts_mergegdb = f"W:\Research&Development\Data-Share\layers\ACS\ACS_20{year}_5YR_TRACT\merge.gdb"

places = r'W:\Research&Development\Data-Share\layers\boundaries\muni\MO_IL_Places_2017.shp'
routes = r'W:\Research&Development\Data-Share\layers\trapeze\MetroBusRoutes\MetroBusRoutes_COA_190917.shp' # ------> Select Routes file




# GEOMETRY FILES
bg_file = f"ACS_20{year}_5YR_BG"
tracts_file = f"ACS_20{year}_5YR_TRACT"

# DB TABLES
inc_file = "X19_INCOME"
pov_file = "X17_POVERTY"
lep_file = "X16_LANGUAGE_SPOKEN_AT_HOME"
race_file = "X02_RACE"
hisp_file = "X03_HISPANIC_OR_LATINO_ORIGIN"
commute_table = "X08_COMMUTING"



def medHHInc(rdir, mgdb, plcs, bgf, incf):
    gdb = f"MedHHInc{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    bg = os.path.join(mgdb, bgf)

    # LOCAL VARIABLES
    gdb = f"MedHHInc{year}.gdb"
    inc_table = os.path.join(bg_mergegdb, incf)
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
    delete_fields = ['B19001e1', 'B19049e1', 'COUNTYFP_1', 'SUM_THH', 'SUM_SqMiles', 'MEDIAN_MedHHInc',
                     'Shape_Length_1', 'Shape_Area_1', 'SUM_THH_1', 'SUM_SqMiles_1', 'MEDIAN_MedHHInc_1',
                     'Shape_Length_12', 'Shape_Area_12', 'STATEFP_1', 'PLACEFP', 'PLACENS', 'AFFGEOID', 'GEOID_12',
                     'LSAD', 'ALAND_1', 'AWATER_1', 'TARGET_FID_12', 'Join_Count_12', 'TARGET_FID_12', 'TARGET_FID', 'Join_Count']

    if os.path.exists(outputgdb) and os.path.isdir(outputgdb):
        shutil.rmtree(outputgdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(rdir, gdb)
    print("GEODATABASE CREATED!!!")

    ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file, "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    print("")
    print("---------------------------")
    print(working_file + " Created!!!")

    ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=inc_table, join_field="GEOID", fields="B19001e1;B19049e1;GEOID")
    print("")
    print("---------------------------")
    print(working_file + " Joined with Income Table!!!")

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ["THH", "DOUBLE"],
                                           ["MedHHInc", "Double"],
                                           ["CoBelMedInc", "DOUBLE"],
                                           ["RegBelMedInc", "DOUBLE"]])

    ap.CalculateFields_management(working_file, "PYTHON3", [["SqMiles", "!shape.area@squaremiles!"],
                                                            ["THH", "!B19001e1!"],
                                                            ["MedHHInc", "!B19049e1!"]])

    print("")
    print("---------------------------")
    print("Finished calculating Median HH Inc Calcs")

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
    ap.SpatialJoin_analysis(twrw, plcs, twrw_places)
    print("")
    print("---------------------------")
    print("Places Spaital Join")

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    print("")
    print("---------------------------")
    print("MedHHInc_Final feature class created - Script Complete!!!")

    for field in delete_fields:
        ap.DeleteField_management(final_file, field)
        print("")
        print("---------------------------")
        print(field + " DELETED")
        print("---------------------------")

medHHInc(root_dir, bg_mergegdb, places, bg_file, inc_file)


def senior(rdir, mgdb, plcs, bgf, senf):
    gdb = f"Poverty{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = "Senior_working"

    sen_table = os.path.join(mgdb, senf)
    bg = os.path.join(mgdb, bgf)
    working_gdb = os.path.join(rdir, gdb)

    senior_file = "X01_AGE_AND_SEX"
    senior_table = os.path.join(mgdb, senior_file)

    # Working file locations
    cw_file = "Senior_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = "Senior_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = "Senior_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = "Senior_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    twrw_places_file = "Senior_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    final_file = "Senior_Final"
    final = os.path.join(outputgdb, final_file)

    list = ['B01001e20', 'B01001e21', 'B01001e22', 'B01001e23', 'B01001e24', 'B01001e25', 'B01001e44', 'B01001e45',
            'B01001e46', 'B01001e47', 'B01001e48', 'B01001e49', 'B01001e1']

    if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
        shutil.rmtree(working_gdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(root_dir, gdb)
    print("GEODATABASE CREATED!!!")

    ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file,
                                             "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    print("")
    print("---------------------------")
    print(working_file + " Created!!!")

    ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=senior_table, join_field="GEOID",
                            fields="B01001e1;B01001e20;B01001e21;B01001e22;B01001e23;B01001e24;B01001e25;B01001e44;B01001e45;B01001e46;B01001e47;B01001e48;B01001e49")

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ['TPop', 'DOUBLE'],
                                           ["TSenior", "DOUBLE"],
                                           ["PSenior", "Double"],
                                           ["SeniorDens", "DOUBLE"],
                                           ["CoAbvSenior", "SHORT"],
                                           ["RegAbvSenior", "SHORT"]])

    ap.CalculateFields_management(working_file, 'PYTHON3', [['SqMiles', '!shape.area@squaremiles!'],
                                                            ['TPop', '!B01001e1!'],
                                                            ['TSenior',
                                                             '!B01001e44! + !B01001e45! + !B01001e46! + !B01001e47! + !B01001e48! + !B01001e49! + !B01001e20! + !B01001e21! + !B01001e22! + !B01001e23! + !B01001e24! + !B01001e25!'],
                                                            ['PSenior', '!TSenior! / !TPop!'],
                                                            ['SeniorDens', '!TSenior!/!SqMiles!']])

    print("")
    print("---------------------------")
    print("Finished calculating Senior Calcs")

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
                                  fields="CoAbvSenior 'ifBlock(!SeniorDens!, !CoSeniorDens!)';RegAbvSenior 'ifBlock(!SeniorDens!, !RegSeniorDens!)'",
                                  code_block="""def ifBlock(area, region):
      if area < region:
         return 1
      else:
         return 0
         """)
    print("")
    print("---------------------------")
    print("Above Senior Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, plcs, twrw_places)
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

senior(root_dir, bg_mergegdb, places, bg_file, inc_file)


def poverty(rdir, mgdb, plcs, bgf, incf):
    gdb = f"Poverty{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = "Poverty_working"

    pov_table = os.path.join(mgdb, incf)
    bg = os.path.join(mgdb, bgf)
    working_gdb = os.path.join(rdir, gdb)

    twrw_places_file = "Poverty_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    cw_file = "Poverty_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = "Poverty_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = "Poverty_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = "Poverty_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    final_file = "Poverty_Final"
    final = os.path.join(outputgdb, final_file)
    delete_fields = ['GEOID_1', 'SUM_TFam', 'SUM_TPov', 'SUM_TFam', 'SUM_SqMiles', 'SUM_TFam_1', 'SUM_TPov_1', 'SUM_TFam_1', 'SUM_SqMiles_1', 'Join_Count', 'TARGET_FID', 'Join_Count_1', 'TARGET_FID_1', 'Join_Count_12', 'TARGET_FID_12', 'B17010e1', 'C17002e1', 'C17002e2', 'C17002e3', 'C17002e4', 'C17002e5', 'Shape_Length_12', 'Shape_Area_12', 'ALAND_1', 'AWATER_1', 'COUNTYFP_1', 'Shape_Length_1', 'Shape_Area_1', 'STATEFP_1', 'PLACEFP', 'PLACENS', 'AFFGEOID', 'GEOID_12', 'LSAD', 'Shape_Length_1', 'Shape_Area_1', 'COUTNYFP_1', ]

    if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
        shutil.rmtree(working_gdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(root_dir, gdb)
    print("GEODATABASE CREATED!!!")

    ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file, "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    print("---------------------------")
    print(working_file + " Created!!!")

    ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=pov_table, join_field="GEOID",
                            fields="B17010e1;C17002e1;C17002e2;C17002e3;C17002e4;C17002e5;GEOID")
    print("---------------------------")
    print(working_file + " Joined with Income Table!!!")

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ["TFam", "DOUBLE"],
                                           ["TPov", "DOUBLE"],
                                           ['PPOV', "DOUBLE"],
                                           ["POVDens", "DOUBLE"],
                                           ["CoPovBG", "SHORT"],
                                           ["RegPovBG", "SHORT"]])
    print('Added Fields to working file')

    ap.CalculateFields_management(working_file, "PYTHON3", [["SqMiles", "!shape.area@squaremiles!"],
                                                            ["TFam", "!C17002e1!"],
                                                            ["TPov", "!C17002e2! + !C17002e3! + !C17002e4! + !C17002e5!"],
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

    ap.management.AddFields(cw, [["CoTFam", "DOUBLE"],
                                 ["CoTPov", "DOUBLE"],
                                 ["CoPPov", "DOUBLE"],
                                 ["CoSqMiles", "DOUBLE"],
                                 ["CoPovDens", "DOUBLE"]])

    ap.CalculateFields_management(cw, "PYTHON", [["CoTFam", "!SUM_TFam!"],
                                                 ["CoTPov", "!SUM_TPov!"],
                                                 ["CoPPov", "!SUM_TPov!/!SUM_TFam!"],
                                                 ["CoSqMiles", "!SUM_SqMiles!"],
                                                 ["CoPovDens", "!CoTPov! / !CoSqMiles!"]])
    print("---------------------------")
    print(rw_file + " fields calculated !!!")

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

    # SPATIAL JOIN TRACTS FILE WITH COUNTY FILE
    ap.SpatialJoin_analysis(working_file, cw, twcw)
    print("---------------------------")
    print("County Spaital Join")

    # SPATIAL JOIN TRACTS FILE WITH REGION FILE
    ap.SpatialJoin_analysis(twcw, rw, twrw)
    print("---------------------------")
    print("Region Spaital Join")

    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3", fields="CoPovBG 'ifBlock(!PovDens!, !CoPovDens!)';RegPovBG 'ifBlock(!PovDens!, !RegPovDens!)'", code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, plcs, twrw_places)
    print("---------------------------")
    print("Places Spaital Join")

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    print("---------------------------")

    for field in delete_fields:
        ap.DeleteField_management(final_file, field)
        print("---------------------------")
        print(field + " DELETED")
        print("---------------------------")

    print("MedHHInc_Final feature class created - Script Complete!!!")


poverty(root_dir, bg_mergegdb, places, bg_file, pov_file)



def lep(rdir, mgdb, plcs, bgf, lepf):
    gdb = f"LEP{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = "LEP_working"

    lep_table = os.path.join(mgdb, lepf)
    bg = os.path.join(mgdb, bgf)
    working_gdb = os.path.join(rdir, gdb)

    # Working file locations
    cw_file = "LEP_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = "LEP_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = "LEP_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = "LEP_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    twrw_places_file = "LEP_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    final_file = "LEP_Final"
    final = os.path.join(outputgdb, final_file)

    # LIST OF FIELDS TO DELETE
    delete_fields = ["Join_Count", "TARGET_FID", "Join_Count_1", "TARGET_FID_1", "Join_Count_12", "TARGET_FID_12",
                     "ALAND_1", "AWATER_1", "Shape_Length_12", "Shape_Area_12", "Shape_Length_1", "Shape_Area_1",
                     "GEOID_1", "B16004e1", "B16004e10", "B16004e11", "B16004e12", "B16004e13", "B16004e14",
                     "B16004e15", "B16004e16", "B16004e17", "B16004e18", "B16004e19", "B16004e2", "B16004e20",
                     "B16004e21", "B16004e22", "B16004e23", "B16004e24", "B16004e25", "B16004e26", "B16004e27",
                     "B16004e28", "B16004e29", "B16004e3", "B16004e30", "B16004e31", "B16004e32", "B16004e33",
                     "B16004e34", "B16004e35", "B16004e36", "B16004e37", "B16004e38", "B16004e39", "B16004e4",
                     "B16004e40", "B16004e41", "B16004e42", "B16004e43", "B16004e44", "B16004e45", "B16004e46",
                     "B16004e47", "B16004e48", "B16004e49", "B16004e5", "B16004e50", "B16004e51", "B16004e52",
                     "B16004e53", "B16004e54", "B16004e55", "B16004e56", "B16004e57", "B16004e58", "B16004e59",
                     "B16004e6", "B16004e60", "B16004e61", "B16004e62", "B16004e63", "B16004e64", "B16004e65",
                     "B16004e66", "B16004e67", "B16004e7", "B16004e8", "B16004e9", "B16004m1", "B16004m10", "B16004m11",
                     "B16004m12", "B16004m13", "B16004m14", "B16004m15", "B16004m16", "B16004m17", "B16004m18",
                     "B16004m19", "B16004m2", "B16004m20", "B16004m21", "B16004m22", "B16004m23", "B16004m24",
                     "B16004m25", "B16004m26", "B16004m27", "B16004m28", "B16004m29", "B16004m3", "B16004m30",
                     "B16004m31", "B16004m32", "B16004m33", "B16004m34", "B16004m35", "B16004m36", "B16004m37",
                     "B16004m38", "B16004m39", "B16004m4", "B16004m40", "B16004m41", "B16004m42", "B16004m43",
                     "B16004m44", "B16004m45", "B16004m46", "B16004m47", "B16004m48", "B16004m49", "B16004m5",
                     "B16004m50", "B16004m51", "B16004m52", "B16004m53", "B16004m54", "B16004m55", "B16004m56",
                     "B16004m57", "B16004m58", "B16004m59", "B16004m6", "B16004m60", "B16004m61", "B16004m62",
                     "B16004m63", "B16004m64", "B16004m65", "B16004m66", "B16004m67", "B16004m7", "B16004m8",
                     "B16004m9", "C16002e1", "C16002e10", "C16002e11", "C16002e12", "C16002e13", "C16002e14",
                     "C16002e2", "C16002e3", "C16002e4", "C16002e5", "C16002e6", "C16002e7", "C16002e8", "C16002e9",
                     "C16002m1", "C16002m10", "C16002m11", "C16002m12", "C16002m13", "C16002m14", "C16002m2",
                     "C16002m3", "C16002m4", "C16002m5", "C16002m6", "C16002m7", "C16002m8", "C16002m9", "GEOID",
                     "SUM_TPOP", "SUM_SqMiles", "SUM_TEngOnly", "SUM_TEngVW", "SUM_TLEP", "SUM_TLEPAsian",
                     "SUM_TLEPSpan", "SUM_TLEPEuro", "SUM_TLEPOther", "SUM_TPOP_1", "SUM_SqMiles_1", "SUM_TEngOnly_1",
                     "SUM_TEngVW_1", "SUM_TLEP_1", "SUM_TLEPAsian_1", "SUM_TLEPSpan_1", "SUM_TLEPEuro_1",
                     "SUM_TLEPOther_1"]

    if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
        shutil.rmtree(working_gdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(rdir, gdb)
    print("GEODATABASE CREATED!!!")

    # CREATE A NEW WORKING FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file,
                                             "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    print("")
    print("---------------------------")
    print(working_file + " Created!!!")

    # JOIN WORKING FEATURE CLASS TO CENSUS TABLE - FILTER OUT SELECT COUNTIES IN REGION
    ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=lep_table, join_field="GEOID",
                            fields="B16004e1;B16004e10;B16004e11;B16004e12;B16004e13;B16004e14;B16004e15;B16004e16;B16004e17;B16004e18;B16004e19;B16004e2;B16004e20;B16004e21;B16004e22;B16004e23;B16004e24;B16004e25;B16004e26;B16004e27;B16004e28;B16004e29;B16004e3;B16004e30;B16004e31;B16004e32;B16004e33;B16004e34;B16004e35;B16004e36;B16004e37;B16004e38;B16004e39;B16004e4;B16004e40;B16004e41;B16004e42;B16004e43;B16004e44;B16004e45;B16004e46;B16004e47;B16004e48;B16004e49;B16004e5;B16004e50;B16004e51;B16004e52;B16004e53;B16004e54;B16004e55;B16004e56;B16004e57;B16004e58;B16004e59;B16004e6;B16004e60;B16004e61;B16004e62;B16004e63;B16004e64;B16004e65;B16004e66;B16004e67;B16004e7;B16004e8;B16004e9;B16004m1;B16004m10;B16004m11;B16004m12;B16004m13;B16004m14;B16004m15;B16004m16;B16004m17;B16004m18;B16004m19;B16004m2;B16004m20;B16004m21;B16004m22;B16004m23;B16004m24;B16004m25;B16004m26;B16004m27;B16004m28;B16004m29;B16004m3;B16004m30;B16004m31;B16004m32;B16004m33;B16004m34;B16004m35;B16004m36;B16004m37;B16004m38;B16004m39;B16004m4;B16004m40;B16004m41;B16004m42;B16004m43;B16004m44;B16004m45;B16004m46;B16004m47;B16004m48;B16004m49;B16004m5;B16004m50;B16004m51;B16004m52;B16004m53;B16004m54;B16004m55;B16004m56;B16004m57;B16004m58;B16004m59;B16004m6;B16004m60;B16004m61;B16004m62;B16004m63;B16004m64;B16004m65;B16004m66;B16004m67;B16004m7;B16004m8;B16004m9;C16002e1;C16002e10;C16002e11;C16002e12;C16002e13;C16002e14;C16002e2;C16002e3;C16002e4;C16002e5;C16002e6;C16002e7;C16002e8;C16002e9;C16002m1;C16002m10;C16002m11;C16002m12;C16002m13;C16002m14;C16002m2;C16002m3;C16002m4;C16002m5;C16002m6;C16002m7;C16002m8;C16002m9;GEOID")
    print("")
    print("---------------------------")
    print(working_file + " Joined with LEP Table!!!")

    # ADDING ALL THE BLOCK GROUP CENSUS FIELDS
    ap.management.AddFields(working_file,
                            [["TPOP", "DOUBLE"],
                             ["SqMiles", "DOUBLE"],
                             ["TEngOnly", "DOUBLE"],
                             ["TEngVW", "DOUBLE"],
                             ["PEngVW", "DOUBLE"],
                             ["TLEP", "DOUBLE"],
                             ["PLEP", "DOUBLE"],
                             ["LEPDens", "DOUBLE"],
                             ["TLEPAsian", "DOUBLE"],
                             ["PLEPAsian", "DOUBLE"],
                             ["LEPAsianDens", "DOUBLE"],
                             ["TLEPSpan", "DOUBLE"],
                             ["PLEPSpan", "DOUBLE"],
                             ["LEPSpanDens", "DOUBLE"],
                             ["TLEPEuro", "DOUBLE"],
                             ["PLEPEuro", "DOUBLE"],
                             ["LEPEuroDens", "DOUBLE"],
                             ["TLEPOther", "DOUBLE"],
                             ["PLEPOther", "DOUBLE"],
                             ['LEPOtherDens', "DOUBLE"],
                             ["CoAbvLEP", "DOUBLE"],
                             ["RegAbvLEP", "DOUBLE"]
                             ])
    print("")
    print("---------------------------")
    print("Added fields")

    # CALCULATE OUT BLOCK GROUP CENSUS VALUES
    ap.CalculateFields_management(working_file, "PYTHON3",
                                  [["SqMiles", "!shape.area@squaremiles!"],
                                   ["TPOP", "!B16004e1!"],
                                   ["TLEP",
                                    "!B16004e6!+!B16004e7!+!B16004e8!+!B16004e11!+!B16004e12!+!B16004e13!+!B16004e16!+!B16004e17!+!B16004e18!+!B16004e21!+!B16004e22!+!B16004e23!+!B16004e28!+!B16004e29!+!B16004e30!+!B16004e33!+!B16004e34!+!B16004e35!+!B16004e38!+!B16004e39!+!B16004e40!+!B16004e43!+!B16004e44!+!B16004e45!+!B16004e50!+!B16004e51!+!B16004e52!+!B16004e55!+!B16004e56!+!B16004e57!+!B16004e60!+!B16004e61!+!B16004e62!+!B16004e65!+!B16004e66!+!B16004e67!"],
                                   ["PLEP", "!TPOP!/!TLEP!"],
                                   ["LEPDens", "!TLEP!/!SqMiles!"],
                                   ["TEngOnly", "!B16004e3!+!B16004e25!+!B16004e47!"],
                                   ["TEngVW",
                                    "!B16004e5!+!B16004e10!+!B16004e15!+!B16004e20!+!B16004e27!+!B16004e32!+!B16004e37!+!B16004e42!+!B16004e49!+!B16004e54!+!B16004e59!+!B16004e64!"],
                                   ["TLEPSpan",
                                    "!B16004e6!+!B16004e7!+!B16004e8!+!B16004e28!+!B16004e29!+!B16004e30!+!B16004e50!+!B16004e51!+!B16004e52!"],
                                   ["TLEPEuro",
                                    "!B16004e11!+!B16004e12!+!B16004e13!+!B16004e33!+!B16004e34!+!B16004e35!+!B16004e55!+!B16004e56!+!B16004e57!"],
                                   ["TLEPAsian",
                                    "!B16004e16!+!B16004e17!+!B16004e18!+!B16004e38!+!B16004e39!+!B16004e40!+!B16004e60!+!B16004e61!+!B16004e62!"],
                                   ["TLEPOther",
                                    "!B16004e21!+!B16004e22!+!B16004e23!+!B16004e43!+!B16004e44!+!B16004e45!+!B16004e65!+!B16004e66!+!B16004e67!"],
                                   ["PEngVW", "!TEngVW!/!TPOP!"],
                                   ["PLEPSpan", "!TLEPSpan!/!TPOP!"],
                                   ["PLEPEuro", "!TLEPEuro!/!TPOP!"],
                                   ["PLEPAsian", "!TLEPAsian!/!TPOP!"],
                                   ["PLEPOther", "!TLEPOther!/!TPOP!"],
                                   ["LEPSpanDens", "!TLEPSpan!/!SqMiles!"],
                                   ["LEPEuroDens", "!TLEPEuro!/!SqMiles!"],
                                   ["LEPAsianDens", "!TLEPAsian!/!SqMiles!"],
                                   ["LEPOtherDens", "!TLEPOther!/!SqMiles!"]
                                   ])
    print("")
    print("---------------------------")
    print("Finished calculating LEP Population Calcs")

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [
        ["TPOP", "SUM"],
        ["SqMiles", "SUM"],
        ["TEngOnly", "SUM"],
        ["TEngVW", "SUM"],
        ["TLEP", "SUM"],
        ["TLEPAsian", "SUM"],
        ["TLEPSpan", "SUM"],
        ["TLEPEuro", "SUM"],
        ["TLEPOther", "SUM"]])
    print("")
    print("---------------------------")
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [
        ["TPOP", "SUM"],
        ["SqMiles", "SUM"],
        ["TEngOnly", "SUM"],
        ["TEngVW", "SUM"],
        ["TLEP", "SUM"],
        ["TLEPAsian", "SUM"],
        ["TLEPSpan", "SUM"],
        ["TLEPEuro", "SUM"],
        ["TLEPOther", "SUM"]])
    print("")
    print("---------------------------")
    print("Dissolve Region Stats")

    # ADD COUNTY FIELDS
    ap.management.AddFields(cw,
                            [["CoTPOP", "DOUBLE"],
                             ["CoSqMiles", "DOUBLE"],
                             ["CoTLEP", "DOUBLE"],
                             ["CoPLEP", "DOUBLE"],
                             ["CoLEPDens", "DOUBLE"],
                             ["CoTLEPAsian", "DOUBLE"],
                             ["CoPLEPAsian", "DOUBLE"],
                             ["CoLEPAsianDens", "DOUBLE"],
                             ["CoTLEPSpan", "DOUBLE"],
                             ["CoPLEPSpan", "DOUBLE"],
                             ["CoLEPSpanDens", "DOUBLE"],
                             ["CoTLEPEuro", "DOUBLE"],
                             ["CoPLEPEuro", "DOUBLE"],
                             ["CoLEPEuroDens", "DOUBLE"],
                             ["CoTLEPOther", "DOUBLE"],
                             ["CoPLEPOther", "DOUBLE"],
                             ['CoLEPOtherDens', "DOUBLE"]])
    print("")
    print("---------------------------")
    print(cw_file + " fields added !!!")

    # ADD REGIONAL FIELDS
    ap.management.AddFields(rw,
                            [["RegTPOP", "DOUBLE"],
                             ["RegSqMiles", "DOUBLE"],
                             ["RegTLEP", "DOUBLE"],
                             ["RegPLEP", "DOUBLE"],
                             ["RegLEPDens", "DOUBLE"],
                             ["RegTLEPAsian", "DOUBLE"],
                             ["RegPLEPAsian", "DOUBLE"],
                             ["RegLEPAsianDens", "DOUBLE"],
                             ["RegTLEPSpan", "DOUBLE"],
                             ["RegPLEPSpan", "DOUBLE"],
                             ["RegLEPSpanDens", "DOUBLE"],
                             ["RegTLEPEuro", "DOUBLE"],
                             ["RegPLEPEuro", "DOUBLE"],
                             ["RegLEPEuroDens", "DOUBLE"],
                             ["RegTLEPOther", "DOUBLE"],
                             ["RegPLEPOther", "DOUBLE"],
                             ['RegLEPOtherDens', "DOUBLE"]])
    print("")
    print("---------------------------")
    print(rw_file + " fields added !!!")

    # CALCULATE COUNTY VALUES
    ap.CalculateFields_management(cw, "PYTHON3",
                                  [["CoTPOP", "!SUM_TPOP!"],
                                   ["CoSqMiles", "!SUM_SqMiles!"],
                                   ["CoTLEP", "!SUM_TLEP!"],
                                   ["CoTLEPAsian", "!SUM_TLEPAsian!"],
                                   ["CoTLEPSpan", "!SUM_TLEPSpan!"],
                                   ["CoTLEPEuro", "!SUM_TLEPEuro!"],
                                   ["CoTLEPOther", "!SUM_TLEPOther!"]])

    # CALCULATE REGIONAL PERCENTAGES AND DENSITIES
    ap.CalculateFields_management(cw, "PYTHON3",
                                  [["CoPLEP", "!CoTLEP!/!CoTPOP!"],
                                   ["CoLEPDens", "!CoTLEP!/!CoSqMiles!"],
                                   ["CoPLEPAsian", "!CoTLEPAsian!/!CoTPOP!"],
                                   ["CoLEPAsianDens", "!CoTLEPAsian!/!CoSqMiles!"],
                                   ["CoPLEPSpan", "!CoTLEPSpan!/!CoTPOP!"],
                                   ["CoLEPSpanDens", "!CoTLEPSpan!/!CoSqMiles!"],
                                   ["CoPLEPEuro", "!CoTLEPEuro!/!CoTPOP!"],
                                   ["CoLEPEuroDens", "!CoTLEPEuro!/!CoSqMiles!"],
                                   ["CoPLEPOther", "!CoTLEPOther!/!CoTPOP!"],
                                   ['CoLEPOtherDens', "!CoTLEPOther!/!CoSqMiles!"]])
    print("")
    print("---------------------------")
    print(cw_file + " fields calculated !!!")

    # CALCULATE REGIONAL VALUES
    ap.CalculateFields_management(rw, "PYTHON3",
                                  [["RegTPOP", "!SUM_TPOP!"],
                                   ["RegSqMiles", "!SUM_SqMiles!"],
                                   ["RegTLEP", "!SUM_TLEP!"],
                                   ["RegTLEPAsian", "!SUM_TLEPAsian!"],
                                   ["RegTLEPSpan", "!SUM_TLEPSpan!"],
                                   ["RegTLEPEuro", "!SUM_TLEPEuro!"],
                                   ["RegTLEPOther", "!SUM_TLEPOther!"]])

    # CALCULATE REGIONAL PERCENTAGES AND DENSITIES
    ap.CalculateFields_management(rw, "PYTHON3",
                                  [["RegPLEP", "!RegTLEP!/!RegTPOP!"],
                                   ["RegLEPDens", "!RegTLEP!/!RegSqMiles!"],
                                   ["RegPLEPAsian", "!RegTLEPAsian!/!RegTPOP!"],
                                   ["RegLEPAsianDens", "!RegTLEPAsian!/!RegSqMiles!"],
                                   ["RegPLEPSpan", "!RegTLEPSpan!/!RegTPOP!"],
                                   ["RegLEPSpanDens", "!RegTLEPSpan!/!RegSqMiles!"],
                                   ["RegPLEPEuro", "!RegTLEPEuro!/!RegTPOP!"],
                                   ["RegLEPEuroDens", "!RegTLEPEuro!/!RegSqMiles!"],
                                   ["RegPLEPOther", "!RegTLEPOther!/!RegTPOP!"],
                                   ['RegLEPOtherDens', "!RegTLEPOther!/!RegSqMiles!"]])
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

    # CALCULATE OUT ABOVE REGIONAL AND COUNTY AVERAGE DENSITIES FOR TRACTS
    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoAbvLEP 'ifBlock(!LEPDens!, !CoLEPDens!)';RegAbvLEP 'ifBlock(!LEPDens!, !RegLEPDens!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("")
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, plcs, twrw_places)
    print("")
    print("---------------------------")
    print("Places Spaital Join")

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    print("")
    print("---------------------------")
    print("LEP_Final feature class created - Script Complete!!!")

    # FOR LOOP FOR CLEANING UP TABLE BY DELETING OUT ALL OF THE FIELDS IN THE DELETE_FIELDS LIST
    for field in delete_fields:
        ap.DeleteField_management(final_file, field)
        print("")
        print("---------------------------")
        print(field + " DELETED")
        print("---------------------------")

    print("")
    print("---------------------------")
    print("Finished Cleaning up fields")
    print("---------------------------")
    print("")
    print('Finished Running tool')

lep(root_dir, bg_mergegdb, places, bg_file, lep_file)


def minority(rdir, mgdb, plcs, bgf, racet, hispt):
    gdb = f"Minority{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = "Minority_working"

    race_table = os.path.join(mgdb, racet)
    hisp_table = os.path.join(mgdb, hispt)
    bg = os.path.join(mgdb, bgf)
    working_gdb = os.path.join(rdir, gdb)



    # Working file locations
    cw_file = "Minority_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = "Minority_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = "Minority_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = "Minority_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    twrw_places_file = "Minority_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    final_file = "Minority_Final"
    final = os.path.join(outputgdb, final_file)

    delete_fields = ["Join_Count", "Join_Count_1", "TARGET_FID_12", "Target_FID", "Target_FID_1", "Join_Count_12",
                     "Geoid_1", "B02001e1", "B02001e2", "B02001e3", "B02001e4", "B02001e5", "B02001e6", "B02001e7",
                     "B02001e8", "B02001e9", "B02001e10", "B03002e13", "SUM_TPop", "SUM_TMinority", "SUM_SqMiles",
                     "SUM_TPop_1", "SUM_TMinority_1", "SUM_SqMiles_1", "GEOID_12_13", "PLACENS", "PLACEFP", "STATEFP_1",
                     "SHAPE_LENGTH_12", "SHAPE_AREA_12", "SHAPE_LENGTH_1", "SHAPE_LENGTH_1", "COUNTYFP_1", "GEOID_12", ]

    if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
        shutil.rmtree(working_gdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(rdir, gdb)
    print("GEODATABASE CREATED!!!")

    ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file,
                                             "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    print("---------------------------")
    print(working_file + " Created!!!")

    ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=race_table, join_field="GEOID",
                            fields="B02001e1;B02001e3;B02001e4;B02001e5;B02001e6;B02001e7;B02001e8;GEOID")
    print("---------------------------")
    print(working_file + " Joined with Race Table!!!")

    ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=hisp_table, join_field="GEOID",
                            fields="B03002e13;GEOID")
    print("---------------------------")
    print(working_file + " Joined with Hispanic Table!!!")

    ap.management.AddFields(working_file, [["SqMiles", "DOUBLE"],
                                           ["TPop", "DOUBLE"],
                                           ["TMinority", "DOUBLE"],
                                           ['PMinority', "DOUBLE"],
                                           ["MinorityDens", "DOUBLE"],
                                           ["CoMinBG", "SHORT"],
                                           ["RegMinBG", "SHORT"]])

    ap.CalculateFields_management(working_file, "PYTHON3", [["SqMiles", "!shape.area@squaremiles!"],
                                                            ["TPop", "!B02001e1!"],
                                                            ["TMinority",
                                                             "!B02001e3! + !B02001e4! + !B02001e5! + !B02001e6! + !B02001e7! + !B02001e8! + !B03002e13!"],
                                                            ['PMinority', "!TMinority! / !TPop!"],
                                                            ["MinorityDens", "!TMinority! / !SqMiles!"]])

    print("---------------------------")
    print("Finished calculating Minority Calcs")

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["TPop", "SUM"],
                                                          ["TMinority", "SUM"],
                                                          ["SqMiles", "SUM"]])
    print("---------------------------")
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [["TPop", "SUM"],
                                                  ["TMinority", "SUM"],
                                                  ["SqMiles", "SUM"]])
    print("---------------------------")
    print("Dissolve Region Stats")

    ap.management.AddFields(cw, [["CoTPop", "Double"],
                                 ["CoTMinority", "Double"],
                                 ["CoTMinority", "Double"],
                                 ["CoSqMiles", "Double"],
                                 ["CoMinorityDens", "Double"]])

    ap.CalculateFields_management(cw, "PYTHON", [["CoTPop", "!SUM_TPop!"],
                                                 ["CoTMinority", "!SUM_TMinority!"],
                                                 ["CoSqMiles", "!SUM_SqMiles!"],
                                                 ["CoMinorityDens", "!CoTMinority! / !CoSqMiles!"]])
    print("---------------------------")
    print(rw_file + " fields calculated !!!")

    ap.management.AddFields(rw, [["RegTPop", "Double"],
                                 ["RegTMinority", "Double"],
                                 ["RegTMinority", "Double"],
                                 ["RegSqMiles", "Double"],
                                 ["RegMinorityDens", "Double"]])

    ap.CalculateFields_management(rw, "PYTHON", [["RegTPop", "!SUM_TPop!"],
                                                 ["RegTMinority", "!SUM_TMinority!"],
                                                 ["RegSqMiles", "!SUM_SqMiles!"],
                                                 ["RegMinorityDens", "!RegTMinority! / !RegSqMiles!"]])
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

    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoMinBG 'ifBlock(!MinorityDens!, !CoMinorityDens!)';RegMinBG 'ifBlock(!MinorityDens!, !RegMinorityDens!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, plcs, twrw_places)
    print("---------------------------")
    print("Places Spaital Join")

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    print("---------------------------")

    for field in delete_fields:
        ap.DeleteField_management(final_file, field)
        print("---------------------------")
        print(field + " DELETED")
        print("---------------------------")

    print("Minority_Final feature class created - Script Complete!!!")

minority(root_dir, bg_mergegdb, places, bg_file, race_file, hisp_file)


def lowCar(rdir, mgdb, plcs, trctf, commutt):
    gdb = f"LowCar{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = "LowCar_working"

    commute_table = os.path.join(mgdb, commutt)
    tract = os.path.join(mgdb, trctf)
    working_gdb = os.path.join(rdir, gdb)

    tw = os.path.join(working_gdb, "NoCar_working")
    tw_file = "NoCar_working"
    cw = os.path.join(working_gdb, "NoCar_working_County")
    cw_file = "NoCar_Working_County"
    rw = os.path.join(working_gdb, "NoCar_working_Reg")
    rw_file = "NoCar_Working_Reg"
    twcw_file = "NoCar_working_CountyJoin"
    twcw = os.path.join(working_gdb, twcw_file)
    twrw_file = "NoCar_working_RegJoin"
    twrw = os.path.join(working_gdb, twrw_file)
    twrw_places_file = f"LowCar{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(working_gdb, twrw_places_file)
    final_file = "NoCar_final"
    final = os.path.join(working_gdb, final_file)

    delete_fields = ["Join_Count", "TARGET_FID", "Join_Count", "TARGET_FID", "B08201e2", "B08201e3", "B08201e1",
                     "B08201e2", "B08201e3", "SUM_THH", "SUM_TNoCar", "SUM_TOneCar", "SUM_SqMiles", "SUM_THH_1",
                     "SUM_TNoCar_1", "SUM_TOneCar_1", "SUM_SqMiles_1", "Shape_Length_12", "Shape_Area_12"]

    if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
        shutil.rmtree(working_gdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(rdir, gdb)
    print("GEODATABASE CREATED!!!")

    # FEATURE CLASS TO WORKING FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(tract, outputgdb, working_file,
                                             "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    print(tw_file + " Created!!!")

    # JOIN WORKING FEATURE CLASS TO CENSUS TABLE - FILTER OUT SELECT COUNTIES IN REGION
    ap.JoinField_management(working_file, "GEOID_DATA", commute_table, "GEOID", ["B08201e1", "B08201e2", "B08201e3"])
    print(tw_file + " Joined with No Car Table file!!!")

    # ADDING ALL OF THE FIELDS TO TRACTS WORKING
    ap.management.AddFields(working_file,
                            [["THH", "DOUBLE"],
                             ["TNoCar", "DOUBLE"],
                             ["TOneCar", "DOUBLE"],
                             ["PNoCar", "DOUBLE"],
                             ["POneCar", "DOUBLE"],
                             ["SqMiles", "DOUBLE"],
                             ["NoCarDens", "DOUBLE"],
                             ["CoNoCarDens", "DOUBLE"],
                             ["RegNoCarDens", "DOUBLE"],
                             ["OneCarDens", "DOUBLE"],
                             ["CoOneCarDens", "DOUBLE"],
                             ["RegOneCarDens", "DOUBLE"],
                             ["TLowCar", "LONG"],
                             ["CoTLowCar", "LONG"],
                             ["RegTLowCar", "LONG"],
                             ["LowCarDens", "DOUBLE"],
                             ["CoLowCarDens", "DOUBLE"],
                             ["RegLowCarDens", "DOUBLE"],
                             ["CoAbvNoCar", "SHORT", '', '', '', 0],
                             ["RegAbvNoCar", "SHORT", '', '', '', 0],
                             ["CoAbvLowCar", "SHORT", '', '', '', 0],
                             ["RegAbvLowCar", "SHORT", '', '', '', 0],
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
                                   ['POneCar', '!B08201e3!/!B08201e1!']])
    print("Finished calculating Population, Total No Car, Total One Car, and Total Low Car")

    # CALCULATE OUT TRACT CENSUS DENSITIES
    ap.CalculateFields_management(working_file, "PYTHON3",
                                  [["NoCarDens", "!TNoCar!/!THH!"],
                                   ['OneCarDens', '!TOneCar!/!THH!'],
                                   ['LowCarDens', '!TLowCar! / !SqMiles!']])
    print("Finished calculating Population, Total No Car, and Total One Car")

    # DISSOLVE TRACTS BY COUNTY - SUM VALUES
    ap.Dissolve_management(working_file, cw, "COUNTYFP", [["THH", "SUM"],
                                                ["TNoCar", "SUM"],
                                                ["TOneCar", "SUM"],
                                                ["SqMiles", "SUM"]])
    print("Dissolve County Stats")

    # DISSOLVE TRACTS BY REGION - SUM VALUES
    ap.Dissolve_management(working_file, rw, "", [["THH", "SUM"],
                                        ["TNoCar", "SUM"],
                                        ["TOneCar", "SUM"],
                                        ["SqMiles", "SUM"]])
    print("Dissolve Region Stats")

    # ADD COUNTY VALUE FIELDS
    ap.management.AddFields(cw,
                            [["CoTHH", "DOUBLE"],
                             ["CoTNoCar", "DOUBLE"],
                             ["CoTOneCar", "DOUBLE"],
                             ["CoSqMiles", "DOUBLE"]])
    print(cw_file + " fields added !!!")

    # ADD REGION VALUE FIELDS
    ap.management.AddFields(rw,
                            [["RegTHH", "DOUBLE"],
                             ["RegTNoCar", "DOUBLE"],
                             ["RegTOneCar", "DOUBLE"],
                             ["RegSqMiles", "DOUBLE"]])
    print(rw_file + " fields added !!!")

    # CALCULATE COUNTY VALUES
    ap.CalculateFields_management(cw, "PYTHON3",
                                  [["CoTHH", "!SUM_THH!"],
                                   ["CoTNoCar", "!SUM_TNoCar!"],
                                   ["CoTOneCar", "!SUM_TOneCar!"],
                                   ["CoSqMiles", "!SUM_SqMiles!"]])
    print(cw_file + " fields calculated !!!")

    # CALCULATE REGIONAL VALUES
    ap.CalculateFields_management(rw, "PYTHON3",
                                  [["RegTHH", "!SUM_THH!"],
                                   ["RegTNoCar", "!SUM_TNoCar!"],
                                   ["RegTOneCar", "!SUM_TOneCar!"],
                                   ["RegSqMiles", "!SUM_SqMiles!"]])
    print(rw_file + " fields calculated !!!")

    # SPATIAL JOIN TRACTS FILE WITH COUNTY FILE
    ap.SpatialJoin_analysis(working_file, cw, twcw)
    print("County Spaital Join")

    # SPATIAL JOIN TRACTS FILE WITH REGION FILE
    ap.SpatialJoin_analysis(twcw, rw, twrw)
    print("Region Spaital Join")

    # CALCULATE OUT LOW CAR AND DENSITIES FOR COUNTYIES AND REGION ON TRACT FILE
    ap.CalculateFields_management(twrw, "PYTHON3",
                                  [["CoTLowCar", "!CoTOneCar!+!CoTNoCar!"],
                                   ["RegTLowCar", "!RegTOneCar!+!RegTNoCar!"],
                                   ["NoCarDens", "!TNoCar!/!SqMiles!"],
                                   ["CoNoCarDens", "!CoTNoCar!/!CoSqMiles!"],
                                   ["RegNoCarDens", "!RegTNoCar!/!RegSqMiles!"],
                                   ["CoOneCarDens", "!CoTOneCar!/!CoSqMiles!"],
                                   ["RegOneCarDens", "!RegTOneCar!/!RegSqMiles!"]])

    # CALCULATE OUT COUNTY AND REGIONAL LOW CAR DENSITIES
    ap.CalculateFields_management(twrw, "PYTHON3",
                                  [["CoLowCarDens", "!CoTLowCar!/!CoTHH!"],
                                   ["RegLowCarDens", "!RegTLowCar!/!RegTHH!"]])
    print('Calculated County and Regional Statistics')

    # CALCULATE OUT ABOVE REGIONAL AND COUNTY AVERAGE DENSITIES FOR TRACTS
    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoAbvNoCar 'ifBlock(!NoCarDens!, !CoNoCarDens!)';RegAbvNoCar 'ifBlock(!NoCarDens!, !RegNoCarDens!)';CoAbvLowCar 'ifBlock(!LowCarDens!, !CoLowCarDens!)';RegAbvLowCar 'ifBlock(!LowCarDens!, !RegLowCarDens!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)
    print("Above Car Density Calculations Completed")

    ap.SpatialJoin_analysis(twrw, plcs, twrw_places)
    print("")
    print("---------------------------")
    print("Places Spaital Join")

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(twrw_places, outputgdb, final_file)
    print("NoCar_final feature class created - Script Complete!!!")

    # FOR LOOP FOR CLEANING UP TABLE BY DELETING OUT ALL OF THE FIELDS IN THE DELETE_FIELDS LIST
    for field in delete_fields:
        ap.DeleteField_management(final_file, field)
        print(field + " DELETED")

lowCar(root_dir, tracts_mergegdb, places, tracts_file, commute_table)


def idRoutes(rdir):
    gdb = f"IdentifiedRoutes{year}.gdb"
    ap.env.workspace = os.path.join(rdir, gdb)  # -----> Change Year
    working_gdb = ap.env.workspace
    working_file = "IdentifiedRoutes_working"


    minority_gdb = os.path.join(root_dir, f"Minority{year}.gdb")  # -----> Change Year
    poverty_gdb = os.path.join(root_dir, f"Poverty{year}.gdb")  # -----> Change Year
    lep_gdb = os.path.join(root_dir, f"LEP{year}.gdb")
    minority_file = os.path.join(minority_gdb, "Minority_Final")
    poverty_file = os.path.join(poverty_gdb, "Poverty_Final")
    lep_file = os.path.join(lep_gdb, "LEP_Final")

    # WORKING FILES
    minority_working_file = "Minority_BG"
    minority_working = os.path.join(working_gdb, minority_working_file)
    poverty_working_file = "Poverty_BG"
    poverty_working = os.path.join(working_gdb, poverty_working_file)
    lep_working_file = "LEP_BG"
    lep_working = os.path.join(working_gdb, lep_file)

    routes_file = "IdentifiedRoutes"
    routes_working = os.path.join(working_gdb, routes_file)

    working_list = [[minority_file, minority_working_file, "RegMinBG",
                     [['MinorityLength', 'double'], ['PMinority', 'double'], ['MinorityRoute', 'SHORT']]],
                    [poverty_file, poverty_working_file, "RegPovBG",
                     [['PovertyLength', 'double'], ['PPoverty', 'double'], ['PovertyRoute', 'SHORT']]],
                    [lep_file, lep_working_file, "RegAbvLEP",
                     [['LEPLength', 'double'], ['PLEP', 'double'], ['LEPRoute', 'SHORT']]]
                    ]

    if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
        shutil.rmtree(working_gdb)
        print(f"{gdb} DELETED!!!")

    # CREATE WORKING GDB
    ap.CreateFileGDB_management(root_dir, gdb)
    print("GEODATABASE CREATED!!!")

    # CREATE WORKING MINORITY, POVERTY AND ROUTES FEATURE CLASSES
    ap.FeatureClassToFeatureClass_conversion(routes, working_gdb, routes_file)
    print("FEATURE CLASS CREATED!!!")

    ap.AddFields_management(routes_working, [['FullLength', 'double']])
    print('INTIIAL FIELDS ADDED TO ROUTES_WORKING FILE!!!')

    ap.CalculateFields_management(routes_working, 'PYTHON3', [['FullLength', '!shape.length@miles!']])
    print('CALCULATE FULL LENGTH OF ROUTES!!!')

    for item in working_list:
        # WORKING LIST ITEM DEFINITIONS
        org_file = item[0]
        working_file = item[1]
        identified_field = item[2]
        add_fields = item[3]
        routes_analysis = "routes_" + str(working_file)
        length_field = item[3][0][0]
        percent_field = item[3][1][0]
        id_field = item[3][2][0]

        print("")
        print("--------------------------------")
        print("********************************")
        print("START OF " + working_file)
        print("********************************")
        print("--------------------------------")
        print("")

        # FOR LOOP FILE NAME DEFINITIONS
        dissolve_file = str(working_file) + "_dissolve"
        buffer_file = str(dissolve_file) + "_buffer"
        clip_routes = str(routes_analysis) + "_clip"
        dissolve_routes = str(clip_routes) + "_dissolve"

        # FOR LOOP POLYGON AND ROUTE GEOPROCESSING
        selected_bg = str(identified_field) + " = 1"
        print(selected_bg)
        ap.FeatureClassToFeatureClass_conversion(org_file, working_gdb, working_file, selected_bg)
        print(working_file + " CREATED!!!")

        ap.FeatureClassToFeatureClass_conversion(routes_working, working_gdb, routes_analysis)
        print(routes_analysis + " FILE CREATED!!!")

        ap.Dissolve_management(working_file, dissolve_file, '')
        print(dissolve_file + " CREATED!!!")

        ap.Buffer_analysis(dissolve_file, buffer_file, "50 feet")
        print(buffer_file + " CREATED!!!")

        ap.Clip_analysis(routes_working, buffer_file, clip_routes)
        print(clip_routes + " CREATED!!!")

        ap.AddField_management(clip_routes, "IdLength", "double")
        print("IdLength Field Added for " + working_file)

        ap.CalculateField_management(clip_routes, "IdLength", "!shape.geodesicLength@miles!")
        print("IdLength Field Calculated for " + working_file)

        ap.Dissolve_management(clip_routes, dissolve_routes, 'LineAbbr', [["IdLength", 'sum']])
        print(clip_routes + " DISSOLVED")

        ap.JoinField_management(routes_working, "LineAbbr", dissolve_routes, "LineAbbr", ["SUM_IdLength"])
        print(routes_working + " JOINED WITH " + dissolve_routes)

        ap.AddFields_management(routes_working, add_fields)
        print("FIELDS ADDED TO " + routes_working)

        ap.CalculateFields_management(routes_working, 'PYTHON3', [[length_field, '!SUM_IdLength!'],
                                                                  [percent_field,
                                                                   '!' + str(length_field) + '! / !FullLength!'],
                                                                  [id_field, 'ifBlock(!' + str(percent_field) + '!)']],
                                      """def ifBlock(percent):
                                        if percent > 0.33:
                                            return 1
                                        elif percent < 0.33 or percent is None:
                                            return 0""")
        print(routes_working + " FIELDS CALCULATED")

        ap.DeleteField_management(routes_working, "SUM_IdLength")
        print("IdLength Field Deleted")


idRoutes(root_dir)
