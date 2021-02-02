import arcpy as ap
import os
import shutil

from helpers import *

def lep(year, root_dir, bg_mergedgdb, region, places, bg_file, lep_file, final_gdb_loc):
    gdb = f"LEP{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year
    outputgdb = ap.env.workspace
    working_file = "LEP_working"

    lep_table = os.path.join(bg_mergedgdb, lep_file)
    bg = os.path.join(bg_mergedgdb, bg_file)
    working_gdb = os.path.join(root_dir, gdb)

    # Working file locations
    cw_file = f"LEP{year}_working_County"
    cw = os.path.join(outputgdb, cw_file)
    rw_file = f"LEP{year}_working_Region"
    rw = os.path.join(outputgdb, rw_file)
    twcw_file = f"LEP{year}_working_CountyJoin"
    twcw = os.path.join(outputgdb, twcw_file)
    twrw_file = f"LEP{year}_working_RegionJoin"
    twrw = os.path.join(outputgdb, twrw_file)
    twrw_places_file = f"LEP{year}_working_RegionJoin_Places"
    twrw_places = os.path.join(outputgdb, twrw_places_file)
    final_file = f"LEP{year}_Final"
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

    # if os.path.exists(working_gdb) and os.path.isdir(working_gdb):
    #     shutil.rmtree(working_gdb)
    #     print(f"{gdb} DELETED!!!")

    # # CREATE WORKING GDB
    # ap.CreateFileGDB_management(root_dir, gdb)
    # print("GEODATABASE CREATED!!!")

    # # CREATE A NEW WORKING FEATURE CLASS
    # ap.FeatureClassToFeatureClass_conversion(bg, outputgdb, working_file,
    #                                          "GEOID LIKE '29189%' Or GEOID LIKE '29510%' Or GEOID LIKE '17163%'")
    # print("")
    # print("---------------------------")
    # print(working_file + " Created!!!")

    # # JOIN WORKING FEATURE CLASS TO CENSUS TABLE - FILTER OUT SELECT COUNTIES IN REGION
    # ap.JoinField_management(in_data=working_file, in_field="GEOID_Data", join_table=lep_table, join_field="GEOID",
    #                         fields="B16004e1;B16004e10;B16004e11;B16004e12;B16004e13;B16004e14;B16004e15;B16004e16;B16004e17;B16004e18;B16004e19;B16004e2;B16004e20;B16004e21;B16004e22;B16004e23;B16004e24;B16004e25;B16004e26;B16004e27;B16004e28;B16004e29;B16004e3;B16004e30;B16004e31;B16004e32;B16004e33;B16004e34;B16004e35;B16004e36;B16004e37;B16004e38;B16004e39;B16004e4;B16004e40;B16004e41;B16004e42;B16004e43;B16004e44;B16004e45;B16004e46;B16004e47;B16004e48;B16004e49;B16004e5;B16004e50;B16004e51;B16004e52;B16004e53;B16004e54;B16004e55;B16004e56;B16004e57;B16004e58;B16004e59;B16004e6;B16004e60;B16004e61;B16004e62;B16004e63;B16004e64;B16004e65;B16004e66;B16004e67;B16004e7;B16004e8;B16004e9;B16004m1;B16004m10;B16004m11;B16004m12;B16004m13;B16004m14;B16004m15;B16004m16;B16004m17;B16004m18;B16004m19;B16004m2;B16004m20;B16004m21;B16004m22;B16004m23;B16004m24;B16004m25;B16004m26;B16004m27;B16004m28;B16004m29;B16004m3;B16004m30;B16004m31;B16004m32;B16004m33;B16004m34;B16004m35;B16004m36;B16004m37;B16004m38;B16004m39;B16004m4;B16004m40;B16004m41;B16004m42;B16004m43;B16004m44;B16004m45;B16004m46;B16004m47;B16004m48;B16004m49;B16004m5;B16004m50;B16004m51;B16004m52;B16004m53;B16004m54;B16004m55;B16004m56;B16004m57;B16004m58;B16004m59;B16004m6;B16004m60;B16004m61;B16004m62;B16004m63;B16004m64;B16004m65;B16004m66;B16004m67;B16004m7;B16004m8;B16004m9;C16002e1;C16002e10;C16002e11;C16002e12;C16002e13;C16002e14;C16002e2;C16002e3;C16002e4;C16002e5;C16002e6;C16002e7;C16002e8;C16002e9;C16002m1;C16002m10;C16002m11;C16002m12;C16002m13;C16002m14;C16002m2;C16002m3;C16002m4;C16002m5;C16002m6;C16002m7;C16002m8;C16002m9;GEOID")
    # print("")
    # print("---------------------------")
    # print(working_file + " Joined with LEP Table!!!")

    replaceGDB(root_dir, gdb)

    fields_list = ["B16004e1", "B16004e10", "B16004e11", "B16004e12", "B16004e13", "B16004e14", "B16004e15", "B16004e16", "B16004e17", "B16004e18", "B16004e19", "B16004e2", "B16004e20", "B16004e21", "B16004e22", "B16004e23", "B16004e24", "B16004e25", "B16004e26", "B16004e27", "B16004e28", "B16004e29", "B16004e3", "B16004e30", "B16004e31", "B16004e32", "B16004e33", "B16004e34", "B16004e35", "B16004e36", "B16004e37", "B16004e38", "B16004e39", "B16004e4", "B16004e40", "B16004e41", "B16004e42", "B16004e43", "B16004e44", "B16004e45", "B16004e46", "B16004e47", "B16004e48", "B16004e49", "B16004e5", "B16004e50", "B16004e51", "B16004e52", "B16004e53", "B16004e54", "B16004e55", "B16004e56", "B16004e57", "B16004e58", "B16004e59", "B16004e6", "B16004e60", "B16004e61", "B16004e62", "B16004e63", "B16004e64", "B16004e65", "B16004e66", "B16004e67", "B16004e7", "B16004e8", "B16004e9", "B16004m1", "B16004m10", "B16004m11", "B16004m12", "B16004m13", "B16004m14", "B16004m15", "B16004m16", "B16004m17", "B16004m18", "B16004m19", "B16004m2", "B16004m20", "B16004m21", "B16004m22", "B16004m23", "B16004m24", "B16004m25", "B16004m26", "B16004m27", "B16004m28", "B16004m29", "B16004m3", "B16004m30", "B16004m31", "B16004m32", "B16004m33", "B16004m34", "B16004m35", "B16004m36", "B16004m37", "B16004m38", "B16004m39", "B16004m4", "B16004m40", "B16004m41", "B16004m42", "B16004m43", "B16004m44", "B16004m45", "B16004m46", "B16004m47", "B16004m48", "B16004m49", "B16004m5", "B16004m50", "B16004m51", "B16004m52", "B16004m53", "B16004m54", "B16004m55", "B16004m56", "B16004m57", "B16004m58", "B16004m59", "B16004m6", "B16004m60", "B16004m61", "B16004m62", "B16004m63", "B16004m64", "B16004m65", "B16004m66", "B16004m67", "B16004m7", "B16004m8", "B16004m9", "C16002e1", "C16002e10", "C16002e11", "C16002e12", "C16002e13", "C16002e14", "C16002e2", "C16002e3", "C16002e4", "C16002e5", "C16002e6", "C16002e7", "C16002e8", "C16002e9", "C16002m1", "C16002m10", "C16002m11", "C16002m12", "C16002m13", "C16002m14", "C16002m2", "C16002m3", "C16002m4", "C16002m5", "C16002m6", "C16002m7", "C16002m8", "C16002m9"]

    # clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file, join_table, fields_list)
    clipPolygons(bg_mergedgdb, bg_file, region, os.path.join(root_dir, gdb), working_file)
    joinAndCalcFields(working_file, bg_mergedgdb, os.path.join(root_dir, gdb), 'GEOID_Data', lep_file, 'GEOID', fields_list)

    ap.env.workspace = outputgdb

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
                                   ["PLEP", "!TLEP!/!TPOP!"],
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
    # NEW WAY USING PERCENT POPULATION

    ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
                                  fields="CoAbvLEP 'ifBlock(!PLEP!, !CoPLEP!)';RegAbvLEP 'ifBlock(!PLEP!, !RegPLEP!)'",
                                  code_block="""def ifBlock(area, region):
      if area > region:
         return 1
      else:
         return 0
         """)

         

    # OLD WAY USING POPULATION DENSITY

    # ap.CalculateFields_management(in_table=twrw, expression_type="PYTHON3",
    #                               fields="CoAbvLEP 'ifBlock(!LEPDens!, !CoLEPDens!)';RegAbvLEP 'ifBlock(!LEPDens!, !RegLEPDens!)'",
    #                               code_block="""def ifBlock(area, region):
    #   if area > region:
    #      return 1
    #   else:
    #      return 0
    #      """)


    print("")
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, places, twrw_places)
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

    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(final_file, final_gdb_loc, final_file)
    print("---------------------------")
