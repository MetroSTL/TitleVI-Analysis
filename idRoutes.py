# ! are the imports needed if they are defined in main?

import arcpy as ap
import os
import shutil

from helpers import *


# Mark routes as identified by each demographic if the route alignment is at least 33% 
# within identified block groups for that demographic.
def idRoutes(year, root_dir, routes, final_gdb_loc):
    gdb = f"IdentifiedRoutes{year}.gdb"
    ap.env.workspace = os.path.join(root_dir, gdb)  # -----> Change

    ap.ClearWorkspaceCache_management()

    working_gdb = ap.env.workspace
    working_file = "IdentifiedRoutes_working"

    # Get input demographic feature classes from previous function outputs
    # minority_gdb = os.path.join(root_dir, f"Minority{year}.gdb")  # -----> Change Year
    # poverty_gdb = os.path.join(root_dir, f"Poverty{year}.gdb")  # -----> Change Year
    # lep_gdb = os.path.join(root_dir, f"LEP{year}.gdb")
    minority_file = os.path.join(final_gdb_loc, f"Minority{year}_Final")
    # minority_file = os.path.join(minority_gdb, f"Minority{year}_Final")
    poverty_file = os.path.join(final_gdb_loc, f"Poverty{year}_Final")
    # poverty_file = os.path.join(poverty_gdb, f"Poverty{year}_Final")
    lep_file = os.path.join(final_gdb_loc, f"LEP{year}_Final")
    medhhinc_file = os.path.join(final_gdb_loc, f"MedHHInc{year}_Final")
    # lep_file = os.path.join(lep_gdb, f"LEP{year}_Final")

    # Working feature classes
    minority_working_file = f"Minority{year}_BG"
    poverty_working_file = f"Poverty{year}_BG"
    lep_working_file = f"LEP{year}_BG"
    medhhinc_working_file = f"MedHHInc{year}_BG"

    routes_file = f"IdentifiedRoutes{year}"
    routes_working = os.path.join(working_gdb, routes_file)

    # define inputs for the for loop - one set for each demographic category
    working_list = [{"org_file": minority_file,              # input feature class
                     "working_file":  minority_working_file, # working feature class for calcs
                     "identified_field": "RegMinBG",         # field containing the threshold value for the region
                     "add_fields": [['MinorityLength', 'double'], ['PMinority', 'double'], ['MinorityRoute', 'SHORT']]}, # route fields to be added
                    {"org_file": poverty_file, 
                     "working_file":  poverty_working_file, 
                     "identified_field": "RegPovBG", 
                     "add_fields": [['PovertyLength', 'double'], ['PPoverty', 'double'], ['PovertyRoute', 'SHORT']]},
                    {"org_file": medhhinc_file, 
                     "working_file":  medhhinc_working_file, 
                     "identified_field": "RegBelMedInc", 
                     "add_fields": [['MedHHIncLength', 'double'], ['PMedHHInc', 'double'], ['MedHHIncRoute', 'SHORT']]},
                    {"org_file": lep_file, 
                     "working_file":  lep_working_file, 
                     "identified_field": "RegAbvLEP",
                     "add_fields": [['LEPLength', 'double'],['PLEP', 'double'], ['LEPRoute', 'SHORT']]}]

    # ! is this a helper function now
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

    # loop through each demographic category, first collecting inputs from the working list,
    # then 
    for item in working_list:
        # WORKING LIST ITEM DEFINITIONS
        org_file = item["org_file"]
        working_file = item["working_file"]
        identified_field = item["identified_field"]
        add_fields = item["add_fields"]
        routes_analysis = "routes_" + str(working_file)
        length_field = add_fields[0][0]
        percent_field = add_fields[1][0]
        id_field = add_fields[2][0]

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
        selected_bg = str(identified_field) + " = 1" # "where" expression filtering for identified blockgroups
        print(selected_bg)
        ap.FeatureClassToFeatureClass_conversion(org_file, working_gdb, working_file, selected_bg)
        print(working_file + " CREATED!!!")

        ap.FeatureClassToFeatureClass_conversion(routes_working, working_gdb, routes_analysis)
        print(routes_analysis + " FILE CREATED!!!")

        ap.Dissolve_management(working_file, dissolve_file, '') # dissolve all into one shape
        print(dissolve_file + " CREATED!!!")

        ap.Buffer_analysis(dissolve_file, buffer_file, "50 feet") # buffer by 50 feet
        print(buffer_file + " CREATED!!!")

        ap.Clip_analysis(routes_working, buffer_file, clip_routes) # clip routes using the dissolve shape
        print(clip_routes + " CREATED!!!")


        # calculate length of route inside identified blockgroups and compare to total length 
        ap.AddField_management(clip_routes, "IdLength", "double")
        print("IdLength Field Added for " + working_file)

        ap.CalculateField_management(clip_routes, "IdLength", "!shape.geodesicLength@miles!")
        print("IdLength Field Calculated for " + working_file)

        ap.Dissolve_management(clip_routes, dissolve_routes, 'RouteAbbr', [["IdLength", 'sum']]) # collect route pieces by route
        print(clip_routes + " DISSOLVED")

        ap.JoinField_management(routes_working, "RouteAbbr", dissolve_routes, "RouteAbbr", ["SUM_IdLength"]) # join and sum ID'ed length
        print(routes_working + " JOINED WITH " + dissolve_routes)

        ap.AddFields_management(routes_working, add_fields)
        print("FIELDS ADDED TO " + routes_working)

        # compute percentage of total that is ID'ed then flag if greater than 0.33
        ap.CalculateFields_management(routes_working, 'PYTHON3', [[length_field, '!SUM_IdLength!'],
                                                                  [percent_field, f'percent(!{length_field}!, !FullLength!)']],
                                      '''def percent(calc, full):
                                        if calc is None:
                                            return 0
                                        else:
                                            return calc / full
                                    ''')
        ap.CalculateFields_management(routes_working, 'PYTHON3', [[id_field, f'ifBlock(!{percent_field}!)']],
                                      '''def ifBlock(percent):
                                        if percent > 0.33:
                                            return 1
                                        else:
                                            return 0
                                    ''')
        print(routes_working + " FIELDS CALCULATED")

        ap.DeleteField_management(routes_working, "SUM_IdLength")
        print("IdLength Field Deleted")

    ## loop end ##
    
    ap.ClearWorkspaceCache_management()

    deleteFeatureClass(routes_file, final_gdb_loc)


    # CREATE FINAL FEATURE CLASS
    ap.FeatureClassToFeatureClass_conversion(routes_file, final_gdb_loc, routes_file)
    print("---------------------------")

