# this is a preprocessing input to create MO + IL merged bg files 
import arcpy
from arcpy import env

year = str(input('What Year "YY": '))
env.workspace = rf"W:\Research&Development\Data-Share\layers\ACS\ACS_20{year}_5YR_BG"
# merge = r"W:\Research&Development\Data-Share\analysis-dev\TitleVI\MetroReimagined_190917\MR_TitleVI_Analysis_190917\merge.gdb"

merge_list = [
    [[f"mo.gdb\ACS_20{year}_5YR_BG_29_MISSOURI", f"il.gdbf\ACS_20{year}_5YR_BG_{year}_ILLINOIS"], f"merge.gdb\ACS_20{year}_5YR_BG"],
    [["mo.gdb\X00_COUNTS", "il.gdb\X00_COUNTS"], f"merge.gdb\X00_COUNT{year}"],
    [["mo.gdb\X01_AGE_AND_SEX", "il.gdb\X01_AGE_AND_SEX"], "merge.gdb\X01_AGE_AND_SEX"],
    [["mo.gdb\X02_RACE", "il.gdb\X02_RACE"], "merge.gdb\X02_RACE"],
    [["mo.gdb\X03_HISPANIC_OR_LATINO_ORIGIN", "il.gdb\X03_HISPANIC_OR_LATINO_ORIGIN"], "merge.gdb\X03_HISPANIC_OR_LATINO_ORIGIN"],
    [["mo.gdb\X09_CHILDREN_HOUSEHOLD_RELATIONSHIP", "il.gdb\X09_CHILDREN_HOUSEHOLD_RELATIONSHIP"], "merge.gdb\X09_CHILDREN_HOUSEHOLD_RELATIONSHIP"],
    [["mo.gdb\X11_HOUSEHOLD_FAMILY_SUBFAMILIES", "il.gdb\X11_HOUSEHOLD_FAMILY_SUBFAMILIES"], "merge.gdb\X11_HOUSEHOLD_FAMILY_SUBFAMILIES"],
    [["mo.gdb\X12_MARITAL_STATUS_AND_HISTORY", "il.gdb\X12_MARITAL_STATUS_AND_HISTORY"], "merge.gdb\X12_MARITAL_STATUS_AND_HISTORY"],
    [["mo.gdb\X15_EDUCATIONAL_ATTAINMENT", "il.gdb\X15_EDUCATIONAL_ATTAINMENT"], "merge.gdb\X15_EDUCATIONAL_ATTAINMENT"],
    [["mo.gdb\X16_LANGUAGE_SPOKEN_AT_HOME", "il.gdb\X16_LANGUAGE_SPOKEN_AT_HOME"], "merge.gdb\X16_LANGUAGE_SPOKEN_AT_HOME"],
    [["mo.gdb\X17_POVERTY", "il.gdb\X17_POVERTY"], "merge.gdb\X17_POVERTY"],
    [["mo.gdb\X19_INCOME", "il.gdb\X19_INCOME"], "merge.gdb\X19_INCOME"],
    [["mo.gdb\X20_EARNINGS", "il.gdb\X20_EARNINGS"], "merge.gdb\X20_EARNINGS"],
    [["mo.gdb\X21_VETERAN_STATUS", "il.gdb\X21_VETERAN_STATUS"], "merge.gdb\X21_VETERAN_STATUS"],
    [["mo.gdb\X25_HOUSING_CHARACTERISTICS", "il.gdb\X25_HOUSING_CHARACTERISTICS"], "merge.gdb\X25_HOUSING_CHARACTERISTICS"]
]

for tables in merge_list:
    arcpy.Merge_management(tables[0], tables[1])
    print(f'{tables[0][0]} and {tables[0][1]} merged')