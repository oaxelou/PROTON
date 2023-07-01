#  An automated script that creates a PROTON project by parsing a 
# SPICE powergrid file. It sets the parameters for technology and 
# temperature for the given powergrid and selected the line to be 
# analyzed along with a given width. 
#  Then, it performs EM transient stress analysis on the selected 
# line and opens the user interface to plot the results.
#
# Author: Olympia Axelou
# Affiliation: University of Thessaly, Greece
# Date: 19/6/2023


# Create project
set_powergrid C:\Users\olymp\Documents\GitHub\EM_analysis_tool\benchmarks\ibmpg1.spice
set_project_path C:\Users\olymp\Desktop
set_project_name automated_ibmpg2
parse_powergrid

# Set technology, temperature, width
set_technology CuDD
set_temperature 378
set_line_width 1

# Select line
select_line M5_n1_1
# show_lines

# Discretize and Perform analysis on selected line
discretize_line --points 5000
analyze_line 6.38e8 1e6 30

# Open GUI to see plot
g

# Quit
q
