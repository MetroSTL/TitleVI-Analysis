# ! are the imports needed if they are defined in main?

import arcpy
import os
import shutil

from helpers import *

# ! are we using tni at all? 
# Compute Transit Need Index (TNI) based on the 2003 service standards for each census blockgroup.
# Use the minority, income, age and car ownership data computed in prior functions as inputs, and
# add a feature class indicating TNI to the final output gdb (final_gdb_loc)
def tni(year, root_dir, final_gdb_loc): 
   arcpy.env.overwriteOutput = True

   # set a working gdb
   gdb = f"TransitNeedIndex{year}.gdb"
   replaceGDB(root_dir, gdb)
   gdb_loc = os.path.join(root_dir,gdb)

   # define input feature classes, generated from prior functions
   minority_fc = os.path.join(final_gdb_loc, f'Minority{year}_final')
   medhhinc_fc = os.path.join(final_gdb_loc, f'MedHHInc{year}_final')
   senior_fc = os.path.join(final_gdb_loc, f'Senior{year}_final')
   NoCar_fc = os.path.join(final_gdb_loc, f"NoCar{year}_Final")

   arcpy.env.workspace = os.path.join(root_dir, gdb)  # -----> Change Year # ! what is this comment?
   arcpy.ClearWorkspaceCache_management()

   # MAke a working feature class from a copy of the minority fc. Define minority TNI fields and calculate them
   TNI_Minority = arcpy.conversion.FeatureClassToFeatureClass(in_features=minority_fc, out_path=arcpy.env.workspace, out_name=f"TNI_Minority{year}")

   arcpy.management.AddFields(in_table=TNI_Minority, field_description=[["TNI_Minority", "DOUBLE"],["PopDens", "DOUBLE"],["RegPopDens", "DOUBLE"],["TNI_Pop", "DOUBLE"]])

   # ! should this use percentage rather than density? If we use this later on I can adjust (if it should be adjusted)
   # Process: Calculate Field (6) (Calculate Field) (management)
   arcpy.management.CalculateField(in_table=TNI_Minority, field="PopDens", expression="!TPOP! / !SqMiles!", expression_type="PYTHON3", code_block="", field_type="TEXT")
   arcpy.management.CalculateField(in_table=TNI_Minority, field="RegPopDens", expression="!RegTPOP! / !RegSqMiles!", expression_type="PYTHON3", code_block="", field_type="TEXT")
   arcpy.management.CalculateField(in_table=TNI_Minority, field="TNI_Minority", expression="!MinorityDens! / !RegMinorityDens!", expression_type="PYTHON3", code_block="", field_type="TEXT")
   arcpy.management.CalculateField(in_table=TNI_Minority, field="TNI_Pop", expression="!PopDens! / !RegPopDens!", expression_type="PYTHON3", code_block="", field_type="TEXT")

   # copy income fc, define TNI fields, and join to minority working fc. 
   # note that median income is used directly in TNI calcs.
   TNI_MedHHInc = arcpy.conversion.FeatureClassToFeatureClass(in_features=os.path.join(final_gdb_loc, medhhinc_fc), out_path=gdb_loc, out_name=f"TNI_MedHHInc{year}")[0]

   arcpy.management.AddFields(in_table=TNI_MedHHInc,field_description=[["TNI_MedInc", "DOUBLE"],["TNI_MedInc", "DOUBLE"]])

   TNI_Minority_MedHHInc_Join = arcpy.management.JoinField(in_data=TNI_Minority, in_field="GEOID", join_table=TNI_MedHHInc, join_field="GEOID", fields=["RegMedHHInc", "MedHHInc", "TNI_MedInc"])[0]


   # same as above, with senior
   TNI_Senior = arcpy.conversion.FeatureClassToFeatureClass(in_features=os.path.join(final_gdb_loc, senior_fc), out_path=gdb_loc, out_name=f"TNI_Senior{year}")[0]

   arcpy.management.AddField(in_table=TNI_Senior, field_name="TNI_Senior", field_type="DOUBLE")

   arcpy.management.CalculateField(in_table=TNI_Senior, field="TNI_Senior", expression="!SeniorDens! / !RegSeniorDens!", expression_type="PYTHON3", code_block="", field_type="DOUBLE")

   TNI_Join = arcpy.management.JoinField(in_data=TNI_Minority_MedHHInc_Join, in_field="GEOID", join_table=TNI_Senior, join_field="GEOID", fields=["TSenior", "SeniorDens", "RegSeniorDens", "TNI_Senior"])[0]



   # Same as above, with zero car households
   TNI_NoCar = arcpy.conversion.FeatureClassToFeatureClass(in_features=os.path.join(final_gdb_loc, NoCar_fc), out_path=gdb_loc, out_name="TNI_NoCar",)[0]

   arcpy.management.AddField(in_table=TNI_NoCar, field_name="TNI_NoCar", field_type="DOUBLE")[0]
   arcpy.management.AddField(in_table=TNI_NoCar, field_name="TNI_LowCar", field_type="DOUBLE")[0]

   arcpy.management.CalculateField(in_table=TNI_NoCar, field="TNI_NoCar", expression="!NoCarDens! / !RegNoCarDens!", expression_type="PYTHON3", field_type="DOUBLE")[0]
   arcpy.management.CalculateField(in_table=TNI_NoCar, field="TNI_LowCar", expression="!LowCarDens! / !RegLowCarDens!", expression_type="PYTHON3", code_block="", field_type="TEXT")[0]

   TNI_Join = arcpy.management.JoinField(in_data=TNI_Join, in_field="GEOID", join_table=TNI_NoCar, join_field="GEOID", fields=["TNoCar", "NoCarDens", "RegNoCarDens", "TNI_NoCar", "TLowCar", "LowCarDens", "RegLowCarDens", "TNI_LowCar"])[0]


   # Create and calculate the TNI
   arcpy.management.AddField(in_table=TNI_Join, field_name="TNI", field_type="DOUBLE")
   arcpy.management.CalculateField(in_table=TNI_Join, field="TNI", expression="(!TNI_MedInc!*3.5)+(!TNI_Minority!*1)+(!TNI_Senior!*1)+(!TNI_LowCar!*1.5)+(!TNI_Pop!*2)", expression_type="PYTHON3", field_type="TEXT")


   # compare each blockgroup's TNI to the regional TNI
   # Determine the regional mean and standard deviation TNI, then join to each blockgroup. 
   # Finally, define each regions need (Very Low to High) based on how it compares to regional TNI
   TNI_Join_Dissolve = arcpy.management.Dissolve(in_features=TNI_Join, out_feature_class=f"{TNI_Join}_dissolve", dissolve_field=[], statistics_fields=[["TNI", "STD"], ["TNI", "MEAN"]], multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")[0]

   TNI_Join_Dissolve_SpJoin = arcpy.analysis.SpatialJoin(target_features=TNI_Join, join_features=TNI_Join_Dissolve, out_feature_class=f'{TNI_Join_Dissolve}_SpJoin', join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL")[0]

   arcpy.management.AddField(in_table=TNI_Join_Dissolve_SpJoin, field_name="Propensity", field_type="DOUBLE")[0]

   arcpy.management.CalculateField(in_table=TNI_Join_Dissolve_SpJoin, field="Propensity", expression="ifBlock(!TNI!,!STD_TNI!,!MEAN_TNI!)", expression_type="PYTHON3", code_block='''def ifBlock(TNI, STD_TNI, MEAN_TNI):
  if TNI < (MEAN_TNI-(STD_TNI*1.5)):
     return \"VL\"
  elif TNI > (MEAN_TNI-(STD_TNI*1.5)) and TNI < (MEAN_TNI-(STD_TNI*.5)):
     return \"L\"
  elif TNI > (MEAN_TNI-(STD_TNI*.5))  and TNI < (MEAN_TNI+(STD_TNI*.5)):
     return \"A\"
  elif TNI > (MEAN_TNI+(STD_TNI*.5)) and TNI < (MEAN_TNI+(STD_TNI*1.5)):
     return \"H\"
  elif TNI > (MEAN_TNI+(STD_TNI*1.5)):
     return \"VH\"
  else:
     return \"ERROR\"
     ''', field_type="TEXT")[0]

   # create TNI feature classes within output gdb's
   arcpy.conversion.FeatureClassToFeatureClass(in_features=TNI_Join_Dissolve_SpJoin, out_path=gdb_loc, out_name=f"TNI{year}_Final")[0]
   arcpy.conversion.FeatureClassToFeatureClass(in_features=TNI_Join_Dissolve_SpJoin, out_path=final_gdb_loc, out_name=f"TNI{year}_Final")[0]
