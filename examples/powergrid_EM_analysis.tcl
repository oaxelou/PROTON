#  An automated script that parses a SPICE powergrid file and performs
# Electromigration (EM) analysis on the complete powergrid at specific 
# time (e.g. chip lifetime) and finds the EM-susceptible lines.
#  Then, some statistics on the parsed powergrid are reported as well   
# as the line with the maximum stress.
#
# Author: Olympia Axelou
# Affiliation: University of Thessaly, Greece
# Date: 19/6/2023

# Create new project
set_powergrid C:\Users\olymp\Documents\GitHub\EM_analysis_tool\benchmarks\ibmpg1.spice
set_project_path C:\Users\olymp\Desktop
set_project_name automated_ibmpg1
parse_powergrid
# open_project C:\Users\olymp\Desktop\automated_ibmpg1

# Set technology, temperature, line width
set_technology CuDD
set_temperature 378
set_line_width 1

# Complete powergrid EM stress check at 20y (6.38e8s) for a random sample of 100 lines
# and check for lines that exceed the critical stress of 10KPa
analyze 6.38e8 --sample 100 --critical 10000

# Export stats on the powergrid and EM stress results
report_powergrid_stats --file C:\Users\olymp\Desktop\powergrid_stats.txt
report_line_stress --maxstress --file C:\Users\olymp\Desktop\critical_line_stress.csv

# Quit
quit