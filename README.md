# Title VI Equitable Analysis 
## Intro
The Title VI Analysis script was designed by Metro St Louis in response to a Triannual review that was requested by the Federal Transit Administration. This script attempts to automate the process of analyzing the amount of people of specific identified populations and attempts to compare them to a specific set of route and stop files to make assumptions. 

This script at this moment only works for Metro St Louis' specifically, because it uses a specific set of fields that are a part of the Open Data specification at [data.metrostlouis.org](https://data.metrostlouis.org/).

## helpers.py
This file does exactly what you think it does. It is a set of functions that are used throughout the script to help with generalized GIS and data management functions.
### deleteFeatureClass(file, loc)
This function deletes a local feature class it does check to see if the file is in the location (loc). If it is there it delete's it.

### deleteFolder(loc)
Checks to see if the folder exists and if it exists delete it.

### clipCalc(table, fields)
Feed in the table (or feature service) and the fields that you want to calculate assumes that there is a field called "sqmiles_coverage".


### replaceGDB(root_dir, gdb)
Deletes and recreates a gdb in the root directory


### calcSqMiles(fc, field)
Calculates the feature class square miles with a custom name with Field Calculator.


### clipPolygons(census_gdb, census_file, boundary_file, output_gdb, output_file)
The clip polygons function is meant to clip all of the polygons (blockgroups or tract) and then run the rest of the analysis. So it just runs at the begining onec for all of the files. 

The process creates 2 feature classes because you need to be able to compare the original to the new and could probaly be done with one, but I didn't want to add another field to a file that is to remain pure as a reference file. You could probably delete the '_init' file at the end of this process as well.

### joinAndCalcFields(fc, census_gdb, output_gdb, key, table, table_key, fields_list)
This process takes a feature class with a census_gdb (orginal location), an output_gdb, the common field (key), the table you want to join, and the common table_key that matches key. 

Once the join is done if calculates all the fields in fields_list using the 'coverage' field that was produced in `clipPolygons()`


### cleanUp(twrw_places, gdb, final_file, final_gdb_loc, delete_fields)
***the parameters in this function could be updated as they are referencing some specific to where this was originally called***

Bassically this function deletes a bunch of fields and then pushes it to the final location. You could probably reverse it and export and then delete the fields. that might make more sense but you might need to change arcpy workspaces.


### checkforfield(fc, field, type)



## idRoutes.py

calculates identified routes based on the fta guidence looking at the total distance that is in identified block groups or census tracts. if the length in identified zones > 33% than it is an identified route.

## lep.py

Creates lep.gdb and copies final feature class to the final gdb. 
lep is limited english proficency and looks total populations above 5 years old

## lowCar.py

Creates low car gdb copies files to final gdb.
Low car calculates 0-1 car households and 0 car households. 

## medHHInc.py

Median household income calculations

## minority.py

Minority Calculations uses total populations and Minority is calculated by looking at the total number of non-white populations and the total population that identifies as white and hispanic. The non-white hispanic populations are already captured in the race tables. 

## poverty.py
This is where the low income households are calculated. the definition of what a low income household is 150% of the poverty line. 


## senior.py
Total people above 65 statistics.

## stopSpacing.py

Stop spacing is an after thought to this whole process. It takes in some custom inputs and is not fully integrated in the process, but it will split routes by direction with the associated stops and then measures out the distance between stops. 

## tni.py

the Transit Need Inex is a failed attempt at analyzing transit propensity. It takes Population, Senior, Median Househould income and No Car population densities to create a metric to predict demand and determine a good level of service or isolate areas that need more transit. This was the original way of calculating stop distances for the 2018 Title VI analysis. 