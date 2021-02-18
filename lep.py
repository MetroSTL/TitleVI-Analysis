import arcpy as ap
import os
import shutil
from census import Census
from us import states
import pandas as pd
from arcgis import GIS

from helpers import *

def lepTracts(census_key, year, tract_mergedgdb, tract_file, root_dir, gdb, final_gdb_loc, region):
    
    # initial census call
    c = Census(census_key, year=2000+int(year))


    print('here')
    # call the acs 5 year tracts api for MO and IL convert to DF's and merge
    mo = c.acs5.state_county_tract(("GEO_ID", "C16001_005E", "C16001_008E","C16001_011E","C16001_014E","C16001_017E","C16001_020E","C16001_023E","C16001_026E","C16001_029E","C16001_035E"), states.MO.fips, '189,510', Census.ALL)
    mo = pd.DataFrame(mo)
    

    il = c.acs5.state_county_tract(("GEO_ID", "C16001_005E", "C16001_008E","C16001_011E","C16001_014E","C16001_017E","C16001_020E","C16001_023E","C16001_026E","C16001_029E","C16001_035E"), states.IL.fips, '163', Census.ALL)
    il = pd.DataFrame(il)

    mergeddf = mo.append(il, ignore_index=True)
    mergeddf["GEOID_DATA"] = mergeddf["GEO_ID"]
    mergeddf['GEOID_DATA'] = mergeddf['GEOID_DATA'].str.slice(start=9)

    # import geo to geopandas
    # pd.DataFrame.spatial.from_layer(os.path.join(tract_mergedgdb, tract_file))

    # # CLIP FEATURE CLASS
    # # CALC COVERAGE OF FIELDS
    
    tracts = pd.DataFrame.spatial.from_featureclass(os.path.join(tract_mergedgdb, tract_file))
    tracts = tracts.merge(mergeddf, left_on='GEOID', right_on='GEOID_DATA')
    
    # ["TLEPFrench", "DOUBLE"], # C16001e8  LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: French, Haitian, or Cajun: Speak English less than "very well": Population 5 years and over -- (Estimate)
    # ["TLEPGerm", "DOUBLE"], # C16001e11  LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: German or other West Germanic languages: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
    # ["TLEPRuss", "DOUBLE"],# C16001e14   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Russian, Polish, or other Slavic languages: Speak English less than "very well": Population 5 years and over -- (Estimate)
    # ["TLEPOIndoEuro", "DOUBLE"],# C16001e17   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Other Indo-European languages: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
    # ["TLEPKor", "DOUBLE"],# C16001e20   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Korean: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
    # ["TLEPChin", "DOUBLE"],# C16001e23   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Chinese (incl. Mandarin, Cantonese): Speak English less than "very well": Population 5 years and over -- (Estimate)
    # ["TLEPViet", "DOUBLE"],# C16001e26   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Vietnamese: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
    # ["TLEPTaglog", "DOUBLE"],# C16001e29   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Tagalog (incl. Filipino): Speak English less than ""very well"": Population 5 years and over -- (Estimate)
    # ["TLEPArabic", "DOUBLE"],# C16001e35   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Arabic: Speak English less than ""very well"": Population 5 years and over -- (Estimate)


    # RENAME FIELDS

    fields = [["C16001_005E", "TLEPSpan"], ["C16001_008E", "TLEPFrench"],["C16001_011E", "TLEPGerm"],["C16001_014E", "TLEPRuss"],["C16001_017E", "TLEPOIndoEuro"],["C16001_020E", "TLEPKor"],["C16001_023E", "TLEPChin"],["C16001_026E", "TLEPViet"],["C16001_029E", "TLEPTaglog"],["C16001_035E", "TLEPArabic"], ["sqmiles", "org_sqmiles"]]

    for field in fields:
        tracts[field[1]] = tracts[field[0]]
        tracts.drop(field[0], axis=1)

    tracts.to_csv(os.path.join(root_dir, rf"LEP_Lang_{year}.csv"), index=False)
    tracts.spatial.to_featureclass(location=os.path.join(gdb, rf"LEP_Lang_{year}"))

    ap.env.workspace = gdb
    ap.env.overwriteOutput = True
    ap.CalculateField_management(f"LEP_Lang_{year}", "org_sqmiles", '!shape.area@squaremiles!', 'PYTHON3')
    ap.Clip_analysis(f"LEP_Lang_{year}", region, f"LEP_Lang_{year}_Region")
    ap.AddField_management(f"LEP_Lang_{year}_Region", "NewSqMiles", field_type='float')
    ap.CalculateField_management(f"LEP_Lang_{year}_Region", "NewSqMiles", '!shape.area@squaremiles!', 'PYTHON3')

    tracts_clipped = pd.DataFrame.spatial.from_featureclass(os.path.join(ap.env.workspace, f"LEP_Lang_{year}_Region"))
    tracts_clipped['Coverage'] = tracts_clipped['NewSqMiles'] / tracts_clipped['org_sqmiles']

    coverage_fields = ['c16001_005_e', 'c16001_008_e', 'c16001_011_e', 'c16001_014_e', 'c16001_017_e','c16001_020_e', 'c16001_023_e', 'c16001_026_e', 'c16001_029_e','c16001_035_e', 'tlep_french','tlep_germ', 'tlep_russ', 'tlepo_indo_euro', 'tlep_kor', 'tlep_chin','tlep_viet', 'tlep_taglog', 'tlep_arabic']

    for field in coverage_fields:
        tracts_clipped[field] = tracts_clipped[field] * tracts_clipped['Coverage']
        print(field)

    tracts_clipped.spatial.to_featureclass(location=os.path.join(final_gdb_loc, rf"LEP_Lang_{year}_Region"))
    tracts_clipped.to_csv(os.path.join(root_dir, rf"LEP_Lang_{year}_Region.csv"), index=False)

def lep(year, root_dir, bg_mergedgdb, region, places, bg_file, lep_file, final_gdb_loc, census_key, tract_mergedgdb, tract_file):
    gdb = f"LEP{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year

    ap.ClearWorkspaceCache_management()

    outputgdb = ap.env.workspace
    working_file = "LEP_working"

    # lep_table = os.path.join(bg_mergedgdb, lep_file)
    # bg = os.path.join(bg_mergedgdb, bg_file)
    # working_gdb = os.path.join(root_dir, gdb)

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
                     "SUM_TLEPOther_1",
                    #  "C16001e8","C16001e11","C16001e14","C16001e17","C16001e20","C16001e23","C16001e26","C16001e29","C16001e35",
                     "SUM_TLEPFrench"
                     "SUM_TLEPFrench_1", "SUM_TLEPGerm", "SUM_TLEPGerm_1", "SUM_TLEPRuss", "SUM_TLEPRuss_1", "SUM_TLEPOIndoEuro", 
                     "SUM_TLEPOIndoEuro_1", "SUM_TLEPKor", "SUM_TLEPKor_1", "SUM_TLEPChin", "SUM_TLEPChin_1", "SUM_TLEPViet", 
                     "SUM_TLEPViet_1", "SUM_TLEPTaglog", "SUM_TLEPTaglog_1", "SUM_TLEPArabic", "SUM_TLEPArabic_1"]

    replaceGDB(root_dir, gdb)

    fields_list = ["B16004e1", "B16004e10", "B16004e11", "B16004e12", "B16004e13", "B16004e14", "B16004e15", "B16004e16", "B16004e17", "B16004e18", "B16004e19", "B16004e2", "B16004e20", "B16004e21", "B16004e22", "B16004e23", "B16004e24", "B16004e25", "B16004e26", "B16004e27", "B16004e28", "B16004e29", "B16004e3", "B16004e30", "B16004e31", "B16004e32", "B16004e33", "B16004e34", "B16004e35", "B16004e36", "B16004e37", "B16004e38", "B16004e39", "B16004e4", "B16004e40", "B16004e41", "B16004e42", "B16004e43", "B16004e44", "B16004e45", "B16004e46", "B16004e47", "B16004e48", "B16004e49", "B16004e5", "B16004e50", "B16004e51", "B16004e52", "B16004e53", "B16004e54", "B16004e55", "B16004e56", "B16004e57", "B16004e58", "B16004e59", "B16004e6", "B16004e60", "B16004e61", "B16004e62", "B16004e63", "B16004e64", "B16004e65", "B16004e66", "B16004e67", "B16004e7", "B16004e8", "B16004e9", "B16004m1", "B16004m10", "B16004m11", "B16004m12", "B16004m13", "B16004m14", "B16004m15", "B16004m16", "B16004m17", "B16004m18", "B16004m19", "B16004m2", "B16004m20", "B16004m21", "B16004m22", "B16004m23", "B16004m24", "B16004m25", "B16004m26", "B16004m27", "B16004m28", "B16004m29", "B16004m3", "B16004m30", "B16004m31", "B16004m32", "B16004m33", "B16004m34", "B16004m35", "B16004m36", "B16004m37", "B16004m38", "B16004m39", "B16004m4", "B16004m40", "B16004m41", "B16004m42", "B16004m43", "B16004m44", "B16004m45", "B16004m46", "B16004m47", "B16004m48", "B16004m49", "B16004m5", "B16004m50", "B16004m51", "B16004m52", "B16004m53", "B16004m54", "B16004m55", "B16004m56", "B16004m57", "B16004m58", "B16004m59", "B16004m6", "B16004m60", "B16004m61", "B16004m62", "B16004m63", "B16004m64", "B16004m65", "B16004m66", "B16004m67", "B16004m7", "B16004m8", "B16004m9", "C16002e1", "C16002e10", "C16002e11", "C16002e12", "C16002e13", "C16002e14", "C16002e2", "C16002e3", "C16002e4", "C16002e5", "C16002e6", "C16002e7", "C16002e8", "C16002e9", "C16002m1", "C16002m10", "C16002m11", "C16002m12", "C16002m13", "C16002m14", "C16002m2", "C16002m3", "C16002m4", "C16002m5", "C16002m6", "C16002m7", "C16002m8", "C16002m9", "C16001e5", 
        "C16001e8","C16001e11","C16001e14","C16001e17","C16001e20","C16001e23","C16001e26","C16001e29","C16001e35"]

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
                             ["RegAbvLEP", "DOUBLE"],
                             ["TLEPFrench", "DOUBLE"], # C16001e8  LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: French, Haitian, or Cajun: Speak English less than "very well": Population 5 years and over -- (Estimate)
                             ["TLEPGerm", "DOUBLE"], # C16001e11  LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: German or other West Germanic languages: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
                             ["TLEPRuss", "DOUBLE"],# C16001e14   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Russian, Polish, or other Slavic languages: Speak English less than "very well": Population 5 years and over -- (Estimate)
                             ["TLEPOIndoEuro", "DOUBLE"],# C16001e17   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Other Indo-European languages: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
                             ["TLEPKor", "DOUBLE"],# C16001e20   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Korean: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
                             ["TLEPChin", "DOUBLE"],# C16001e23   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Chinese (incl. Mandarin, Cantonese): Speak English less than "very well": Population 5 years and over -- (Estimate)
                             ["TLEPViet", "DOUBLE"],# C16001e26   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Vietnamese: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
                             ["TLEPTaglog", "DOUBLE"],# C16001e29   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Tagalog (incl. Filipino): Speak English less than ""very well"": Population 5 years and over -- (Estimate)
                             ["TLEPArabic", "DOUBLE"],# C16001e35   LANGUAGE SPOKEN AT HOME FOR THE POPULATION 5 YEARS AND OVER: Arabic: Speak English less than ""very well"": Population 5 years and over -- (Estimate)
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
                                   ["LEPOtherDens", "!TLEPOther!/!SqMiles!"],
                                   ["TLEPFrench", "!C16001e8!"],
                                   ["TLEPGerm", "!C16001e11!"],
                                   ["TLEPRuss", "!C16001e14!"],
                                   ["TLEPOIndoEuro", "!C16001e17!"],
                                   ["TLEPKor", "!C16001e20!"],
                                   ["TLEPChin", "!C16001e23!"],
                                   ["TLEPViet", "!C16001e26!"],
                                   ["TLEPTaglog", "!C16001e29!"],
                                   ["TLEPArabic", "!C16001e35!"],
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
        ["TLEPOther", "SUM"],
        ["TLEPFrench", "SUM"],
        ["TLEPGerm", "SUM"],
        ["TLEPRuss", "SUM"],
        ["TLEPOIndoEuro", "SUM"],
        ["TLEPKor", "SUM"],
        ["TLEPChin", "SUM"],
        ["TLEPViet", "SUM"],
        ["TLEPTaglog", "SUM"],
        ["TLEPArabic", "SUM"]])
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
        ["TLEPOther", "SUM"],
        ["TLEPFrench", "SUM"],
        ["TLEPGerm", "SUM"],
        ["TLEPRuss", "SUM"],
        ["TLEPOIndoEuro", "SUM"],
        ["TLEPKor", "SUM"],
        ["TLEPChin", "SUM"],
        ["TLEPViet", "SUM"],
        ["TLEPTaglog", "SUM"],
        ["TLEPArabic", "SUM"]])
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
                             ['CoLEPOtherDens', "DOUBLE"],
                             ["CoTLEPOther", "DOUBLE"],
                             ["CoTLEPFrench", "DOUBLE"],
                             ["CoPLEPFrench", "DOUBLE"],
                             ["CoLEPFrenchDens", "DOUBLE"],
                             ["CoTLEPGerm", "DOUBLE"],
                             ["CoPLEPGerm", "DOUBLE"],
                             ["CoLEPGermDens", "DOUBLE"],
                             ["CoTLEPRuss", "DOUBLE"],
                             ["CoPLEPRuss", "DOUBLE"],
                             ["CoLEPRussDens", "DOUBLE"],
                             ["CoTLEPOIndoEuro", "DOUBLE"],
                             ["CoPLEPOIndoEuro", "DOUBLE"],
                             ["CoLEPOIndoEuroDens", "DOUBLE"],
                             ["CoTLEPKor", "DOUBLE"],
                             ["CoPLEPKor", "DOUBLE"],
                             ["CoLEPKorDens", "DOUBLE"],
                             ["CoTLEPChin", "DOUBLE"],
                             ["CoPLEPChin", "DOUBLE"],
                             ["CoLEPChinDens", "DOUBLE"],
                             ["CoTLEPViet", "DOUBLE"],
                             ["CoPLEPViet", "DOUBLE"],
                             ["CoLEPVietDens", "DOUBLE"],
                             ["CoTLEPTaglog", "DOUBLE"],
                             ["CoPLEPTaglog", "DOUBLE"],
                             ["CoLEPTaglogDens", "DOUBLE"],
                             ["CoTLEPArabic", "DOUBLE"],
                             ["CoPLEPArabic", "DOUBLE"],
                             ["CoLEPArabicDens", "DOUBLE"]])
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
                             ['RegLEPOtherDens', "DOUBLE"],
                             ["RegTLEPFrench", "DOUBLE"],
                             ["RegPLEPFrench", "DOUBLE"],
                             ["RegLEPFrenchDens", "DOUBLE"],
                             ["RegTLEPGerm", "DOUBLE"],
                             ["RegPLEPGerm", "DOUBLE"],
                             ["RegLEPGermDens", "DOUBLE"],
                             ["RegTLEPRuss", "DOUBLE"],
                             ["RegPLEPRuss", "DOUBLE"],
                             ["RegLEPRussDens", "DOUBLE"],
                             ["RegTLEPOIndoEuro", "DOUBLE"],
                             ["RegPLEPOIndoEuro", "DOUBLE"],
                             ["RegLEPOIndoEuroDens", "DOUBLE"],
                             ["RegTLEPKor", "DOUBLE"],
                             ["RegPLEPKor", "DOUBLE"],
                             ["RegLEPKorDens", "DOUBLE"],
                             ["RegTLEPChin", "DOUBLE"],
                             ["RegPLEPChin", "DOUBLE"],
                             ["RegLEPChinDens", "DOUBLE"],
                             ["RegTLEPViet", "DOUBLE"],
                             ["RegPLEPViet", "DOUBLE"],
                             ["RegLEPVietDens", "DOUBLE"],
                             ["RegTLEPTaglog", "DOUBLE"],
                             ["RegPLEPTaglog", "DOUBLE"],
                             ["RegLEPTaglogDens", "DOUBLE"],
                             ["RegTLEPArabic", "DOUBLE"],
                             ["RegPLEPArabic", "DOUBLE"],
                             ["RegLEPArabicDens", "DOUBLE"]])
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
                                   ["CoTLEPOther", "!SUM_TLEPOther!"],
                                   ["CoTLEPFrench", "!SUM_TLEPFrench!"],
                                   ["CoTLEPGerm", "!SUM_TLEPGerm!"],
                                   ["CoTLEPRuss", "!SUM_TLEPRuss!"],
                                   ["CoTLEPOIndoEuro", "!SUM_TLEPOIndoEuro!"],
                                   ["CoTLEPKor", "!SUM_TLEPKor!"],
                                   ["CoTLEPChin", "!SUM_TLEPChin!"],
                                   ["CoTLEPViet", "!SUM_TLEPViet!"],
                                   ["CoTLEPTaglog", "!SUM_TLEPTaglog!"],
                                   ["CoTLEPArabic", "!SUM_TLEPArabic!"]])

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
                                   ['CoLEPOtherDens', "!CoTLEPOther!/!CoSqMiles!"],
                                   ["CoPLEPFrench", "!CoTLEPFrench! / !CoTPOP!"],
                                   ["CoLEPFrenchDens", "!CoTLEPFrench! / !CoSqMiles!"],
                                   ["CoPLEPGerm", "!CoTLEPGerm! / !CoTPOP!"],
                                   ["CoLEPGermDens", "!CoTLEPGerm! / !CoSqMiles!"],
                                   ["CoPLEPRuss", "!CoTLEPRuss! / !CoTPOP!"],
                                   ["CoLEPRussDens", "!CoTLEPRuss! / !CoSqMiles!"],
                                   ["CoPLEPOIndoEuro", "!CoTLEPOIndoEuro! / !CoTPOP!"],
                                   ["CoLEPOIndoEuroDens", "!CoTLEPOIndoEuro! / !CoSqMiles!"],
                                   ["CoPLEPKor", "!CoTLEPKor! / !CoTPOP!"],
                                   ["CoLEPKorDens", "!CoTLEPKor! / !CoSqMiles!"],
                                   ["CoPLEPChin", "!CoTLEPChin! / !CoTPOP!"],
                                   ["CoLEPChinDens", "!CoTLEPChin! / !CoSqMiles!"],
                                   ["CoPLEPViet", "!CoTLEPViet! / !CoTPOP!"],
                                   ["CoLEPVietDens", "!CoTLEPViet! / !CoSqMiles!"],
                                   ["CoPLEPTaglog", "!CoTLEPTaglog! / !CoTPOP!"],
                                   ["CoLEPTaglogDens", "!CoTLEPTaglog! / !CoSqMiles!"],
                                   ["CoPLEPArabic", "!CoTLEPArabic! / !CoTPOP!"],
                                   ["CoLEPArabicDens", "!CoTLEPArabic! / !CoSqMiles!"]])
                                   
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
                                   ["RegTLEPOther", "!SUM_TLEPOther!"],
                                   ["RegTLEPFrench", "!SUM_TLEPFrench!"],
                                   ["RegTLEPGerm", "!SUM_TLEPGerm!"],
                                   ["RegTLEPRuss", "!SUM_TLEPRuss!"],
                                   ["RegTLEPOIndoEuro", "!SUM_TLEPOIndoEuro!"],
                                   ["RegTLEPKor", "!SUM_TLEPKor!"],
                                   ["RegTLEPChin", "!SUM_TLEPChin!"],
                                   ["RegTLEPViet", "!SUM_TLEPViet!"],
                                   ["RegTLEPTaglog", "!SUM_TLEPTaglog!"],
                                   ["RegTLEPArabic", "!SUM_TLEPArabic!"]])

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
                                   ['RegLEPOtherDens', "!RegTLEPOther!/!RegSqMiles!"],
                                   ["RegPLEPFrench", "!RegTLEPFrench! / !RegTPOP!"],
                                   ["RegLEPFrenchDens", "!RegTLEPFrench! / !RegSqMiles!"],
                                   ["RegPLEPGerm", "!RegTLEPGerm! / !RegTPOP!"],
                                   ["RegLEPGermDens", "!RegTLEPGerm! / !RegSqMiles!"],
                                   ["RegPLEPRuss", "!RegTLEPRuss! / !RegTPOP!"],
                                   ["RegLEPRussDens", "!RegTLEPRuss! / !RegSqMiles!"],
                                   ["RegPLEPOIndoEuro", "!RegTLEPOIndoEuro! / !RegTPOP!"],
                                   ["RegLEPOIndoEuroDens", "!RegTLEPOIndoEuro! / !RegSqMiles!"],
                                   ["RegPLEPKor", "!RegTLEPKor! / !RegTPOP!"],
                                   ["RegLEPKorDens", "!RegTLEPKor! / !RegSqMiles!"],
                                   ["RegPLEPChin", "!RegTLEPChin! / !RegTPOP!"],
                                   ["RegLEPChinDens", "!RegTLEPChin! / !RegSqMiles!"],
                                   ["RegPLEPViet", "!RegTLEPViet! / !RegTPOP!"],
                                   ["RegLEPVietDens", "!RegTLEPViet! / !RegSqMiles!"],
                                   ["RegPLEPTaglog", "!RegTLEPTaglog! / !RegTPOP!"],
                                   ["RegLEPTaglogDens", "!RegTLEPTaglog! / !RegSqMiles!"],
                                   ["RegPLEPArabic", "!RegTLEPArabic! / !RegTPOP!"],
                                   ["RegLEPArabicDens", "!RegTLEPArabic! / !RegSqMiles!"]])
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


    print("")
    print("---------------------------")
    print("Above LEP Density Calculations Completed")

    # SPATIAL JOIN TRACTS FILE WITH PLACES FILE
    ap.SpatialJoin_analysis(twrw, places, twrw_places)
    print("")
    print("---------------------------")
    print("Places Spaital Join")


    cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)

    lepTracts(census_key, int(year), tract_mergedgdb, tract_file, root_dir, gdb, final_gdb_loc, region)
