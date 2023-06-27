from argparse import HelpFormatter, ArgumentParser
import argparse
from collections.abc import Sequence
from typing import Any
from prettytable import PrettyTable, ALL
import os
from sys import platform
import shutil
import json
import time
from tqdm import tqdm
import glob 
# import multiprocessing
from functools import partial
import concurrent.futures
from threading import Lock
import threading
import random
import signal
from unidecode import unidecode

from spice_function_cli import *
import spice_function_cli
from matrix_formulation_func_cli import *
from analytical_class_cli import *
from transient_class_cli import *
import GUI_auxiliary
from GUI_auxiliary import save_project_details, save_config_file, extract_numbers
from PROTON_main import main, extract_number_between, open_project_main
import history_handling

if platform == "win32":
	# print('Windows!')
	IS_LINUX = False
	INSTALLATION_FOLDER = "C:/Users/olymp/Documents/GitHub/EM_analysis_tool/"
else:
	# print('Linux!')
	IS_LINUX = True
	INSTALLATION_FOLDER = "/home/proton/Documents/GitHub/EM_analysis_tool/"

if not os.path.exists(INSTALLATION_FOLDER):
	INSTALLATION_FOLDER = os.getcwd()

commands = {}
commands["help"] = (" (h)", "", "Documentation of the commands.")
commands["quit"] = (" (q)", "", "Command to exit PROTON CLI tool.")
commands["gui"] = (" (g)", "", "Command to open the GUI of PROTON tool.\nIf set_project_path has been run, then open the specified project.")
commands["source"] = (" <commands file>", "", "Command to source a file with commands.\nArguments: filename with the commands")
commands["set_powergrid"] = (" <powergrid filename>", "", "Command to set the path to the powergrid SPICE file.\nArguments: SPICE file")
commands["set_project_path"] = (" <project path>", "", "Command to set the path for the project.\nArguments: project path")
commands["set_project_name"] = (" <project name>", "", "Command to set the project name.\nArguments: project name")
commands["parse_powergrid"] = (" -y/n", "set_powergrid,\nset_project_path,\nset_project_name", "Command to set parse the given powergrid and create the project.\nArguments: -y/n for automated response in possible questions.")
commands["open_project"] = (" <project path> -y/n", "", "Command to open an existing PROTON project.\nArguments: -y/n for automated response in possible questions.")
commands["show_lines"] = (" <layer>", "parse_powergrid or open_project", "Command to show all the parsed lines of the powergrid.\nArguments: (optional) The layer of the powergrid for filtering")
commands["select_line"] = (" <line>", "parse_powergrid or open_project", "Command to select a line of the powergrid.\nArguments: The line of the powergrid to select")
commands["set_technology"] = (" <technology>", "parse_powergrid or open_project", "Command to set the technology for the analysis.\nArguments: The selected technology")
commands["set_temperature"] = (" <temperature (K)>", "parse_powergrid or open_project", "Command to set the temperature for the analysis.\nArguments: The selected temperature in K")
commands["set_line_width"] = (" <width (um)>", "parse_powergrid or open_project", "Command to set the line width for the analysis.\nArguments: The selected line width in um")
commands["set_discr_points"] = (" <num. of points>", "parse_powergrid or open_project", "Command to set the number of discretization points for the spatial FDM procedure.\nArguments: The chosen number of discritization points")
commands["set_discr_step"] = (" <spatial step>", "parse_powergrid or open_project", "Command to set the discretization step for the spatial FDM procedure.\nArguments: The chosen discretization step")
commands["discretize_line"] = (" --step <disc. step>\ndiscretize_line --points <disc. points>", "parse_powergrid or open_project,\nselect_line,\nset_line_width,\n(optional) set_discr_points or set_discr_step", "Command to discretize the line with the spatial FDM procedure.\nArguments (optional if commands set_disc_points or set_disc_step are executed): The discretization step (um) or the discretization points")
commands["analyze_line"] = ("  <time> <timestep (op)> <reduced_size (op)>", "parse_powergrid or open_project,\ndiscretize_line", "Command to compute the EM stress.\nArguments: The simulation time <time>,\n<timestep> (optional: If set, then transient analysis on the selected via is performed),\n<reduced size> (optional: Must be accompanied by <timestep>. If set, then MOR is performed before the analysis)")
commands["report_powergrid_stats"] = ("  --file <filename>", "parse_powergrid or open_project", "Command to report statistics on the parsed powergrid.\nArguments: --file <filename> (optional: If set, then the report is saved in a file)")
commands["report_line_stress"] = ("  <line> --maxstress --file <filename>", "parse_powergrid or open_project", "Command to report the EM stress results on selected line.\nArguments: \n<line>\n--maxstress (optional: If set, the stress on the line with the maximum stress is reported)\n--file <filename> (optional: If set, then the report is saved in a file)")
commands["report_transient_stress"] = ("  <line> <via> --file <filename>", "parse_powergrid or open_project", "Command to report the EM transient stress results on selected via of a line.\nArguments: \n<line> \n<via> \n--file <filename> (optional: If set, then the report is saved in a file)")
commands["analyze"] = ("  <time> --critical <critical stress (op)> --sample <sample lines (op)", "parse_powergrid or open_project", "Command to perform complete powergrid EM stress analysis.\nArguments: \n<time> \n<critical stress> (optional: If set, then the commands finds all lines that exceed the critical stress) \n<sample lines> (optional: If set, then a number of lines is only analyzed)")


PROTON_STRING ='''
█▀█ █▀█ █▀█ ▀█▀ █▀█ █▄ █ 
█▀▀ █▀▄ █▄█  █  █▄█ █ ▀█'''

PROTON_UNICODE_STRING = r'''
  _____  _____   ____ _______ ____  _   _ 
 |  __ \|  __ \ / __ \__   __/ __ \| \ | |
 | |__) | |__) | |  | | | | | |  | |  \| |
 |  ___/|  _  /| |  | | | | | |  | | . ` |
 | |    | | \ \| |__| | | | | |__| | |\  |
 |_|    |_|  \_\\____/  |_|  \____/|_| \_|'''
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# Commands:
# 1. (DONE) set_powergrid
#	 (DONE) set_project_path (an einai idi project tote -> open an oxi -> new)
#	 (DONE) set_project_name
#	 (DONE) parse_powergrid # TO-DO: Isws na mporei na dwsei to arxeio me ta currents kai oxi by default na to lunei
#	 (dependencies: set_project_path and set_project_name and set_powergrid)
#	(DONE) open_project

# 2. (DONE) gui () # TO-DO: Na anoigei to teleutaio analyze pou exei kanei 
#	(dependencies: if set_project_path and set_project_name and set_powergrid and parse_powergrid)

# 3. (DONE) show_lines <optional: layer>
#	 (DONE) select_line <Line name>

# 4. (DONE) set_technology (optional "Technology has not been set. Selecting the default value of Copper Dual-Damascene (CuDD)" - 
#					An to trexei kapoios exei upoxrewtika options: CuDD/Al)
#	 (DONE) set_temperature (optional "Temperature has not been set. Selecting 378K.")
#	 (DONE) set_line_width (Mandatory)
# 5. (DONE) set_discr_points (ena apo ta dyo ypoxrewtika)
#	 (DONE) set_discr_step
#	 (DONE) discretize_line

# 6. (DONE) analyze_line <time> <timestep (op)> <reduced_size (op)>
#				 (na ektupwnei pou exei apothikeutei i analusi)

# 7. (DONE) analyze <time> <critical stress> (Analyze the whole powergrid with the sparsest possible discretization)
# Epanaliptika tha koitaei mexri na kanei discretize to line me to kalutero 
# (ksekinontas apo to min length olwn twn segments)
# (Vale parallelization OpenMP)
# Max stress found at line tade of net tade. (critical stress)
# Se posa lines apo ola ta lines kanei fail
# Max stress
# Meta: analyze_line (me to max stress)


# 8. (DONE) report_powergrid_stats --file <filename> 
#	(DONE) report_line_stress <line> --maxstress --file <filename> 
#	(DONE) report_transient_stress <line> <via> --file <filename> 

# 9. (DONE) source <tcl file>

# DONE: Ftiakse tcl script me tis analuseis kai sto telos gui gia na plotarei tis grafikes
# (DONE) Ftiakse na agnoei ta comments (single-line)
def gui():
	global directory
	print("Opening GUI...")
	# If set_project_path has been run, then open the specified project
	# else, simply open GUI

	if directory != "":
		# print(f"There is already an open project at {directory}.")
		# open_project_main(directory=directory, line_plot=r'C:\Users\olymp\Desktop\oly_cli\output\M5_n0_1\CuDD_378.0_1.0\stress_100000000.000000.txt')
		open_project_main(directory=directory)
	else:
		main()



directory = ""
powergrid = ""
def set_powergrid(spice_file):
	global powergrid
	powergrid = spice_file

project_path = ""
def set_project_path(given_path):
	global project_path
	project_path = given_path

project_name = ""
def set_project_name(given_name):
	global project_name
	if not given_name.isascii():
		print("Project name should be an ASCII string.")
		return 1
	project_name = given_name

parsed_powergrid = False
def parse_powergrid(response=None):
	global directory, parsed_powergrid, powergrid, project_path, project_name, max_stress_loc, IS_LINUX, INSTALLATION_FOLDER
	spice_file_entry = powergrid
	project_location_entry = project_path
	project_name_entry = project_name
	
	if directory != "":
		if response is None:
			answer = input("A project is already opened. Do you wish to close it and create another? (y/n)\n")
			if answer.lower() == "n":
				print("The project was not created.")
				return 1
			elif answer.lower() != "y":
				print("Invalid answer. Try again")
				return 1
		elif response == 'n':
			print("The project was not created.")
			return 1
		
	if parsed_powergrid:
		print(f"Powergrid file has already been parsed for this project.")
	if (project_name_entry and project_location_entry and spice_file_entry):
		project_location_entry = project_location_entry
		spice_file_entry = spice_file_entry

		# print(project_location_entry)
		if not os.path.exists(project_location_entry):
			try:
				os.mkdir(project_location_entry)
			except PermissionError as e:
				print(f"The project cannot be created at {project_location_entry} due to permission errors.")
		# else:
		# 	print("The given directory for the PROTON project already exists.")
		# 	return 1
		
		directory = os.path.join(project_location_entry, project_name_entry)
		try:
			os.mkdir(directory, 0o777)
		except FileExistsError as e:
			print(f"\'{project_name_entry}\' project exists already. Choose a different path or project name.")
			directory = ""
			return 1
		except PermissionError as e:
			print(f"The project cannot be created at {directory} due to permission errors.")
			directory = ""
			return 1

		#-----------------------------------------------------#
		# project_location_entry = directory

		message_log_path = directory + "/history_log.txt"
		open(message_log_path, "x")
		
		# # # # # # THREAD # # # # # # # #
		spice_parser_worker = Spice_Parser_Class(spice_file_entry,directory, IS_LINUX, INSTALLATION_FOLDER)
		return_message = spice_parser_worker.spice_parser()

		if "seconds" in return_message:
			return_string = f'Spice file was successfully parsed {return_message} and the project has been created at {os.path.normpath(directory)}.'

			save_project_details(project_name_entry, project_location_entry, spice_file_entry, spice_function_cli.benchmark)
			save_config_file(False, directory)
			with open(os.path.join(directory, "config.json"), "r") as json_file:
				GUI_auxiliary.json_data_sim = json.load(json_file)

			# Call the function for the new layout
			exec_time = extract_number_between(return_message, "in", "seconds")
			# if exec_time is not None:
				# if window is not None:
				# 	create_main_window(window, GUI_auxiliary.directory, "new", exec_time)
			parsed_powergrid = True
			print(return_string)
			max_stress_loc = None
			return 0

		if "seconds" not in return_message or exec_time is None:
			if "seconds" in return_message and exec_time is None:
				return_string = "An error occured while parsing the parsing execution time."
				print(return_string)
			print(return_message)
			print(f"Going to delete project {directory}...")
			shutil.rmtree(directory)
			# create_open_project_form(window, "both")
			
			return 1

		print("Should never reach this")
		return 1
		# # # # # # # # # # # # # #

	else:
		depend_string = "For parse_powergrid command, the following dependencies are missing:\n"
		if powergrid is None or powergrid == "":
			depend_string += "  set_powergrid\n"
		if project_path is None or project_path == "":
			depend_string += "  set_project_path\n"
		if project_name is None or project_name == "":
			depend_string += "  set_project_name\n"
		print(depend_string)
		return 1

def open_project(given_path, response=None):
	global directory, max_stress_loc

	if directory != "":
		if response is None:
			answer = input("A project is already opened. Do you wish to close it and open another? (y/n)\n")
			if answer.lower() == "n":
				print("The project was not opened.")
				return 1
			elif answer.lower() != "y":
				print("Invalid answer. Try again")
				return 1
		elif response == 'n':
			print("The project was not opened.")
			return 1


	# Check if the given dir is a PROTON project
	directory = given_path
	temp_path_to_json = directory + "/" + "PROTON_project_details.json" 
	checkExists =os.path.exists(temp_path_to_json)
	
	if checkExists == False:
		print("The given location isn't a PROTON project. Try again.")
		directory = ""
		return 1

	#temp_path_to_json = directory + "/" + "PROTON_project_details.json" 
	with open(temp_path_to_json, "r") as fd:
		details_json = json.load(fd)

	if "magic_word" not in details_json or details_json["magic_word"] != "papaya56":
		print("The given location isn't a PROTON project. Try again.")
		directory = ""
		return 1
	
	#print(details_json)
	directory_from_details = details_json["full_path_to_project"]
	powergrid = details_json["spice_path"]
	benchmark_given = details_json["parsed_spice_path"]
	# Hide the previous layout and delete its widgets 

	message_log_path = os.path.exists(os.path.join(directory+ "/history_log.txt"))
	path_to_stastitics = os.path.exists(os.path.join(directory + "/statistics/Statistics.csv"))
	path_to_config = os.path.exists(os.path.join(directory + "/config.json"))

	# print(f'{os.path.normpath(directory+ "/history_log.txt")}: {message_log_path}')
	# print(f'{os.path.normpath(directory+ "/statistics/Statistics.csv")}: {path_to_stastitics}')
	# print(f'{os.path.normpath(directory+ "/config.json")}: {path_to_config}')
	if os.path.normpath(directory) != os.path.normpath(directory_from_details) or not message_log_path or not path_to_stastitics or not path_to_config or not os.path.exists(benchmark_given):
		message = "The given PROTON project is corrupted. Try again."
		if os.path.normpath(directory) != os.path.normpath(directory_from_details):
			message = f"The given PROTON was initially created at {directory_from_details} but it is instead at {directory}. Try recreating the project."
		print(message)
		directory = ""
		return 1
	
	spice_function_cli.benchmark = benchmark_given
	try:
		with open(os.path.normpath(directory+ "/config.json"), "r") as json_file:
			GUI_auxiliary.json_data_sim = json.load(json_file)
		
		if 'line' not in GUI_auxiliary.json_data_sim or 'technology' not in GUI_auxiliary.json_data_sim['line'] \
			or 'temperature' not in GUI_auxiliary.json_data_sim['line'] or 'width' not in GUI_auxiliary.json_data_sim['line']:
			raise ValueError
		if GUI_auxiliary.json_data_sim['line']['technology'] != "CuDD" and GUI_auxiliary.json_data_sim['line']['technology'] != "Al":
			raise ValueError
		float(GUI_auxiliary.json_data_sim['line']['temperature'])
		float(GUI_auxiliary.json_data_sim['line']['width'])

		if 'discretization' not in GUI_auxiliary.json_data_sim or 'parameter' not in GUI_auxiliary.json_data_sim['discretization'] \
			or 'points' not in GUI_auxiliary.json_data_sim['discretization'] or 'step' not in GUI_auxiliary.json_data_sim['discretization']:
			raise ValueError
		if GUI_auxiliary.json_data_sim['discretization']['parameter'] != 'step' \
			and GUI_auxiliary.json_data_sim['discretization']['parameter'] != 'points':
			raise ValueError
		float(GUI_auxiliary.json_data_sim['discretization']['points'])
		float(GUI_auxiliary.json_data_sim['discretization']['step'])
		

		if 'workspace_details' not in GUI_auxiliary.json_data_sim or 'selected_line' not in GUI_auxiliary.json_data_sim['workspace_details']:
			raise ValueError
	except:
		print(f"Cannot open project. Corrupted file: {os.path.normpath(directory+ '/config.json')}.")
		directory = ""
		return 1
	# return(f"spice_function_cli.benchmark: {spice_function_cli.benchmark}")
	print(f"Successfully opened project at {directory}.") 
	max_stress_loc = None
	return 0

def print_folder_contents(folder_path, indent=""):
	sorted_files = sorted(os.listdir(folder_path), key=extract_numbers)
	for item in sorted_files:
		item_path = os.path.join(folder_path, item)
		if os.path.isfile(item_path):
			print(indent + os.path.splitext(item)[0])
		elif os.path.isdir(item_path):
			print(indent + "[" + item + "]")
			print_folder_contents(item_path, indent + "  ")

def get_num_lines(folder_path):
	stack = [(folder_path, "")]
	
	num_lines = 0
	while stack:
		current_path, indent = stack.pop()
		sorted_files = sorted(os.listdir(current_path), key=extract_numbers)
		
		for item in sorted_files:
			item_path = os.path.join(current_path, item)
			
			if os.path.isfile(item_path):
				num_lines += 1
			elif os.path.isdir(item_path):
				stack.append((item_path, indent + "  "))
	return num_lines
		
def show_lines(layer):
	if spice_function_cli.benchmark == "":
		depend_string = "For show_lines command, the following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	if layer is None:
		print_folder_contents(spice_function_cli.benchmark)
	else:
		if not os.path.exists(os.path.join(spice_function_cli.benchmark, layer)):
			print(f"Layer {layer} does not exist in powergrid.")
		else:
			print_folder_contents(os.path.join(spice_function_cli.benchmark, layer))
	return 0

def find_line(folder_path, line):
	for item in os.listdir(folder_path):
		item_path = os.path.join(folder_path, item)
		if os.path.isfile(item_path):
			# print(f'{line} VS {os.path.splitext(item)}')
			if line in os.path.splitext(item):
				return True
		elif os.path.isdir(item_path):
			if find_line(item_path, line):
				return True
	return False 

selected_line = ""
def select_line(line, silent=False):
	global selected_line
	if spice_function_cli.benchmark == "":
		depend_string = "For show_lines command, the following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	found_line = find_line(spice_function_cli.benchmark, line)
	if found_line:
		selected_line = line
		if not silent:
			print(f"Line {line} was selected.")
			return 0
	else:
		if not silent:
			print(f"Line {line} does not exist in the powergrid.")
			return 1

technology = ""
def set_technology(tech):
	global technology
	if spice_function_cli.benchmark == "":
		depend_string = "For set_technology command, the following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	if tech.lower() == "cudd" or tech.lower() == "al":
		technology = tech
		print(f'Technology set to {"CuDD" if tech.lower() == "cudd" else "Al"}')
		return 0
	else:
		print("Wrong value for technology. Possible Options:\n CuDD for Copper Dual-Damascene\n Al for Aluminum")
		return 1

temperature = 0
def set_temperature(temp):
	global temperature
	if spice_function_cli.benchmark == "":
		depend_string = "For set_temperature command, the following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	try:
		if float(temp) > 0:
			temperature = float(temp)
			print(f"Temperature was set to {temperature} K.")
			return 0
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for temperature: It must be a positive real number.")
		return 1

width = 0
def set_line_width(given_width):
	global width
	if spice_function_cli.benchmark == "":
		depend_string = "For set_line_width command, the following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	try:
		if float(given_width) > 0:
			width = float(given_width)
			print(f"Line width was set to {width} um.")
			return 0
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for line width: It must be a positive real number.")
		return 1

disc_points = 0
def set_discr_points(given_disc_points):
	global disc_points
	if spice_function_cli.benchmark == "":
		depend_string = "The following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	try:
		if int(given_disc_points) > 0:
			disc_points = int(given_disc_points)
			print(f"The number of spatial discretization points was set to {disc_points}.")
			return 0
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for spatial discretization points: It must be a positive integer.")
		return 1

disc_step = 0
def set_discr_step(given_disc_step, silent=False):
	global disc_step
	if spice_function_cli.benchmark == "":
		depend_string = "The following dependencies are missing:\n"
		depend_string += "  set_powergrid\n"
		depend_string += " or \n"
		depend_string += "  open_project\n"
		print(depend_string)
		return 1
	try:
		if float(given_disc_step) > 0:
			disc_step = float(given_disc_step)
			if not silent:
				print(f"The spatial discretization step was set to {disc_step} um.")
			return 0
		else:
			raise ValueError
	except ValueError as e:
		print(f"given_disc_step: {given_disc_step}")
		print("Wrong argument for spatial discretization step: It must be a positive real number.")
		return 1

discr_size = 0
def _discr_line():
	global discr_size, directory, parsed_powergrid, powergrid, project_path

	# Check temperature and technology 
	if technology == "":
		print(" No technology was set. Selected the default technology: Copper dual-damascene (CuDD).")
		tech = "CuDD"
	else:
		tech = technology
	
	if temperature == 0:
		print(" No temperature was set. Selected the default temperature: 378K.")
		temp = 378.0
	else:
		temp = temperature

	temp_disc_points = None
	temp_disc_step = None
	if disc_points > 0:
		temp_disc_points = disc_points
		GUI_auxiliary.json_data_sim['discretization']['parameter'] = 'points'
		GUI_auxiliary.json_data_sim['discretization']['points'] = int(disc_points)
	if disc_step > 0:
		temp_disc_step = disc_step
		GUI_auxiliary.json_data_sim['discretization']['parameter'] = 'step'
		GUI_auxiliary.json_data_sim['discretization']['step'] = float(disc_step)
	
	csv_filename = spice_function_cli.benchmark + "/" + selected_line.split("_")[0] + "/" + selected_line+".csv"

	# # # # # # THREAD # # # # # # # #
	matrix_formulation_worker = Matrix_Formulation_Class(csv_file=csv_filename,project_location=directory,sp_step=temp_disc_step,given_disc_point=temp_disc_points,technology=tech,temperature=float(temp),givenWidth=float(width))
	return_message = matrix_formulation_worker.matrix_formulation()

	if "seconds" in return_message:
		message = f'Line {selected_line} was successfully discretized into {return_message}.'
		discr_size = int(return_message.split()[0])
		# print(f"Discretization size: {discr_size}")
		exec_time = extract_number_between(return_message, "in", "seconds")
		message_type = "success"
	else:
		message = return_message	
		message_type = "error"
	history_handling.write_message_in_log(directory+ "/history_log.txt", message, message_type)
	
	print(message)

	if "seconds" not in return_message or exec_time is None:
		if "seconds" in return_message and exec_time is None:
			message = "An error occured while parsing the matrix formulation time."
			print(message)
			history_handling.write_message_in_log(directory+ "/history_log.txt", message, "error")
		# print(f"Going to delete project {directory}...")
		# shutil.rmtree(directory)
	
	GUI_auxiliary.json_data_sim['line']['technology'] = tech
	GUI_auxiliary.json_data_sim['line']['temperature'] = temp
	GUI_auxiliary.json_data_sim['line']['width'] = width
	GUI_auxiliary.json_data_sim['workspace_details']['selected_line'] = selected_line
	save_config_file(True, directory)

	if message_type == "success":
		return 0
	else:
		return 1
	
def discr_line(disc_type=""):
	global disc_points, disc_step, selected_line, width, disc_points,  disc_step
	if spice_function_cli.benchmark == "" or selected_line == "" or width == 0 or (disc_points == 0 and disc_step == 0):
		depend_string = "The following dependencies are missing:\n"
		if spice_function_cli.benchmark == "": depend_string += "  set_powergrid or open_project\n"
		if selected_line == "": depend_string += "  select_line\n"
		if width == 0: depend_string += "  set_line_width\n"
		if disc_points == 0 and disc_step == 0: depend_string += "  set_discr_points or set_discr_step\n"
		print(depend_string)
		return 1

	if disc_type == "step":
		if disc_step > 0:
			# print(f"Going to start discretization with step {disc_step} um...")
			return _discr_line()
		else:
			print("Discretization step has not been set (should never reach this)")
			return 1
	elif disc_type == "points":
		if disc_points > 0:
			# print(f"Going to start discretization with {disc_step} discretization points.")
			return _discr_line()
		else:
			print("Discretization points has not been set (should never reach this)")
			return 1
	else:
		if disc_step > 0:
			# print(f"Going to start discretization with step {disc_step} um...")
			return _discr_line()
		elif disc_points > 0:
			# print(f"Going to start discretization with {disc_step} discretization points.")
			return _discr_line()
		else:
			print("Invalid argument for command discr_line: no discretization method was set.")
			return 1

def analytical(time, silent=False, line=None):
	global disc_points, disc_step, selected_line, width, technology, temperature
	global IS_LINUX, INSTALLATION_FOLDER
	if spice_function_cli.benchmark == "" or (not silent and selected_line == ""):
		depend_string = "The following dependencies are missing:\n"
		if spice_function_cli.benchmark == "": depend_string += "  set_powergrid or open_project\n"
		if selected_line == "": depend_string += "  select_line\n"
		print(depend_string)
		return 1
	
	# Check simulation time
	try:
		if float(time) > 0:
			sim_time = float(time)
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for simulation time: It must be a positive real number.")
		return 1
	
	# Check temperature and technology 
	if technology == "":
		if not silent:
			print(" No technology was set. Selected the default technology: Copper dual-damascene (CuDD).")
		tech = "CuDD"
	else:
		tech = technology
	
	if temperature == 0:
		if not silent:
			print(" No temperature was set. Selected the default temperature: 378K.")
		temp = 378.0
	else:
		temp = temperature

	if not silent:
		analytical_worker=Analytical_Class(sim_time=sim_time,directory=directory,selected_line=selected_line,TECHNOLOGY=tech,TEMPERATURE=temp,WIDTH=width,IS_LINUX=IS_LINUX, INSTALLATION_FOLDER=INSTALLATION_FOLDER)
	else:
		# try:
		analytical_worker=Analytical_Class(sim_time=sim_time,directory=directory,selected_line=line,TECHNOLOGY=tech,TEMPERATURE=temp,WIDTH=width,IS_LINUX=IS_LINUX, INSTALLATION_FOLDER=INSTALLATION_FOLDER)
		# except KeyboardInterrupt as e:
		# 	print("Analytical: Received Keyboardinterrupt")
		# 	raise KeyboardInterrupt
	return_message = analytical_worker.analytical_function()
	
	if "seconds" in return_message:
		#THA PREPEI TO APOTELESMA APO EDW NA GRAFTEI SE CONFIG.JSON GIA NA TO PAREI META TO SIMULATE?
		
		history_handling.write_message_in_log(directory+ "/history_log.txt", return_message, "success")
		# print(return_message)
		# print('Line analysis was successfully performed.')
		if not silent:
			line_path = selected_line+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"
		else:
			line_path = line+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"

		if not silent:
			output_files = os.path.normpath(directory + "/output/"+line_path)
			print(f"The simulation results can be found at {output_files}.")
		return 0
	else:
		history_handling.write_message_in_log(directory+ "/history_log.txt", return_message, "error")
		print(return_message)
		if(not silent and not selected_line):
			message = 'No line was selected and discretized prior to simulation.'
			print(message)
		return 1

def numerical(is_mor,time, step, reduced_size=None):
	global discr_size, selected_line, temperature, technology, width, IS_LINUX, INSTALLATION_FOLDER
	if spice_function_cli.benchmark == "" or selected_line == "":
		depend_string = "The following dependencies are missing:\n"
		if spice_function_cli.benchmark == "": depend_string += "  set_powergrid or open_project\n"
		if selected_line == "": depend_string += "  select_line\n"
		print(depend_string)
		return 1
	
	# Check simulation time
	try:
		if float(time) > 0:
			sim_time = float(time)
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for simulation time: It must be a positive real number.")
		return 1
	
	# Check timestep
	try:
		if float(step) > 0:
			time_step = float(step)
		else:
			raise ValueError
	except ValueError as e:
		print("Wrong argument for simulation timestep: It must be a positive real number.")
		return 1
	
	# Check temperature and technology 
	if technology == "":
		print(" No technology was set. Selected the default technology: Copper dual-damascene (CuDD).")
		tech = "CuDD"
	else:
		tech = technology
	
	if temperature == 0:
		print(" No temperature was set. Selected the default temperature: 378K.")
		temp = 378.0
	else:
		temp = temperature

	reduced_order = None
	if is_mor:
		# print("MOR selected")
		try:
			if int(reduced_size) > 0:
				reduced_order = int(reduced_size)
			else:
				raise ValueError
		except ValueError as e:
			print("Wrong argument for reduced size: It must be a positive integer.")
			return 1
		
	transient_worker=Transient_Class(sim_time=sim_time, timestep=time_step, directory=directory, 
				selected_line=selected_line, technology=tech, temperature=temp, width=width, NX_TOTAL = discr_size,
				mor_enabled=is_mor, reduced_order=reduced_order, IS_LINUX=IS_LINUX, INSTALLATION_FOLDER=INSTALLATION_FOLDER)
	return_message = transient_worker.transient_function()
	print(return_message)
	if "seconds" in return_message:
		history_handling.write_message_in_log(directory+ "/history_log.txt", return_message, "success")
		line_path = selected_line+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"
		output_files = os.path.normpath(directory + "/output/"+line_path)
		if is_mor:
			print(f"The simulation results can be found at {os.path.normpath(output_files+'/transient'+'/reduced')}.")
		else:
			print(f"The simulation results can be found at {os.path.normpath(output_files+'/transient'+'/original')}.")
		return 0
	else:
		history_handling.write_message_in_log(directory+ "/history_log.txt", return_message, "error")
		if(not selected_line):
			message = 'No line was selected and discretized prior to simulation.'
			print(message)
		return 1

def report_stats(filename=None):
	global directory
	
	if spice_function_cli.benchmark == "":
		depend_string = "The following dependencies are missing:\n"
		depend_string += "  set_powergrid or open_project\n"
		print(depend_string)
		return 1
	
	path_to_stastitics = directory + "/statistics/Statistics.csv"
	# print(f"Going to copy from {path_to_stastitics} to {filename}")
	list_cols = ["#layers", "#nets", "total #lines", "total #seg", "max #lines", "max #seg", "max current (A)"]
	tool_logo = "* * * PROTON Tool * * *\n"
	file_str = ""
	with open(path_to_stastitics, 'r', newline ='') as statsfile:
		all_stats = csv.reader(statsfile)
		i = 0
		for row in all_stats:	
			if ("Max" in row[0]):
				file_str += list_cols[i] + ", " + row[1] + ", " + row[2].replace('.csv', '') + "\n"
			else:
				file_str += list_cols[i] + ", " + row[1] + "\n"
			i += 1
	if filename is None:
		# Print the stats here
		print(file_str)
	else:
		try:
			with open(filename, "w") as f:
				f.write(tool_logo + file_str)
		except Exception as e:
			print("There was an error while exporting the report. Check the given path.")
			return 1
	return 0

def report_line_stress(line=None, maxstress=None, export_filename=None):
	global max_stress_loc
	if spice_function_cli.benchmark == "":
		depend_string = "The following dependencies are missing:\n"
		depend_string += "  set_powergrid or open_project\n"
		print(depend_string)
		return 1
	
	if line is None and (maxstress is None or max_stress_loc is None):
		print("No line to export was selected. Rerun the command with selecting one of the following lines:")
		for line in os.scandir(directory+"/output/"):
			if line.is_dir():
				print(f" {os.path.basename(line.path)}")
		return 1
	else:
		# Get all stress analyses for the specific line
		stress_file_pattern = r"stress_([\d.]+)\."
		# Iterate over files in the directory
		if maxstress is None or max_stress_loc is None:
			line = line.split(" - ")[0]
		else:
			line = max_stress_loc

		file_str=""
		print(f"line: {line}")
		for technology in os.listdir(directory+"/output/"+line):
			tech,temp,width = technology.split('_')
			temp = float(temp) 
			width = float(width)
			print(f'Technology: {tech}')
			print(f'Temperature: {temp}')
			print(f'Width: {width}')
			for filename in os.listdir(directory+"/output/"+line+"/"+technology):
				if filename.endswith(".txt") and filename.startswith("stress"):
					match = re.search(stress_file_pattern, filename)
					if match:
						number = float(match.group(1))
						try:
							# Write the line with sim_time in export file
							with open(directory+"/output/"+line+"/"+technology+"/"+filename, 'r') as f:
								lines = f.readlines()
								file_str+=f"* * * PROTON Tool * * *\n"
								file_str+=f"* Line analysis of line {line} at {'{:.2e}'.format(number)} sec.\n"
								file_str+=f"* Technology, {tech}\n"
								file_str+=f"* Temperature, {temp} K\n"
								file_str+=f"* Width, {width} um\n"

								i = 0
								max_stress = float(lines[0])
								local_max_stress_loc = 0
								for line1 in lines: 
									if float(line1) > max_stress:
										max_stress = float(line1)
										local_max_stress_loc = i
									i += 1
								file_str+=f"* Maximum stress, {'{:.3}'.format(max_stress)} Pa at node {local_max_stress_loc}\n"

								file_str+="* Node , Stress\n"
								i=0
								for line1 in lines:
									file_str+=str(i)+" , "+line1
									i+=1
								i=0
								file_str+="Nodes\n"
								for line1 in lines:
									file_str+=str(i)+"\n"
									i=i+1
								file_str+="Stress\n"
								for line1 in lines:
									file_str+=line1
						except ValueError as e:
							print("Corrupted stress.txt file.")
							return 1
		
		if export_filename is None:
			print(file_str)
		else:
			with open(export_filename, "w") as f:
				f.write(file_str)
			print(f"Successfully reported stress at {export_filename}.")
		return 0

def report_transient_stress(line=None, via=None, export_filename=None):
	global directory
	
	if directory == "":
		depend_string = "The following dependencies are missing:\n"
		depend_string += "  set_powergrid or open_project"
		print(depend_string)
		return 1
	
	if line is None or via is None:
		transient_lines = {}
		vias_per_line = {}
		simulated_lines_folder = directory+"/output/"
		if os.path.exists(simulated_lines_folder):
			for item in os.listdir(simulated_lines_folder):
				item_path = os.path.join(simulated_lines_folder, item)
				if os.listdir(item_path):
					for technology in os.listdir(item_path):
						technology_path = os.path.join(item_path, technology)
						if os.path.exists(os.path.join(technology_path, "transient")):
							transient_lines[item] = []
							line_w_tech = item + " - " + technology.split("_")[0] + " " + technology.split("_")[1] + " " + technology.split("_")[2]
							path_w_tech = os.path.join(technology_path, "transient")
							if os.path.exists(os.path.join(path_w_tech, "original")): 
								vias_folder = os.path.join(path_w_tech, "original")
							else:
								vias_folder = os.path.join(path_w_tech, "reduced")
							files = glob.glob(vias_folder + '/*.txt')  # Replace '*.txt' with the desired pattern
							vias = []
							for file in files:
								try:
									vias.append(int(os.path.splitext(os.path.basename(file))[0]))
								except ValueError as e:
									pass
							vias_per_line[item] = max(vias)
				for technology in os.listdir(item_path):
					technology_path = os.path.join(item_path, technology)
					if os.path.exists(os.path.join(technology_path, "transient")):
						line_w_tech = item + " - " + technology.split("_")[0] + " " + technology.split("_")[1] + " " + technology.split("_")[2]
						transient_lines[item].append((technology.split("_")[0], technology.split("_")[1], technology.split("_")[2]))
		else:
			print("No analyses have been run yet.")
			return 1

		print("No line and/or no via was selected. Select a line from the following:")
		for trans_line in transient_lines:
			print(trans_line)
		return 1

	try:
		via_num = int(via)
	except ValueError as e:
		print("Wrong argument: <via>.\nCorrect syntax: report_transient_stress <line> <via> --file <filename (op)>")
		return 1
	
	file_str = ""
	line_folder = os.path.join(directory+"/output/", line)
	if os.path.exists(line_folder):
		for technology in os.listdir(line_folder):
			technology_path = os.path.join(line_folder, technology)
			if os.path.exists(os.path.join(technology_path, "transient")):
				path_w_tech = os.path.join(technology_path, "transient")
				if os.path.exists(os.path.join(path_w_tech, "original")): 
					vias_folder = os.path.join(path_w_tech, "original")
				else:
					vias_folder = os.path.join(path_w_tech, "reduced")

				time_file=os.path.join(vias_folder, 'simulation_time.txt')
				stress_tran_file=os.path.join(vias_folder, f'{via_num}.txt') 

				try:
					with open(time_file) as t_f:
						t_lines = t_f.readlines()
				except ValueError as e:
					print("Corrupted simulation_time file.")
				try:
					with open(stress_tran_file) as s_f:
						s_lines = s_f.readlines()
				except ValueError as e:
					print("Corrupted stress.txt file.")
					
				file_str+=f"* * * PROTON Tool * * *\n"
				file_str+=f"* Transient analysis of line {line} at {'{:.2e}'.format(float(t_lines[-1]))} sec with timestep {'{:.2e}'.format(float(t_lines[1]))} sec.\n"
				file_str+=f"* Technology, {technology.split('_')[0]}\n"
				file_str+=f"* Temperature, {technology.split('_')[1]} K\n"
				file_str+=f"* Width, {technology.split('_')[2]} um\n"
				file_str+="* Time , Stress\n"
				for line1,line2 in zip(t_lines,s_lines):
					line1=line1.strip()
					line2=line2.strip()
					file_str+=line1+" , "+line2+"\n"
			
	else:
		print("No analyses have been run for the selected line.")
		return 1

	# Write here the file or print in output stream
	if export_filename is None:
		print(file_str)
	else:
		with open(export_filename, "w") as f:
			f.write(file_str)
		print(f"Successfully reported stress at {export_filename}.")
	return 0

def analyze_line_item(item_path, exiting, problematic_lines, problematic_lines_lock, simulation_time, tech, temp, critical_stress):
	item = os.path.splitext(os.path.basename(item_path))[0]
	# print(f"Going to open: {item_path}", end='\t')
	# print(indent + os.path.splitext(item)[0])
	# time.sleep(0.01)
	
	with open(item_path, 'r') as csv_file:
		lines = csv_file.readlines()
	lengths = []
	for line in lines:
		if line[0] == 'R':
			line_components = line.split(',')
			lengths.append(float(line_components[3]))
	min_length = min(lengths)
	
	if len(lengths) < 150:
		discr_times = 0
		while discr_times < 10:
			# print(f"min_length: {min_length}")
			# time.sleep(2)
			set_discr_step(min_length*0.99, True)
			matrix_formulation_worker = Matrix_Formulation_Class(csv_file=item_path,project_location=directory,sp_step=disc_step,given_disc_point=None,technology=tech,temperature=float(temp),givenWidth=float(width))
			return_message = matrix_formulation_worker.matrix_formulation()

			if "seconds" in return_message:
				break
			else:
				print(f"Going to reduce min_length to: {min_length}")
				min_length = min_length * 0.7
				if min_length <= 0:
					print("Discretization cannot be more sparse.")
					break
			discr_times += 1

		if discr_times < 10 or min_length > 0:
			# Perform analytical for the selected line
			# select_line(os.path.splitext(item)[0], True)

			if exiting.is_set():
				return 1
			if analytical(simulation_time, True, os.path.splitext(item)[0]) == 0:
				if exiting.is_set():
					return 1
				if critical_stress is not None:
					#  Get results, check if ok, else store it in the problematic_lines
					line_path = os.path.splitext(item)[0]+"/"+tech+"_"+str(temp)+"_"+str(width)+"/"
					output_files = os.path.normpath(directory + "/output/"+line_path)

					stress_file_pattern = r"stress_([\d.]+)\."
					lines = []
					
					for filename in os.listdir(output_files):
						if filename.endswith(".txt") and filename.startswith("stress"):
							match = re.search(stress_file_pattern, filename)
							if match:
								number = float(match.group(1))
								# print(f'Going to check: {number} with {simulation_time}')
								if float(number) == float(simulation_time):
									# print("Got in here!")
									with open(os.path.join(output_files, filename), 'r') as f_stress:
										lines = f_stress.readlines()
					
					# print(f"len(lines): {len(lines)}")
					if len(lines) == 0:
						print("The file is empty!")
						return 1
					
					max_stress = float(lines[0])
					for l in lines:
						if float(l) > max_stress:
							max_stress = float(l)
					
					if max_stress > critical_stress:
						# Acquire the lock before modifying the shared dictionary
						with problematic_lines_lock:
							problematic_lines[os.path.splitext(item)[0]] = max_stress
			else:
				# The line could not be analyzed
				print(f"{os.path.splitext(item)[0]} The line could not be analyzed")
				pass
		else:
			print(f"{os.path.splitext(item)[0]} The line was discarded")
			pass
	else:
		pass
		# print(f"Going to discard this large line: {len(lengths)}")

max_stress_loc = None
def analyze(simulation_time, critical_stress=None, sample_lines=None):
	global selected_line, width, technology, temperature, max_stress_loc
	if spice_function_cli.benchmark == "" or width == 0:
		depend_string = "The following dependencies are missing:\n"
		if spice_function_cli.benchmark == "": 
			depend_string += "  set_powergrid or open_project\n"
		if width == 0: 
			depend_string += "  set_line_width\n"
		print(depend_string)
		return 1
	
	# Check time that is number
	try:
		sim_time = float(simulation_time)
	except ValueError as e:
		print("Invalid argument: simulation time.\nCorrect syntax: analyze <time> <critical stress (op)>") 
		return 1
	
	# Check critical that is number
	if critical_stress is not None:
		try:
			crit_stress = float(critical_stress)
		except ValueError as e:
			print("Invalid argument: critical stress.\nCorrect syntax: analyze <time> <critical stress (op)>") 
			return 1
	else:
		crit_stress = None
	
	# Get the technology, temperature and width 
	if technology == "":
		print(" No technology was set. Selected the default technology: Copper dual-damascene (CuDD).")
		tech = "CuDD"
	else:
		tech = technology
	
	if temperature == 0:
		print(" No temperature was set. Selected the default temperature: 378K.")
		temp = 378.0
	else:
		temp = temperature

	# Get all lines
	print(spice_function_cli.benchmark)
	# print_folder_contents(spice_function_cli.benchmark)

	stack = [(spice_function_cli.benchmark, "")]
	
	# Get the total number of lines
	lines_num = get_num_lines(spice_function_cli.benchmark)

	start_time = time.time()
	# successful_lines = 0

	all_lines = []
	while stack:
		current_path, indent = stack.pop(0)

		sorted_files = sorted(os.listdir(current_path), key=extract_numbers)
		
		for item in sorted_files:
			# analyze_line_item(item)
			item_path = os.path.join(current_path, item)
			if os.path.isdir(item_path):
				stack.append((item_path, indent + "  "))
				continue
			elif os.path.isfile(item_path):
				all_lines.append(item_path)

	if sample_lines is not None:
		_sample_lines = int(sample_lines)
		all_lines = random.sample(all_lines, _sample_lines)
		lines_num = _sample_lines

	print(f"Total number of lines: {lines_num}")
	progress_bar = tqdm(total=lines_num, unit=' line')

	problematic_lines = {}  # Global shared dictionary
	problematic_lines_lock = Lock()  # Lock for synchronizing access to the dictionary

	exiting = threading.Event()
	def signal_handler(signum, frame):
		print("Setting exiting event")
		exiting.set()
	signal.signal(signal.SIGTERM, signal_handler)
	
	partial_analyze_line_item  = partial(analyze_line_item, exiting=exiting, problematic_lines=problematic_lines, problematic_lines_lock=problematic_lines_lock, simulation_time=simulation_time, tech=tech, temp=temp, critical_stress=crit_stress)
	
	# with concurrent.futures.ThreadPoolExecutor() as executor:
	# 	# Use the map() method to apply the process_item function to each item
	# 	for _ in executor.map(partial_analyze_line_item, all_lines):
	# 		progress_bar.update(1)

	# for item in all_lines:
	# 	analyze_line_item(item, problematic_lines, problematic_lines_lock, simulation_time, tech, temp, crit_stress)
	# 	progress_bar.update(1)

	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = []
		for item in all_lines:
			future = executor.submit(partial_analyze_line_item, item)
			future.add_done_callback(lambda _: progress_bar.update(1))
			futures.append(future)
		# Wait for all futures to complete
		concurrent.futures.wait(futures)
		# try:
		# 	while not exiting.is_set():
		# 		time.sleep(0.1)
		# 		print('waiting')
		# except KeyboardInterrupt:
		# 	print('Caught keyboardinterrupt')
		# 	exiting.set()

	end_time = time.time()
	progress_bar.close()

	# TO-DO: Write the analysis in a separate folder for the whole powergrid
	print(f"Powergrid analysis has finished in {end_time-start_time:.2f} seconds.")
	print(f"The results can be found at: {os.path.join(directory, 'output')}")
	
	if critical_stress is not None:
		print(f"Failed lines: {len(list(problematic_lines))}/{lines_num}.")
		# print(f"Max stress has been exceeded at lines:")
		max_stress = None
		max_stress_loc = None
		with problematic_lines_lock:
			for failed_line in problematic_lines:
				if max_stress is None:
					max_stress = problematic_lines[failed_line]
					max_stress_loc = failed_line
				elif problematic_lines[failed_line] > max_stress:
					max_stress = problematic_lines[failed_line]
					max_stress_loc = failed_line
				# print(failed_line, end=" ")
		# print()

		print(f"Maximum stress found at line {max_stress_loc} with value {max_stress:.2f} Pa.") 
	return 0
		
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def source(filename):
	with open(filename, 'r') as commands_file:
		for line in commands_file:
			if line != "":
				return_value = process_command(line)
				if return_value == 1:
					return 1

def help():
	print()
	print(PROTON_STRING)
	print()

	table = PrettyTable()
	table.field_names = ["Command", "Dependencies", "Description"]
	table.align["Description"] = "l"
	table.valign["Command"] = "m"
	table.valign["Dependencies"] = "m"
	table.valign["Description"] = "m"
	table.max_width = int(shutil.get_terminal_size((80,20))[0]/3)-5
	table.hrules=ALL
	# table.border = True
	for command in commands:
		table.add_row([command+commands[command][0], commands[command][1], commands[command][2]])
	print(table)

# Set up autocomplete using the list of commands
def autocomplete(text, state):
	options = [command for command in commands if command.startswith(text)]
	if state < len(options):
		return options[state]
	else:
		return None
	
# Define a custom argument parser class
class CustomArgumentParser(argparse.ArgumentParser):
	# def __init__(self, prog: str | None = None, usage: str | None = None, invalid_syntax_error: str | None = None, description: str | None = None, epilog: str | None = None, parents: Sequence[ArgumentParser] = ..., formatter_class: HelpFormatter = ..., prefix_chars: str = "-", fromfile_prefix_chars: str | None = None, argument_default: Any = None, conflict_handler: str = "error", add_help: bool = True, allow_abbrev: bool = True, exit_on_error: bool = True) -> None:
	# 	self.invalid_syntax_error = invalid_syntax_error
	# def __init__(self, prog: str | None = None, usage: str | None = None, invalid_syntax_error: str | None = None,description: str | None = None, epilog: str | None = None, parents: Sequence[ArgumentParser] = ..., formatter_class: _FormatterClass = ..., prefix_chars: str = "-", fromfile_prefix_chars: str | None = None, argument_default: Any = None, conflict_handler: str = "error", add_help: bool = True, allow_abbrev: bool = True, exit_on_error: bool = True) -> None:
	# def __init__(self, invalid_syntax_error, *args, **kwargs):
	# 	self.invalid_syntax_error = invalid_syntax_error
	# 	super().__init__(*args, **kwargs)
	def error(self, message):
		pass
		# # Custom error message for missing mandatory argument
		# if 'the following arguments are required: time' in message:
		# 	print(f'{self.description}: Missing mandatory time argument')
		# 	print(self.invalid_syntax_error)
		# else:
		# 	# Print other error messages as-is
		# 	print(f'{self.description}: {message}')
		# 	print(self.invalid_syntax_error)
		
def process_command(command):
	words = command.split()
	
	if not words or words[0][0] == "#": return 0

	if words[0].lower() not in commands and words[0].lower() != "g" and \
		words[0].lower() != "help" and words[0].lower() != "h" and \
		words[0].lower() != "quit" and words[0].lower() != "q":
		print(f"{words[0]}: Unknown command")
		return 1
	
	if words[0].lower() == "help" or words[0].lower() == "h":
		help()
	elif words[0].lower() == "quit" or words[0].lower() == "q":
		exit(0)
	elif words[0].lower() == "gui" or words[0].lower() == "g":
		gui()
	elif words[0].lower() == "source" or words[0].lower() == "s":
		if len(words) == 1:
			print("Argument missing: commands file.\nCorrect syntax: source <commands filename>.")
			return 1
		if not os.path.exists(words[1]):
			print(f"Wrong argument: {words[1]} does not exist.")
			return 1
		return source(words[1])
	elif words[0].lower() == "set_powergrid":
		if len(words) == 1:
			print("Argument missing: SPICE powergrid file.\nCorrect syntax: set_powergrid <SPICE powergrid file>.")
			return 1
		if not words[1].endswith(".spice"):
			print(f"Wrong argument: {words[1]} needs to be a SPICE file.")
			return 1
		if not os.path.exists(words[1]):
			print(f"Wrong argument: {words[1]} does not exist.")
			return 1
		set_powergrid(words[1])
	elif words[0].lower() == "set_project_path":
		if len(words) == 1:
			print("Argument missing: project path.\nCorrect syntax: set_project_path <project path>.")
			return 1
		# if os.path.exists(words[1]):
		#	 print(f"Wrong argument: path {words[1]} already exists.")
		#	 return
		set_project_path(words[1])
	elif words[0].lower() == "set_project_name":
		if len(words) == 1:
			print("Argument missing: project name.\nCorrect syntax: set_project_path <project name>.")
			return 1
		return set_project_name(words[1])
	elif words[0].lower() == "parse_powergrid":
		parser = CustomArgumentParser(description='parse_powergrid')
		parser.add_argument('-y', '--yes', action=argparse.BooleanOptionalAction, help='yes argument')
		parser.add_argument('-n', '--no', action=argparse.BooleanOptionalAction, help='yes argument')

		parsed_args, unknown_args = parser.parse_known_args(words[1:])
		response = None 
		if parsed_args.yes is not None:
			response = 'y'
		elif parsed_args.no is not None:
			response = 'n'
		return parse_powergrid(response)
	elif words[0].lower() == "open_project":
		parser = CustomArgumentParser(description='open_project')
		parser.add_argument('project_path', help='mandatory project_path argument')
		parser.add_argument('-y', '--yes', action=argparse.BooleanOptionalAction, help='yes argument')
		parser.add_argument('-n', '--no', action=argparse.BooleanOptionalAction, help='yes argument')

		parsed_args, unknown_args = parser.parse_known_args(words[1:])
		if parsed_args.project_path is None:
			print("Argument missing: project path.\nCorrect syntax: open_project <project path>.")
			return 1
		if not os.path.exists(parsed_args.project_path):
			print(f"Wrong argument: path {parsed_args.project_path} does not exist.")
			return 1
		
		response = None 
		if parsed_args.yes is not None:
			response = 'y'
		elif parsed_args.no is not None:
			response = 'n'
		return open_project(parsed_args.project_path, response)
	elif words[0].lower() == "show_lines":
		return(show_lines(None) if len(words) == 1 else show_lines(words[1]))
	elif words[0].lower() == "select_line":
		if len(words) == 1:
			print("Argument missing: selected line.\nCorrect syntax: select_line <line>.")
			return 1
		return select_line(words[1])
	elif words[0].lower() == "set_technology":
		if len(words) == 1:
			print("Argument missing: selected technology.\nCorrect syntax: set_technology <technology>.")
			return 1
		return set_technology(words[1])
	elif words[0].lower() == "set_temperature":
		if len(words) == 1:
			print("Argument missing: selected temperature.\nCorrect syntax: set_temperature <temperature>.")
			return 1
		return set_temperature(words[1])
	elif words[0].lower() == "set_line_width":
		if len(words) == 1:
			print("Argument missing: selected line width.\nCorrect syntax: set_line_width <width (um)>.")
			return 1
		return set_line_width(words[1])
	elif words[0].lower() == "set_discr_points":
		if len(words) == 1:
			print("Argument missing: selected discretization points.\nCorrect syntax: set_discr_points <num. of points>.")
			return 1
		return set_discr_points(words[1])
	elif words[0].lower() == "set_discr_step":
		if len(words) == 1:
			print("Argument missing: selected discretization step.\nCorrect syntax: set_discr_step <discretization step (um)>.")
			return 1
		return set_discr_step(words[1])
	elif words[0].lower() == "discretize_line":
		if len(words) == 1:
			# Check that commands set_disc_points/set_disc_step have been executed
			discr_line()
		elif len(words) == 3:
			# Check that --step <step> or --points <points> are there
			if words[1] == "--step":
				# Check step
				if set_discr_step(words[2]) == 0:
					discr_line("step")
				# else:
				# 	print("Invalid argument: discretization step. It should be a positive real number.")
			elif words[1] == "--points":
				if set_discr_points(words[2]) == 0:
					discr_line("points")
				# else:
				# 	print("Invalid argument: discretization points. It should be a positive integer.")
			else:
				print("Invalid arguments for discretize_line command.\nCorrect syntax:\n discretize_line (if commands set_disc_points or set_disc_step have been executed)\n discretize_line --step <discretization step (um)>\n discretize_line --points <num. of discretization points>.")
				return 1
		else:
			print("Invalid arguments for discretize_line command.\nCorrect syntax:\n discretize_line (if commands set_disc_points or set_disc_step have been executed)\n discretize_line --step <discretization step (um)>\n discretize_line --points <num. of discretization points>.")
			return 1
	elif words[0].lower() == "analyze_line":
		if len(words) == 1:
			print("Argument missing: execution time.\nCorrect syntax: analyze_line <time> <timestep (op)> <reduced_size (op)>.")
			return 1
		elif len(words) == 2:
			return analytical(words[1])
		elif len(words) == 3:
			return numerical(False, words[1], words[2])
		elif len(words) == 4:
			return numerical(True, words[1], words[2], words[3])
	elif words[0].lower() == "report_powergrid_stats":
		if len(words) == 1:
			return report_stats()
		elif len(words) == 3 and words[1] == "--file":
			return report_stats(words[2])
		else:
			print("Wrong arguments: --file.\nCorrect syntax: report_powergrid_stats --file <filename> (optional)")
			return 1
	elif words[0].lower() == "report_line_stress":
		parser = CustomArgumentParser(description='report_line_stress')
		parser.add_argument('line', help='line argument')
		parser.add_argument('--maxstress', action=argparse.BooleanOptionalAction, help='maxstress argument')
		parser.add_argument('--file', help='file argument')

		parsed_args, unknown_args = parser.parse_known_args(words[1:])
		return report_line_stress(parsed_args.line, parsed_args.maxstress, parsed_args.file)

		# if len(words) == 1:
		# 	return report_line_stress()
		# elif len(words) == 2:
		# 	if words[1] == "--file":
		# 		print("Argument missing: filename.\nCorrect syntax: report_line_stress <line (op)> --file <filename (op)>")
		# 		return 1
		# 	return report_line_stress(words[1])
		# elif len(words) == 3:
		# 	if words[1] != "--file":
		# 		print("Argument missing: filename.\nCorrect syntax: report_line_stress <line (op)> --file <filename (op)>")
		# 		return 1
		# 	else:
		# 		return report_line_stress(None, words[2])
		# elif len(words) == 4:
		# 	if words[2] != "--file":
		# 		print("Wrong argument: filename.\nCorrect syntax: report_line_stress <line (op)> --file <filename (op)>")
		# 	else:
		# 		return report_line_stress(words[1], words[3])
		# else:
		# 	print("Invalid syntax for report_line_stress.\nCorrect syntax: report_line_stress <line> --file <filename (op)>")
		# 	return 1
	elif words[0].lower() == "report_transient_stress":
		if len(words) == 1:
			return report_transient_stress()
		elif len(words) == 3:
			if words[1] == "--file":
				print("Arguments missing: <line> and <via>.\nCorrect syntax: report_transient_stress <line> <via> --file <filename (op)>")
				return 1
			return report_transient_stress(words[1], words[2])
		elif len(words) == 5:
			if words[3] == "--file":
				return report_transient_stress(words[1], words[2], words[4])
			else:
				print("Argument missing: filename.\nCorrect syntax: report_transient_stress <line> <via> --file <filename (op)>")
				return 1
		else:
			print("Invalid syntax for report_transient_stress.\nCorrect syntax: report_transient_stress <line> <via> --file <filename (op)>")
			return 1
	elif words[0].lower() == "analyze":
		parser = CustomArgumentParser(description='analyze')
		parser.add_argument('time', type=float, help='mandatory time argument')
		parser.add_argument('--critical', type=float, help='optional critical stress argument')
		parser.add_argument('--sample', type=int, help='optional sample argument')

		parsed_args, unknown_args = parser.parse_known_args(words[1:])
		if parsed_args.time is None:
			print('Invalid syntax for analyze.\nCorrect syntax: analyze <time> <critical stress (op)> <sample lines (op)>')
			return 1
		
		# # Handle unknown arguments
		# if unknown_args:
		# 	print('Discarding the unknown arguments:', ' '.join(unknown_args))
		
		return analyze(parsed_args.time, parsed_args.critical, parsed_args.sample)
	else:
		print(f"{words[0]}: Unknown command")
		print("Should never reach this!!")
		return 1
	return 0
	

def shell():
	while True:
		try:
			user_input = input(">$ (PROTON) ")
		except KeyboardInterrupt as e:
			break
		if user_input.lower() == "quit" or user_input.lower() == "q" or user_input.lower() == "exit":
			print("Exiting the shell...")
			break
		if user_input != "":
			try:
				process_command(user_input)
			except KeyboardInterrupt as e:
				print()

if __name__ == "__main__":
	
	try:
		print(PROTON_STRING + " v1.0")
	except UnicodeEncodeError as e:
		print(PROTON_UNICODE_STRING + " v1.0")
		
	print("\nUniversity of Thessaly, Greece")

	# if not os.path.exists('installation_folder.txt'):
	# 	print('PROTON has not been installed yet on this system.')
	# 	exit(1)

	args = sys.argv[1:]
	if args:
		# File to source was given
		if os.path.exists(args[0]):
			if os.path.isfile(args[0]):
				source(args[0])
			else:
				print(f"Could not open {args[0]} as it is a folder.")
		else:
			print(f"File {args[0]} does not exist.")
	else:
		shell()
