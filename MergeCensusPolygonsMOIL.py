import arcpy as ap
import os

env = ap.env.workspace = os.path("W:\Research&Development\Data-Share\layers\Missouri_ACS_5yr_GDB")

final_name = "ACS_2013_5YR_BG"
il_path = os.path.join("W:\Research&Development\Data-Share\layers\Missouri_ACS_5yr_GDB\ACS_2013_5YR_BG_17.gdb\ACS_2013_5YR_BG_17_ILLINOIS.gdb", "ACS_2013_5YR_BG_17_ILLINOIS")

mo_path = os.path.join("W:\Research&Development\Data-Share\layers\Missouri_ACS_5yr_GDB\ACS_2013_5YR_BG_29.gdb\ACS_2013_5YR_BG_29_MISSOURI.gdb", "ACS_2013_5YR_BG_29_MISSOURI")
outputgdb = "W:\Research&Development\Data-Share\layers\Missouri_ACS_5yr_GDB\merge.gdb"
