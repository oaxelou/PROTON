import subprocess
import sys
import os
import json
import csv
import time
import re
import shutil
from sys import platform

from history_handling import *

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QThread
from PyQt5 import QtGui
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtGui import QPalette, QColor, QMovie, QIcon

from EM_tool_plots import *
import EM_tool_plots
import spice_function
# import matrix_formulation_func
from matrix_formulation_func import Matrix_Formulation_Class
from analytical_class import Analytical_Class
from transient_class import Transient_Class

# The following flag is going to be set to True 
# only when one runs the code on Linux
# if platform == "linux" or platform == "linux2":
#     # linux
# elif platform == "darwin":
#     # OS X

INSTALLATION_FOLDER = ""

if platform == "win32":
    # print('Windows!')
    IS_LINUX = False
else:
	# print('Linux!')
	IS_LINUX = True

DELETE_OLD_DISCR_FLAG = False
MAIN_WINDOW_FLAG = False
GRID_ON = True
MIN_MAIN_WINDOW_SIZE = (1100,800)
LEFT_FRAME_WIDTH = 300
RIGHT_FRAME_WIDTH = 1000

PLOT_DELAY = 1
PLOTS_LABEL_PIXEL_MARGIN = 0

SELECTED_LINE = ""
TECHNOLOGY = ""
TEMPERATURE = 0
WIDTH = 0
DISCR_SIZE = 0

FILE_FORMAT = ".csv"
PROJECT_NAME = ""
POWERGRID_LOCATION = "kati"
directory=""
spice_file=""

NUM_OF_VIAS = 21

matrix_formulation_worker = None
matrix_formulation_thread = None

analytical_worker = None
analytical_thread = None

transient_worker = None
transient_thread = None

window = None
powergrid_tree = None

right_frame_v_splitter = None
#global json_data_sim
#global PROTON_history_list 

json_data_sim = {}
PROTON_history_list = []


# GENERAL
def add_line(form_layout):
	line_layout = QVBoxLayout()
	line_spacer_top = QSpacerItem(1,4, QSizePolicy.Minimum, QSizePolicy.Expanding)
	line_layout.addItem(line_spacer_top)
	line = QFrame()
	line.setFrameShape(QFrame.HLine)
	# line.setLineWidth(2)
	line.setStyleSheet("color: #888888")
	line_layout.addWidget(line)
	line_spacer_bottom = QSpacerItem(1,4, QSizePolicy.Minimum, QSizePolicy.Expanding)
	line_layout.addItem(line_spacer_bottom)
	form_layout.addRow(line_layout)

def add_space(form_layout, space_value):
	spacer = QSpacerItem(1,space_value, QSizePolicy.Minimum, QSizePolicy.Expanding)
	form_layout.addItem(spacer)

def remove_children(widget):
	for child in widget.children():
		if isinstance(child, QLayout):
			child.removeItem(child)
			child.deleteLater()
		else:
			child.deleteLater()

def create_label_text(label, label_text, label_style, alignment=None):
	label.setText(label_text)
	label.setStyleSheet(label_style)

	if alignment:
		label.setAlignment(alignment)

def generate_popup_message(text, label, isQuestion=False):
	message_dialog = QMessageBox()
	icon = QtGui.QIcon(os.path.join(INSTALLATION_FOLDER, "media/proton_logo.png"))
	message_dialog.setWindowIcon(icon)
	
	if(label == "warning"):
		message_dialog.setIcon(QMessageBox.Warning)
		message_dialog.setWindowTitle("Warning")
	elif (label == "error"):
		message_dialog.setIcon(QMessageBox.Critical)
		message_dialog.setWindowTitle("Error")
	elif (label == "info"):
		message_dialog.setIcon(QMessageBox.Information)
		message_dialog.setWindowTitle("Information")
	
	message_dialog.setText(text)
	if isQuestion:
		message_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
	else:
		message_dialog.setStandardButtons(QMessageBox.Ok)
	button_clicked = message_dialog.exec_()

	if button_clicked == QMessageBox.Yes:
		return True
	else:
		return False


def save_project_details(project_name, project_path, spice_path, benchmark):
	temp_dictionary = {
		"magic_word": "papaya56",
		"project_name": project_name,
		"project_path": project_path,
		"full_path_to_project": project_path+ "/" + project_name,
		"spice_path": spice_path,
		"parsed_spice_path": benchmark
	}

	project_details_json = json.dumps(temp_dictionary, indent = 4)
	temp_path = project_path+ "/" + project_name + "/" + "PROTON_project_details.json"
	with open(temp_path, "w") as fd:
		fd.write(project_details_json)

def save_config_file(save, given_directory=None):
	global SELECTED_LINE, directory
	if given_directory is None:
		given_directory = directory
	full_path = given_directory + "/config.json"

	if save:
		dictionary_json = json.dumps(json_data_sim, indent = 4)
		with open(full_path, "w") as fd:
			fd.write(dictionary_json)
	else:
		#save default values for the window to open
		#full_path
		temp_dict1 = {"technology": "CuDD", "temperature": 0, "width": 0}
		temp_dict2 = {"parameter": "points","points": 0, "step": 0}
		temp_dict3 = {"selected_line" : ""}
		dictionary = {"line": temp_dict1, "discretization": temp_dict2, "workspace_details": temp_dict3}
		dictionary_json = json.dumps(dictionary, indent = 4)
		with open(full_path, "w") as fd:
			fd.write(dictionary_json)


	return



def browse_location(dialog, project_location_entry):
	global directory
	options = QFileDialog.Options()
	options |= QFileDialog.ReadOnly
	temp_directory = QFileDialog.getExistingDirectory(dialog, "Select Project Location", options=options)
	if temp_directory:
		directory = temp_directory
		project_location_entry.setText(directory)


def browse_spice(dialog, spice_file_entry):
	global spice_file
	options = QFileDialog.Options()
	options |= QFileDialog.ReadOnly
	temp_spice_file, _ = QFileDialog.getOpenFileName(dialog, "Select Spice File", "", "SPICE Files (*.spice);;All Files (*)", options=options)
	if temp_spice_file[-6:] == ".spice":
		spice_file = temp_spice_file
		spice_file_entry.setText(spice_file)


def browse_config(dialog, config_file_entry):
		options = QFileDialog.Options()
		options |= QFileDialog.ReadOnly
		file_name, _ = QFileDialog.getOpenFileName(dialog, "Select Configuration File", "", "All Files (*);;Text Files (*.txt)", options=options)
		if file_name:
			config_file_entry.setText(file_name)

#-----------------------------------------------------------------------------------------------------------------------------------------------------	
# TOOLBAR DEFS

def on_save_action():
	# log_keeper.track_history_messages("Saving project.", True)
	
	save_config_file(True)
	log_keeper.track_history_messages("The project has been successfully saved.", False)

def exit_app(window):
	result = QMessageBox.question(window, ' ', "Are you sure you want to exit?", 
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
	if result == QMessageBox.Yes:
		log_keeper.save_history_log(True)
		sys.exit()
	else:
		return


	

#--------------------------------------------------------------------------------------------------------------------------------------
# EXPORT DATA
def update_columns_to_export(index, lines_label, analytical_lines_dropdown,transient_lines_dropdown, points_label, points_dropdown, columns_layout,system_label,system_layout,done_button):
	widgets_count = [7,2,2]
	for i in range(columns_layout.count()):
		columns_layout.itemAt(i).widget().setVisible(False)
		lines_label[0].setVisible(False)
		lines_label[1].setVisible(False)
		analytical_lines_dropdown.setVisible(False)
		transient_lines_dropdown.setVisible(False)
		points_label.setVisible(False)
		points_dropdown.setVisible(False)
	#the mor radio button	
	system_label.setVisible(False)
	system_layout.itemAt(0).widget().setVisible(False)
	system_layout.itemAt(1).widget().setVisible(False)
	if index == 0:
		for j in range(widgets_count[0]):
			columns_layout.itemAt(j).widget().setVisible(True)
		done_button.setEnabled(True)
	elif index == 1:
		lines_label[0].setVisible(True)
		analytical_lines_dropdown.setVisible(True)
		columns_layout.itemAt(7).widget().setVisible(True)
		columns_layout.itemAt(8).widget().setVisible(True)
		if analytical_lines_dropdown.count() == 0:
			done_button.setEnabled(False)
		else:
			done_button.setEnabled(True)
	elif index == 2:
		lines_label[1].setVisible(True)
		transient_lines_dropdown.setVisible(True)
		points_label.setVisible(True)
		points_dropdown.setVisible(True)
		columns_layout.itemAt(9).widget().setVisible(True)
		columns_layout.itemAt(10).widget().setVisible(True)
		system_label.setVisible(True)
		# system_layout.itemAt(0).widget().setChecked(False)
		# system_layout.itemAt(1).widget().setChecked(False)
		# system_layout.itemAt(0).widget().setEnabled(False)
		# system_layout.itemAt(1).widget().setEnabled(False)
		transient_lines_dropdown.currentIndexChanged.connect(lambda:transient_dropdown_changes(system_layout,transient_lines_dropdown.currentText()))
		system_layout.itemAt(0).widget().setVisible(True)
		system_layout.itemAt(1).widget().setVisible(True)
		if transient_lines_dropdown.count() == 0:
			done_button.setEnabled(False)
		else:
			done_button.setEnabled(True)


def transient_dropdown_changes(system_layout,line_w_tech):
	global directory

	print(f'line_w_tech: {line_w_tech}')

	line = line_w_tech.split(" - ")[0]
	tech, temp, width = line_w_tech.split(" - ")[1].split()

	line_folder=directory+"/output/"+line+"/"+tech+"_"+temp+"_"+width

	print(f'line_folder: {line_folder}')
	# for technology in os.listdir(line_folder):
	# 	technology_path=os.path.join(line_folder,technology)
	if os.path.exists(line_folder+"/transient/"+"original") and os.path.exists(line_folder+"/transient/"+"reduced"):
		print('both')
		system_layout.itemAt(0).widget().setEnabled(True)
		system_layout.itemAt(1).widget().setChecked(True)
		system_layout.itemAt(0).widget().setEnabled(True)
	elif os.path.exists(line_folder+"/transient/"+"original"):
		print('original')
		system_layout.itemAt(0).widget().setEnabled(True)
		system_layout.itemAt(0).widget().setChecked(True)
		system_layout.itemAt(1).widget().setEnabled(False)
	elif os.path.exists(line_folder+"/transient/"+"reduced"):
		print('reduced')
		system_layout.itemAt(1).widget().setEnabled(True)
		system_layout.itemAt(1).widget().setChecked(True)
		system_layout.itemAt(0).widget().setEnabled(False)
	else:
		print('Got in else!')
	
def browse_export(parent, export_file_entry):
	global FILE_FORMAT
	options = QFileDialog.Options()
	options |= QFileDialog.ReadOnly
	file_name, _ = QFileDialog.getSaveFileName(parent, "Save file", "", f"{FILE_FORMAT} Files (*{FILE_FORMAT});;All Files (*)", options=options)
	
	if not file_name.endswith(FILE_FORMAT):
		file_name = file_name + FILE_FORMAT
	if file_name:
		export_file_entry.setText(file_name)

def set_file_format(fmt):
	global FILE_FORMAT
	FILE_FORMAT = fmt

def export_data(window):
	global directory
	
	export_dialog = QDialog()
	export_dialog.setWindowTitle("Export Data")
	icon = QtGui.QIcon(os.path.join(INSTALLATION_FOLDER, "media/proton_logo.png"))
	export_dialog.setWindowIcon(icon)
	form_layout = QFormLayout(export_dialog)
	
	# Add a title to the form
	title_layout = QHBoxLayout()
	title_label = QLabel("<h3>Export Data</h3>")
	title_label.setTextFormat(Qt.RichText)
	title_layout.addWidget(title_label)
	title_layout.setAlignment(Qt.AlignHCenter)
	form_layout.addRow(title_layout)

	add_space(form_layout, 3)

	button_group_file=QButtonGroup() #we need to group radio buttons in 2 categories in order to check 2 buttons
	button_group_system=QButtonGroup()

	file_format_label = QLabel("File format:")
	csv_radio = QRadioButton(".csv")
	csv_radio.setChecked(True)
	txt_radio = QRadioButton(".txt")
	button_group_file.addButton(csv_radio)
	button_group_file.addButton(txt_radio)
	# txt_radio.setChecked(False)
	file_format_layout = QHBoxLayout()
	file_format_layout.addWidget(csv_radio)
	file_format_layout.addWidget(txt_radio)
	form_layout.addRow(file_format_label, file_format_layout)

	csv_radio.clicked.connect(lambda: set_file_format('.csv'))
	txt_radio.clicked.connect(lambda: set_file_format('.txt'))

	# Add export data dropdown
	export_data_label = QLabel("Data to export:")
	export_data_dropdown = QComboBox()
	export_data_dropdown.addItems(["General statistics of the power grid", 
								  "EM stress analysis results on selected line", 
								  "EM Transient stress evolution on selected node"])
	form_layout.addRow(export_data_label, export_data_dropdown)

	# Line to export
	# Find all the available simulated lines 
	simulated_lines_folder = os.path.join(directory,"output")

	lines = []
	transient_lines = []
	analytical_lines = []
	if os.path.exists(simulated_lines_folder):
		for item in os.listdir(simulated_lines_folder):
			item_path = os.path.join(simulated_lines_folder, item)
			
			stress_pattern = r"stress_([\d.]+)\."
			for technology in os.listdir(item_path):
				match = None
				for filename in os.listdir(os.path.join(item_path,technology)):
					if filename.endswith(".txt") and filename.startswith("stress"):
						match = re.search(stress_pattern, filename)
						if match:
							analytical_lines.append(item)
							break
				if match:
					break
			print(f"Going to check if {item_path+'/transient/'} exists.")
			for technology in os.listdir(item_path):
				technology_path = os.path.join(item_path, technology)
				print(f'Path to check:{os.path.join(technology_path, "transient")}')
				if os.path.exists(os.path.join(technology_path, "transient")):
					line_w_tech = item + " - " + technology.split("_")[0] + " " + technology.split("_")[1] + " " + technology.split("_")[2]
					transient_lines.append(line_w_tech)
			if os.path.isdir(item_path):
				lines.append(item)
	print(f"Simulated lines: {lines}")
	print(f"analytical lines: {analytical_lines}")
	print(f"transient lines: {transient_lines}")

	# Add columns to export checkboxes
	columns_to_export_label = QLabel("Columns to export:")
	columns_to_export_layout = QVBoxLayout()
	form_layout.addRow(columns_to_export_label, columns_to_export_layout)
	
	# 1. General statistics of the power grid (5)
	number_of_layers_checkbox = QCheckBox("Number of layers", checked=True, visible=False)
	number_of_nets_checkbox = QCheckBox("Number of nets", checked=True, visible=False)
	number_of_lines_checkbox = QCheckBox("Number of lines", checked=True, visible=False)
	number_of_segments_checkbox = QCheckBox("Number of segments", checked=True, visible=False)
	max_lines_checkbox = QCheckBox("Max number of lines per net", checked=True, visible=False)
	max_seg_checkbox = QCheckBox("Max number of segments per line", checked=True, visible=False)
	max_current_checkbox = QCheckBox("Max current", checked=True, visible=False)

	# 2. EM stress analysis results on selected line (2) + 1
	
	node_checkbox = QCheckBox("Node", checked=True, visible=False)
	spatial_stress_checkbox = QCheckBox("Stress", checked=True, visible=False)

	# 3. EM Transient stress evolution on selected node (2) + 2
	time_checkbox = QCheckBox("Time", checked=True, visible=False)
	temporal_stress_checkbox = QCheckBox("Stress", checked=True, visible=False)

	columns_to_export_layout.addWidget(number_of_layers_checkbox)
	columns_to_export_layout.addWidget(number_of_nets_checkbox)
	columns_to_export_layout.addWidget(number_of_lines_checkbox)
	columns_to_export_layout.addWidget(number_of_segments_checkbox)
	columns_to_export_layout.addWidget(max_lines_checkbox)
	columns_to_export_layout.addWidget(max_seg_checkbox)
	columns_to_export_layout.addWidget(max_current_checkbox)

	columns_to_export_layout.addWidget(node_checkbox)
	columns_to_export_layout.addWidget(spatial_stress_checkbox)

	columns_to_export_layout.addWidget(time_checkbox)
	columns_to_export_layout.addWidget(temporal_stress_checkbox)

	# for i in range(columns_to_export_layout.count()):
	# 	columns_to_export_layout.itemAt(i).widget().setVisible(False)
	number_of_layers_checkbox.setVisible(True)
	number_of_nets_checkbox.setVisible(True)
	number_of_lines_checkbox.setVisible(True)
	number_of_segments_checkbox.setVisible(True)
	max_lines_checkbox.setVisible(True)
	max_seg_checkbox.setVisible(True)
	max_current_checkbox.setVisible(True)

	# Add dropdown with lines
	# lines_dropdown = QComboBox()
	# lines_dropdown.addItems([line for line in lines])

	analytical_lines_dropdown = QComboBox()
	analytical_lines_dropdown.addItems([line for line in analytical_lines])

	transient_lines_dropdown = QComboBox()
	transient_lines_dropdown.addItems([line for line in transient_lines])
	

	lines_label = (QLabel("Line to export:"),QLabel("Line to export:"))
	form_layout.addRow(lines_label[0], analytical_lines_dropdown)
	form_layout.addRow(lines_label[1], transient_lines_dropdown)

	lines_label[0].setVisible(False)
	lines_label[1].setVisible(False)
	analytical_lines_dropdown.setVisible(False)
	transient_lines_dropdown.setVisible(False)

	# Add dropdown for points
	points_dropdown = QComboBox()

	if transient_lines:
		print(f'transient_lines[0]: {transient_lines[0]}')
		line = transient_lines[0].split(" - ")[0]
		tech, temp, width = transient_lines[0].split(" - ")[1].split()
		
		simulated_vias_folder = directory + "/output/" + line+"/"+tech+"_"+temp+"_"+width + "/transient/"

		print(simulated_vias_folder + "original/")

		if os.path.exists(simulated_vias_folder + "original/"):
			simulated_vias_folder += "original/"
		elif os.path.exists(simulated_vias_folder + "reduced/"):
			simulated_vias_folder += "reduced/"
		else:
			print("Should never reach here")
			sys.exit()
		if os.path.exists(simulated_lines_folder):
			points_dropdown.addItems(get_all_points(line+"/"+tech+"_"+temp+"_"+width, simulated_vias_folder))

	points_label = QLabel("Via point to export:")
	form_layout.addRow(points_label, points_dropdown)

	points_label.setVisible(False)
	points_dropdown.setVisible(False)
	
	system_label = QLabel("System to export:")
	original_radio = QRadioButton("Original")
	#original_radio.setEnabled(False)
	original_radio.setChecked(False) 
	reduced_radio = QRadioButton("Reduced")
	reduced_radio.setChecked(False) 
	system_layout = QHBoxLayout()
	system_layout.addWidget(original_radio)
	system_layout.addWidget(reduced_radio)
	form_layout.addRow(system_label, system_layout)
	system_layout.itemAt(0).widget().setVisible(False)
	system_layout.itemAt(1).widget().setVisible(False)
	system_label.setVisible(False)
	button_group_system.addButton(original_radio)
	button_group_system.addButton(reduced_radio)
	if transient_lines:
		transient_dropdown_changes(system_layout,transient_lines_dropdown.currentText())
	else:
		system_layout.itemAt(0).widget().setEnabled(False)
		system_layout.itemAt(1).widget().setEnabled(False)

	analytical_lines_dropdown.currentIndexChanged.connect(lambda: lines_dropdown_changes(export_data_dropdown.currentIndex(), analytical_lines_dropdown, transient_lines_dropdown, points_dropdown, None))
	transient_lines_dropdown.currentIndexChanged.connect(lambda: lines_dropdown_changes(export_data_dropdown.currentIndex(), analytical_lines_dropdown, transient_lines_dropdown, points_dropdown, system_layout))

	export_file_label = QLabel("Path to export file:")
	export_file_entry = QLineEdit()
	browse_export_button = QPushButton("...")
	browse_export_button.clicked.connect(lambda: browse_export(export_dialog, export_file_entry))
	export_file_layout = QHBoxLayout()
	export_file_layout.addWidget(export_file_entry)
	export_file_layout.addWidget(browse_export_button)
	form_layout.addRow(export_file_label, export_file_layout)
	
	# add_line(form_layout)
	add_space(form_layout, 5)

	# Add the done & cancel buttons
	button_layout = QHBoxLayout()
	
	done_button = QPushButton("Done")
	done_button.setDefault(True)
	button_layout.addWidget(done_button)
	
	# Connect the dropdown with the checkboxes
	export_data_dropdown.currentIndexChanged.connect(lambda i: update_columns_to_export(i, lines_label, analytical_lines_dropdown,
										     transient_lines_dropdown, points_label, points_dropdown, columns_to_export_layout,
											 system_label,system_layout,done_button))


	done_button.clicked.connect(export_dialog.accept)
	done_button.clicked.connect(lambda: export_function(export_file_entry.text(), csv_radio.isChecked(), 
						     txt_radio.isChecked(), export_data_dropdown.currentIndex(),columns_to_export_layout,
							 analytical_lines_dropdown.currentText(), transient_lines_dropdown.currentText(), points_dropdown.currentText() if points_dropdown else None,
							 system_layout.itemAt(0).widget().isChecked(), system_layout.itemAt(1).widget().isChecked()))
	
	cancel_button = QPushButton("Cancel", export_dialog)
	cancel_button.clicked.connect(export_dialog.reject)
	button_layout.addWidget(cancel_button)

	button_layout.setAlignment(Qt.AlignHCenter)
	form_layout.addRow(button_layout)

	export_dialog.exec_()

def get_all_points(line, simulated_vias_folder):
	via_points = []
	if not os.path.exists(simulated_vias_folder):
		# generate_popup_message(f"No transient analysis was run on the original system for line {line}.", "info")
		return []
	
	try:
		for item in os.listdir(simulated_vias_folder):
			item_path = os.path.join(simulated_vias_folder, item)
			if item.endswith(".txt"):
				via_points.append(item.rstrip(".txt"))
	except Exception as e:
		generate_popup_message("An error occured while parsing the simulation files.", "error")
		return []
	
	if not via_points:
		generate_popup_message(f"No via points were analyzed for line {line}.", "info")
		return []
	
	# print(f"Simulated via_points: {via_points}")
	via_points = [via_point for via_point in via_points if "simulation_time" not in via_point]
	points_list = sorted([int(via_point) for via_point in via_points])
	return [str(point) for point in points_list]
	

def lines_dropdown_changes(export_type_idx, lines_dropdown_analytical, lines_dropdown_transient, points_dropdown, system_layout):
	global directory
	print("Got in lines_dropdown_changes")

	if export_type_idx == 0:
		generate_popup_message("An unexpected error occured.", "error")
		return
	elif export_type_idx == 1:
		line = lines_dropdown_analytical.currentText()
	elif export_type_idx==2:
		line_w_tech = lines_dropdown_transient.currentText()
		transient_dropdown_changes(system_layout,line_w_tech)
		line = line_w_tech.split(" - ")[0]
		tech, temp, width = line_w_tech.split(" - ")[1].split()
		line_w_tech_folder=directory+"/output/"+line+"/"+tech+"_"+temp+"_"+width
		simulated_vias_folder = f'{line_w_tech_folder}/transient/{"reduced" if system_layout.itemAt(1).widget().isChecked() else "original"}/'
		points_dropdown.clear()
		points_dropdown.addItems(get_all_points(line, simulated_vias_folder))


def export_function(file_location, is_csv, is_txt, columns_choice, columns_to_export , analytical_line, transient_line, via_point, original_enabled, mor_enabled):
	global directory
	print("Got in export!")
	file_str=""

	if not file_location:
		generate_popup_message("Please select the file location for the exported data.", "error")
		return
	if (is_csv and (not file_location.endswith('.csv'))) or (is_txt and (not file_location.endswith('.txt'))):
		generate_popup_message("Wrong filename extension.", "error")
		return
	
	if via_point:
		line = transient_line
		print(f"via_point: {via_point}")

		if not mor_enabled and not original_enabled:
			generate_popup_message("Neither the original nor the reduced system were chosen.", "error")
			return
	else:
		line = analytical_line

	print(f"line: {line}")

	print(f"columns_choice: {columns_choice}")
	if columns_choice == 0:
		print("General statistics of the power grid")

		path_to_stastitics = directory + "/statistics/Statistics.csv"
		print(f"Going to copy from {path_to_stastitics} to {file_location}")
		#                     : Vale mono ta columns pou exei epileksei o xristis
		list_cols = ["#layers", "#nets", "total #lines", "total #seg", "max #lines", "max #seg", "max current (A)"]
		file_str = "* * * PROTON Tool * * *\n"
		with open(path_to_stastitics, 'r', newline ='') as statsfile:
			all_stats = csv.reader(statsfile)
			i = 0
			for row in all_stats:
				if columns_to_export.itemAt(i).widget().isChecked():
					# if(columns_to_export.itemAt(5).widget().isChecked() and columns_to_export.itemAt(6).widget().isChecked()):
					if ("Max" in row[0]):
						file_str += list_cols[i] + ", " + row[1] + ", " + row[2].replace('.csv', '') + "\n"
					else:
						file_str += list_cols[i] + ", " + row[1] + "\n"
				i += 1
		print(f'file_str: {file_str}')
	elif columns_choice == 1:
		print("EM stress analysis results on selected line")
		
		stress_file_pattern = r"stress_([\d.]+)\."
		# Iterate over files in the directory
		line = line.split(" - ")[0]
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
								max_stress_loc = 0
								for line1 in lines: 
									if float(line1) > max_stress:
										max_stress = float(line1)
										max_stress_loc = i
									i += 1
								file_str+=f"* Maximum stress, {'{:.3}'.format(max_stress)} Pa at node {max_stress_loc}\n"

								if(columns_to_export.itemAt(7).widget().isChecked() and columns_to_export.itemAt(8).widget().isChecked()):
									file_str+="* Node , Stress\n"
									i=0
									for line1 in lines:
										file_str+=str(i)+" , "+line1
										i+=1
								elif columns_to_export.itemAt(7).widget().isChecked():
									i=0
									file_str+="Nodes\n"
									for line1 in lines:
										file_str+=str(i)+"\n"
										i=i+1
								elif columns_to_export.itemAt(8).widget().isChecked():
									file_str+="Stress\n"
									for line1 in lines:
										file_str+=line1
						except ValueError as e:
							generate_popup_message("Corrupted stress.txt file.","error")
	elif columns_choice == 2:
		print("EM Transient stress evolution on selected node")
		if not via_point:
			generate_popup_message("No via point to export was given.", "error")
			return
		line_w_tech = line
		line = line_w_tech.split(" - ")[0]
		tech, temp, width = line_w_tech.split(" - ")[1].split()
		technology_path=directory+"/output/"+line+"/"+tech+"_"+temp+"_"+width

		time_file=f'{technology_path}/transient/{"reduced" if mor_enabled else "original"}/simulation_time.txt'
		stress_tran_file=f'{technology_path}/transient/{"reduced" if mor_enabled else "original"}/{via_point}.txt'

		try:
			with open(time_file) as t_f:
				t_lines = t_f.readlines()
		except ValueError as e:
			generate_popup_message("Corrupted simulation_time file.","error")
		try:
			with open(stress_tran_file) as s_f:
				s_lines = s_f.readlines()
		except ValueError as e:
			generate_popup_message("Corrupted stress.txt file.","error")
		if(columns_to_export.itemAt(9).widget().isChecked() and columns_to_export.itemAt(10).widget().isChecked()):
			file_str+=f"* * * PROTON Tool * * *\n"
			file_str+=f"* Transient analysis of line {line} at {'{:.2e}'.format(float(t_lines[-1]))} sec with timestep {'{:.2e}'.format(float(t_lines[1]))} sec.\n"
			file_str+=f"* Technology, {tech}\n"
			file_str+=f"* Temperature, {temp} K\n"
			file_str+=f"* Width, {width} um\n"
			file_str+="* Time , Stress\n"
			for line1,line2 in zip(t_lines,s_lines):
				line1=line1.strip()
				line2=line2.strip()
				file_str+=line1+" , "+line2+"\n"
		elif columns_to_export.itemAt(9).widget().isChecked():
			file_str+="Time\n"
			for line2 in t_lines:
				file_str+=line2
		elif columns_to_export.itemAt(10).widget().isChecked():
			file_str+="Stress\n"
			for line2 in s_lines:
				file_str+=line2
			
	else:
		print("Something went terribly wrong. It should never reach this.")
		generate_popup_message("An unexpected error occured.", "error")
		return
	
	if columns_choice == 0 or columns_choice == 1 or columns_choice == 2:
		#create the file 
		try:
			with open(file_location,"w") as file:
				file.write(file_str)
		except FileNotFoundError as e:
			generate_popup_message("Export file doesnt exists.", "error")
			return
		except ValueError as e:
			generate_popup_message("Corrupted export file.","error")
			return
		except Exception as e:
			generate_popup_message("An error occured.","error")
			return
	
#---------------------------------------------------------------------------------------------------------------------------
# POWERGRID PLOT
def remove_powergrid_plot_panel(v_splitter):
	# Get the outer label
	outer_label = v_splitter.widget(0)
	if outer_label is not None:
		# Remove the layout
		layout = outer_label.layout()
		remove_all_widgets_from_layout(layout)
		# Remove the outer label
		# v_splitter.takeAt(0)
		outer_label.hide()
		outer_label.deleteLater()

def resize(event, fig, nav):
	# on resize reposition the navigation toolbar to (0,0) of the axes.
	x,y = fig.axes[0].transAxes.transform((0,0))
	figw, figh = fig.get_size_inches()
	ynew = int(figh*100- y - nav.frameGeometry().height()-20)
	nav.move(int(x),int(ynew))

def create_powergrid_plot_panel(v_splitter, selected_line):
	global NUM_OF_VIAS
	outer_label = QWidget()
	layout = QVBoxLayout()
	outer_label.setLayout(layout)
	outer_label.layout().setContentsMargins(0,0,0,0)
	outer_label.layout().setSpacing(0)
	outer_label.setMinimumHeight(250)

	hbox_first = QHBoxLayout()

	# The title of the label
	title_label = QLabel()
	# title_label.setAutoFillBackground(True)
	create_label_text(title_label, f"<h4>Geometric plot of powergrid line {selected_line}</h4>", "padding: 1px; border: none; color: #444444;", alignment=None)
	title_label.setMaximumHeight(30)
	hbox_first.addWidget(title_label)

	# Create a close button with an X icon
	close_button = QPushButton()
	close_button.setIcon(QIcon(os.path.join(INSTALLATION_FOLDER, "media/close-icon.png")))  # Provide the path to your own X icon
	close_button.setIconSize(QSize(25,25))  # Set the icon size to match the button
	button_size = 30
	close_button.setFixedSize(button_size, button_size)
	hbox_first.addWidget(close_button)
	layout.addLayout(hbox_first)

	close_button.clicked.connect(lambda: close_layout(layout))
	
	layout.addStretch()

	fig, total_length, NUM_OF_VIAS = plot_powergrid(outer_label, spice_function.benchmark, selected_line)
	canvas = FigureCanvas(fig)
	canvas.draw()
	# canvas.setStyleSheet("background-color: red;")
	nav_toolbar = NavigationToolbar(canvas, outer_label, coordinates=False)
	canvas.setMinimumHeight(int(160))
	nav_toolbar.setStyleSheet("QToolBar { border: 0px }")
	outer_label.layout().addWidget(canvas)

	label_str = "Length: " + str(total_length) + "um"
	length_label = QLabel(label_str) 
	length_label.setFixedWidth(130)
	length_label.setFixedHeight(30)
	
	layout.addStretch() 
	# layout.addWidget(nav_toolbar)
	# layout.addWidget(length_label)
	
	hbox_last = QHBoxLayout()
	hbox_last.addWidget(nav_toolbar)
	hbox_last.addWidget(length_label)
	layout.addLayout(hbox_last)

	v_splitter.insertWidget(0, outer_label)


#---------------------------------------------------------------------------------------------------------------------------
# EM STRESS PLOT
def plot_result(is_analytical, line, line_data, time_dropdown):
	print(is_analytical)
	print(line)
	print(line_data)
	print(time_dropdown)
	
	if line_data is not None and ((is_analytical and time_dropdown) or (not is_analytical)):
		if is_analytical:
			print(os.path.dirname(line_data))
			time = float(time_dropdown.currentText())
			add_plot(is_analytical_method=True, output_directory=os.path.dirname(line_data), sim_time=time)
		else:
			add_plot(is_analytical_method=False, output_directory=os.path.dirname(line_data[2]), sim_time=line_data[1], timestep=line_data[0], via_point=1, plot_reduced=line_data[3])
	else:
		generate_popup_message("No line was selected.", "error")

def create_opened_plot(line_plot):
	# The plot
	folder_path, file_name = os.path.split(line_plot)
	folder_path += '/'
	print(f'folder_path: {folder_path}')
	print(f"Going to get the sim_time from filename: {file_name}")
	stress_file_pattern = r"stress_([\d.]+)\."
	if file_name.endswith(".txt") and file_name.startswith("stress"):
		match = re.search(stress_file_pattern, file_name)
		if match:
			number = float(match.group(1))

	# If analytical
	
	add_plot(True, folder_path, number)
	# If numerical
	# add_plot(is_analytical_method=False, output_directory=folder_path, sim_time=sim_time, timestep=timestep, via_point=index, plot_reduced=mor_enabled)


def create_main_plot_panel(v_splitter):
	global plot_label, plot_layout

	# Create a layout for the frame
	outer_label = QLabel()
	outer_label.setMinimumHeight(400)
	# outer_label.setStyleSheet("background-color: rgb(255,255,255);") # THE DESTROYER STYLESHEET
	# outer_label.setMinimumSize(QSize(100,100))
	plot_layout = QVBoxLayout()
	outer_label.setLayout(plot_layout)

	v_splitter.addWidget(outer_label)

def remove_all_widgets_from_layout(layout):
	if layout is not None:
		index = layout.count()-1
		print(f"Items to delete: {index+1}")
		while(index >= 0):
			print(f"Going to delete item {index}")
			if layout.itemAt(index).layout() is not None:
				myLayout = layout.itemAt(index)
				remove_all_widgets_from_layout(myLayout)
				myLayout.setParent(None)
				myLayout.deleteLater()
			elif layout.itemAt(index).widget() is not None:
				myWidget = layout.itemAt(index).widget()
				myWidget.setParent(None)
				myWidget.deleteLater()
			index -= 1

def close_layout(layout):
	print("Going to close plot")
	if layout.count() > 0:
		remove_all_widgets_from_layout(layout)
	
def create_plot_wrapper(is_analytical, output_directory, heatmap_data, data_size, N, sim_time, timestep, x, y, via_point, mor_enabled):
	global SELECTED_LINE, plot_layout, right_frame_v_splitter

	# if SELECTED_LINE:
	# 	line_name = SELECTED_LINE.text(0)

	line_name = os.path.basename(os.path.dirname(output_directory))
	print(f"line_name: {line_name}")
		
	# Create the heatmap plot
	if plot_layout.count() > 0:
		remove_all_widgets_from_layout(plot_layout)

	hbox_first = QHBoxLayout()

	# The title of the label
	title_label = QLabel()
	title_label.setAutoFillBackground(True)
	# title_label.setStyleSheet("background-color: rgb(255,0,255);")
	formatted_time = "{:.2e}".format(sim_time).replace("+", "")
	years_sim_time = sim_time/31536000 
	if is_analytical:
		create_label_text(title_label, f"<h4>Heatmap of EM stress on line {line_name} at t={years_sim_time:.2f}y ({formatted_time}s)<br>(Configuration: {TECHNOLOGY}, {TEMPERATURE}K, {WIDTH}um)</h4>", "padding: 1px; border: none; color: #444444;", alignment=None)
	else:
		# create_panel_label(title_label, f"<h4>Transient evolution of Electromigration stress on line {SELECTED_LINE.text(0)} at t=20y with timestep {timestep:.2e}sec</h4>", "padding: 1px; border: none; color: #444444;", alignment=None)
		formatted_timestep = "{:.2e}".format(timestep).replace("+", "")
		years_timestep = timestep/31536000
		create_label_text(title_label, f"<h4>Transient evolution of EM stress on monitor point {via_point} on line {line_name}<br>at t={years_sim_time:.2f}y ({formatted_time}s) with timestep={years_timestep:.2f}y ({formatted_timestep}s) (Configuration: {TECHNOLOGY}, {TEMPERATURE}K, {WIDTH}um)</h4>", "padding: 1px; border: none; color: #444444;", alignment=None)
	# else:
	# 	generate_popup_message("No line was selected to simulate", "warning") #-alex
	# 	return
	
	title_label.setMaximumHeight(60)
	hbox_first.addWidget(title_label)

	# Create a close button with an X icon
	close_button = QPushButton()
	close_button.setIcon(QIcon(os.path.join(INSTALLATION_FOLDER, "media/close-icon.png")))  # Provide the path to your own X icon
	close_button.setIconSize(QSize(25,25))  # Set the icon size to match the button
	button_size = 30
	close_button.setFixedSize(button_size, button_size)
	# close_button.setStyleSheet("padding:2px;box-shadow:none;border:none;")


	# Connect the close button's clicked signal to the close_layout function
	close_button.clicked.connect(lambda: close_layout(plot_layout))

	# hbox_first.addStretch()
	# Add the close button to the layout
	hbox_first.addWidget(close_button)
	plot_layout.addLayout(hbox_first)
	
	if not is_analytical:
		hbox = QHBoxLayout()
		
		via_point_label = QLabel(" Via point to examine: ")
		via_point_label.setAutoFillBackground(True)
		via_point_label.setMaximumHeight(30)
		hbox.addWidget(via_point_label)

		via_point_selection = QComboBox()
		
		path_to_line_file = spice_function.benchmark + "/" + line_name.split("_")[0] + "/" + line_name + ".csv"
		with open(path_to_line_file, newline ='') as file:
			reader = csv.DictReader(file)
			NUM_OF_VIAS = len(list(reader)) + 1

		via_point_selection.addItems([str(i) for i in range(1, NUM_OF_VIAS+1)])
		via_point_selection.setCurrentText(str(via_point))
		via_point_selection.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		hbox.addWidget(via_point_selection)
		via_point_selection.currentIndexChanged.connect(lambda index: transient_plot_via_selection(index, output_directory, sim_time, timestep, mor_enabled))

		hbox.setAlignment(Qt.AlignLeft)
		# hbox.addStretch()

		# checkbox = QCheckBox("Grid", plot_layout)
    	# checkbox.setToolTip("Toggle grid")
    	# checkbox.setChecked(GRID_ON)
		toggle_grid_button = QCheckBox('Show grid')
		toggle_grid_button.setFixedWidth(150)
		toggle_grid_button.setChecked(EM_tool_plots.grid_state)
		hbox.addWidget(toggle_grid_button)
		
		plot_layout.addLayout(hbox)

	plot_label = QLabel()
	plot_label.setVisible(False)
	if is_analytical:
		fig, ax = create_heatmap(heatmap_data, N)
	else:
		fig, ax = create_transient(timestep, x, y)
		# plot_label.resizeEvent = lambda event: on_pg_plot_resize(event, fig, canv, plot_label)
		
	fig.subplots_adjust(left=0.7)
	fig.tight_layout()
	canv = FigureCanvas(fig)
	canv.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
	canv.setVisible(False)
	if is_analytical:
		plot_label.resizeEvent = lambda event: on_pg_heatmap_resize(event, fig, canv, plot_label)
	else:
		plot_label.resizeEvent = lambda event: on_transient_plot_resize(event, fig, canv, plot_label)
		ax.set_aspect('auto')
		# canv.draw()
	plot_layout.addWidget(plot_label)
	canv.setParent(plot_label)
	navbar = NavigationToolbar(canv, plot_label)
	navbar.setStyleSheet("QToolBar { border: 0px }")
	canv.move(0,0)
	canv.draw()
	canv.setVisible(True)
	plot_label.setVisible(True)
	plot_layout.addWidget(navbar)
	right_frame_v_splitter.setSizes([3, 3, 1])
	if not is_analytical:
		toggle_grid_button.clicked.connect(lambda: toggle_grid(toggle_grid_button.isChecked(), canv))
		toggle_grid_button.clicked.connect(lambda: print(f"toggle grid isChecked: {toggle_grid_button.isChecked()}"))
	
def transient_plot_via_selection(index, output_directory, sim_time, timestep, mor_enabled):
	global directory, SELECTED_LINE, TECHNOLOGY, TEMPERATURE, WIDTH
	index += 1
	print(index)
	# line_path = line_name+"/"+TECHNOLOGY+"_"+str(TEMPERATURE)+"_"+str(WIDTH)+"/"
	# output_files = directory + "/output/"+line_path
	add_plot(is_analytical_method=False, output_directory=output_directory, sim_time=sim_time, timestep=timestep, via_point=index, plot_reduced=mor_enabled)

def add_plot(is_analytical_method, output_directory, sim_time, timestep=None, via_point=None, plot_reduced=False):

	# Create the heatmap plot
	if is_analytical_method:
		message = "Creating heatmap plot..."
	else:
		message = "Create transient plot..."
	try:
		log_keeper.track_history_messages(message, False)
	except NameError as e:
		pass

	output_directory = os.path.normpath(output_directory)
	if is_analytical_method:
		stress = []
		try:
			# Find here all the files with pattern stress_<time>.txt
			stress_file_pattern = r"stress_([\d.]+)\."
			file_dict = {}
			# Iterate over files in the directory
			for filename in os.listdir(output_directory):
				if filename.endswith(".txt") and filename.startswith("stress"):
					match = re.search(stress_file_pattern, filename)
					if match:
						number = float(match.group(1))
						file_dict[number] = filename
			print(f"Stress file dictionary: {file_dict}")
			print(f"Looking for sim_time: {sim_time}")
			
			with open(os.path.join(output_directory, file_dict[sim_time]), "r") as f:
				i = 0
				for line in f:
					if 'nan' in line.lower():
						generate_popup_message("Hydrostatic stress contains NaN values.", "error")
						try:
							log_keeper.track_history_messages("Hydrostatic stress contains NaN values. The plot cannot be created.", False, "error")
						except NameError as e:
							pass
						return
					stress.append(float(line))
					i += 1
		except Exception as e:
			print(f'error: {e}')
			generate_popup_message("There was a problem with the simulation results. Try again.", "error")
			try:
				log_keeper.track_history_messages("There was a problem with the simulation results while creating heatmap.", False, "error")
			except NameError as e:
				pass
			return
		stress_array = np.array(stress)
		data_size = len(stress_array)
		N = data_size
		tile_ratio = int(data_size/30)
		print(f'tile_ratio: {tile_ratio}')
		if tile_ratio == 0:
			tile_ratio = 1
		heatmap_data = np.tile(stress_array,(tile_ratio,1))

		print(f'output_directory: {output_directory}')
		create_plot_wrapper(is_analytical_method, output_directory, heatmap_data, data_size, N, sim_time, None, None, None, None, None)
	else:
		stress = []
		if plot_reduced:
			stress_file = os.path.join(output_directory, f"transient/reduced/{via_point}.txt")
		else:
			stress_file = os.path.join(output_directory, f"transient/original/{via_point}.txt")
		try:
			with open(stress_file, "r") as f:
				i = 0
				for line in f:
					if 'nan' in line.lower():
						generate_popup_message("Hydrostatic stress contains NaN values.", "error")
						try:
							log_keeper.track_history_messages("Hydrostatic stress contains NaN values. The plot cannot be created.", False, "error")
						except NameError as e:
							pass
						return
					stress.append(float(line))
					i += 1
		except Exception as e:
			generate_popup_message("There was a problem with the simulation results. Try again.", "error")
			return
		# Get x (time)
		transient_folder = os.path.join(output_directory,"transient")
		vias_folder = os.path.join(transient_folder, "reduced" if plot_reduced else "original")
		time_file = os.path.join(vias_folder, 'simulation_time.txt')
		x = []
		with open(time_file, "r") as f:
			j = 0
			for line in f:
				x.append(float(line))
				j += 1

		timestep = float(1e6)

		x = np.array(x)
		y = np.array(stress)
		create_plot_wrapper(is_analytical_method, output_directory, None, None, None, sim_time, timestep, x, y, via_point, plot_reduced)


#--------------------------------------------------------------------------------
#MAIN WINDOW LOWER RIGHT WIDGETS

def find_line(item, name):
	if item.text(0) == name:
		return item

	for i in range(item.childCount()):
		child = item.child(i)
		result = find_line(child, name)
		if result is not None:
			return result
	return None
	
def handle_item_double_clicked(item):
	global right_frame_v_splitter
	text = item.text()
	match = re.search(r"Location\s+(\S+)\.csv", text)
	if match:
		match_str = match.group(1).lstrip()
		print("Item double-clicked: ", match_str)
		
		for i in range(powergrid_tree.topLevelItemCount()):
			item = find_line(powergrid_tree.topLevelItem(i),match_str)
			if item:
				on_line_clicked(item, right_frame_v_splitter)
				break
		
		if not item:
			print("Line not found! This should never happen.")
    
def create_table(list_cols, row1):
	table = QTableWidget()
	
	table.setRowCount(1)
	table.setColumnCount(len(list_cols))
	table.setHorizontalHeaderLabels(list_cols)
	
	table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
	table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
	table.verticalHeader().setVisible(False)  # hide the row numbers

	for i in range(len(list_cols)):
		item = QTableWidgetItem(row1[i])
		item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
		table.setItem(0,i,item)
	
	table.setSelectionMode(QAbstractItemView.ContiguousSelection)
	table.setEditTriggers(QAbstractItemView.NoEditTriggers)
	table.itemDoubleClicked.connect(handle_item_double_clicked)  # connect the signal to your slot


	return table

def create_table_stats_tab(parent):
	# table_widget = QTableWidget(8, 2, parent)


	# # The table
	table_label = QLabel()
	table_label.setLayout(QVBoxLayout())
	list_cols = ["#layers", "#nets", "total #lines", "total #seg", "max #lines", "max #seg", "max current (A)"] #, "max curden"]
	stats = []
	path_to_stastitics = directory + "/statistics/Statistics.csv"

	try:
		with open(path_to_stastitics, 'r', newline ='') as statsfile:
			all_stats = csv.reader(statsfile)
			for row in all_stats:
				if ("Max" in row[0]):
					temp_item = row[1]+"\n"+row[2]
					stats.append(temp_item)
				else:
					stats.append(row[1])
		statsfile.close()
	except e:
		print('There was a problem loading statistics file. Cannot load project.')
		return None

	table = create_table(list_cols, stats)
	table_label.layout().addWidget(table)
	table_label.setAlignment(Qt.AlignBottom)
	# layout.addWidget(table_label)
	# outer_label.resizeEvent = lambda event: table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
	

	return table_label

def create_analytics_panel(v_splitter):
	# Create a layout for the frame
	global log_keeper

	outer_label = QLabel()
	outer_label.setMinimumHeight(150)
	# outer_label.setStyleSheet("background-color: rgb(255,255,255);")

	layout = QVBoxLayout()
	outer_label.setLayout(layout)

	tab_widget = QTabWidget(outer_label)

	log_keeper = Message_log_handling(tab_widget, directory)
	console_tab = log_keeper.get_widget()
	tab_widget.addTab(console_tab, "Message Log")

	table_tab = create_table_stats_tab(tab_widget)
	tab_widget.addTab(table_tab, "Power grid analytics")


	layout.addWidget(tab_widget)

	v_splitter.addWidget(outer_label)

#--------------------------------------------------------------------------------
#RESIZING PLOTS

def on_pg_heatmap_resize(event, fig, canvas, qframe):
	# use a timer to delay the execution of the function
	QTimer.singleShot(PLOT_DELAY, lambda: _on_pg_plot_resize(fig, canvas, qframe))

def on_pg_plot_resize(event, fig, canvas, qframe):
	# use a timer to delay the execution of the function
	QTimer.singleShot(PLOT_DELAY, lambda: _on_pg_plot_resize(fig, canvas, qframe))

def _on_pg_plot_resize(fig, canvas, qframe):
	qframe_geometry = qframe.geometry()
	canvas.setGeometry(qframe.geometry())
	width, height = qframe_geometry.width() - PLOTS_LABEL_PIXEL_MARGIN, qframe_geometry.height() - PLOTS_LABEL_PIXEL_MARGIN
	#canvas.setGeometry(0, 0, width, height)
	#fig.tight_layout()
	ax = fig.gca()
	ax.set_aspect('equal')
	canvas.draw()

def on_transient_plot_resize(event, fig, canvas, qframe):
	# use a timer to delay the execution of the function
	QTimer.singleShot(PLOT_DELAY, lambda: _on_transient_plot_resize(fig, canvas, qframe))

def _on_transient_plot_resize(fig, canvas, qframe):
	# canvas.setGeometry(qframe.geometry())
	qframe_geometry = qframe.geometry()
	width, height = qframe_geometry.width() - PLOTS_LABEL_PIXEL_MARGIN, qframe_geometry.height() - PLOTS_LABEL_PIXEL_MARGIN
	canvas.setGeometry(0, 0, width, height)
	
	#fig.tight_layout()
	# ax.set_aspect('equal')
	canvas.draw()

#----------------------------------------------------------------------------------
def extract_numbers(string):
    matches = re.findall(r'\d+', string)
    return tuple(map(int, matches))

def add_items(parent, path):
	global SELECTED_LINE

	selected_item = None
	files = os.listdir(path)
	sorted_files = sorted(files, key=extract_numbers)

	for item in sorted_files:
		item_path = os.path.join(path, item)
		if os.path.isdir(item_path):
			# Add a new folder to the tree
			folder = QTreeWidgetItem(parent)
			folder.setText(0, item)
			folder.setIcon(0, QtGui.QIcon("folder.png"))
			add_items(folder, item_path)
		else:
			# Add a new file to the tree
			file_name = os.path.splitext(item)[0]
			file = QTreeWidgetItem(parent)
			file.setText(0, file_name)
			file.setIcon(0, QtGui.QIcon("file.png"))
			file.setFont(0, QtGui.QFont('MS Shell Dlg 2', 10, weight=QtGui.QFont.Normal))
			if json_data_sim['workspace_details']['selected_line'] and json_data_sim['workspace_details']['selected_line'] == file_name:
				SELECTED_LINE = file
				


def create_powergrid_tree(folder_path, right_frame_v_splitter):
	global SELECTED_LINE, powergrid_tree
	tree = QTreeWidget()
	tree.setHeaderHidden(True)

	# Recursively add folders and files to the tree
	add_items(tree.invisibleRootItem(), folder_path)
	if SELECTED_LINE:
		temp_selected_line = SELECTED_LINE
		SELECTED_LINE = ""
		on_line_clicked(temp_selected_line, right_frame_v_splitter, user_driven=False)

	tree.itemClicked.connect(lambda item: on_line_clicked(item, right_frame_v_splitter))

	powergrid_tree = tree
	return tree


def on_line_clicked(item, right_frame_v_splitter, user_driven=True):
	global DELETE_OLD_DISCR_FLAG, SELECTED_LINE,directory
	if item.parent() is None:
		# This is a folder, do nothing
		return
	if SELECTED_LINE:
		
		# # If the DELETE_OLD_DISCR_FLAG is set to True, 
		# # then the file created for the Analytical is removed
		# if DELETE_OLD_DISCR_FLAG and user_driven:
		# 	# Check if discretization has been applied
			
		# 	filename = directory + "/" + "input" + "/"+SELECTED_LINE.text(0)+"/analytical.txt"
		# 	if os.path.exists(filename):
		# 		answer = generate_popup_message(f"Discretization has already been applied on selected line {SELECTED_LINE.text(0)}. By selecting another line, the discretization will removed.",'info', True)

		# 		if not answer:
		# 			return
			
		# 		try:
		# 			os.remove(filename)
		# 		except OSError as e:
		# 			print("The file did not exist.")
		
		SELECTED_LINE.setFont(0, QtGui.QFont('MS Shell Dlg 2', 10, weight=QtGui.QFont.Normal))
		
		SELECTED_LINE_name = item.text(0)
		message = "Removing powergrid plot for line " + SELECTED_LINE_name
		log_keeper.track_history_messages(message, False)

		remove_powergrid_plot_panel(right_frame_v_splitter)
	if SELECTED_LINE != item:

		SELECTED_LINE = item
		SELECTED_LINE.setFont(0, QtGui.QFont('MS Shell Dlg 2', 10, weight=QtGui.QFont.Bold))
		SELECTED_LINE_name = item.text(0)
		
		message = SELECTED_LINE_name + " line was selected. Creating powergrid plot..."
		log_keeper.track_history_messages(message, False)

		json_data_sim['workspace_details']['selected_line'] = SELECTED_LINE.text(0)
		
		create_powergrid_plot_panel(right_frame_v_splitter, SELECTED_LINE_name)

		message = "Created the powergrid plot for " + SELECTED_LINE_name
		log_keeper.track_history_messages(message, False, "success")
	else:
		SELECTED_LINE = ""
		json_data_sim["workspace_details"]['selected_line'] = ""

def interp_array(arr, new_size):
	x = np.linspace(0, 1, arr.size)
	y = arr
	f = np.interp(np.linspace(0, 1, new_size), x, y)
	return f


#--------------------------------------------------------------------------------
#ALL THE DISCRETAZATION STUFF

def handle_nx_total_message(nx_total):
	global DISCR_SIZE
	DISCR_SIZE = nx_total
	print(f"DISCR_SIZE: {DISCR_SIZE}")

def handle_discretization_messages(return_message):
	global DISCR_SIZE
	if "seconds" in return_message:
		#THA PREPEI TO APOTELESMA APO EDW NA GRAFTEI SE CONFIG.JSON GIA NA TO PAREI META TO SIMULATE?
		generate_popup_message(f'Line {SELECTED_LINE.text(0)} was successfully discretized into {DISCR_SIZE} nodes {return_message}.','info')
		message = f'Line {SELECTED_LINE.text(0)} was successfully discretized into {DISCR_SIZE} nodes {return_message}.'
		msg_type = "success"
	else:
		generate_popup_message(return_message,'error')
		message = return_message	
		msg_type = "error"		
	log_keeper.track_history_messages(message, False, msg_type)
	return return_message

def handle_analytical_messages(return_message, sim_time):
	global directory, SELECTED_LINE, TECHNOLOGY, TEMPERATURE, WIDTH
	if "seconds" in return_message:
		#THA PREPEI TO APOTELESMA APO EDW NA GRAFTEI SE CONFIG.JSON GIA NA TO PAREI META TO SIMULATE?
		
		message = return_message
		msg_type = "success"
		log_keeper.track_history_messages(message, False, msg_type)

		answer = generate_popup_message('Line analysis was successfully performed. Would like like to plot the heatmap of the results?','info', True)
		if answer:
			line_path = SELECTED_LINE.text(0)+"/"+TECHNOLOGY+"_"+str(TEMPERATURE)+"_"+str(WIDTH)+"/"
			output_files = directory + "/output/"+line_path
			add_plot(True, output_files, sim_time)
	else:
		generate_popup_message(return_message,'error')
		if(SELECTED_LINE):
			message = f"There was a problem while analysing line {SELECTED_LINE.text(0)}."
		else:
			message = 'No line was selected and discretized prior to simulation.'
		msg_type = "error"
		log_keeper.track_history_messages(message, False, msg_type)		
		
	return return_message

def handle_transient_messages(return_message, sim_time, timestep, via_to_plot, mor_enabled):
	global directory, SELECTED_LINE, TECHNOLOGY, TEMPERATURE, WIDTH
	if "seconds" in return_message:

		message = return_message
		msg_type = "success"
		log_keeper.track_history_messages(message, False, msg_type)

		answer = generate_popup_message('Point analysis was successfully performed. Would like like to plot the transient plot of the results?','info', True)
		if answer:
			line_path = SELECTED_LINE.text(0)+"/"+TECHNOLOGY+"_"+str(TEMPERATURE)+"_"+str(WIDTH)+"/"
			output_files = directory + "/output/"+line_path
			print(f"via point: {via_to_plot}")
			add_plot(False, output_files, sim_time, timestep, via_point=via_to_plot, plot_reduced=mor_enabled)
	else:
		generate_popup_message(return_message,'error')
		if(SELECTED_LINE):
			message = f"There was a problem while analysing line {SELECTED_LINE.text(0)}."
		else:
			message = 'No line was selected and discretized prior to simulation.'
		msg_type = "error"
	# else:
	# 	message = f"Point analysis was successfully performed on {SELECTED_LINE.text(0)}."
	log_keeper.track_history_messages(message, False, msg_type)
	return return_message


def delete_matrix_form_thread():
	global matrix_formulation_worker, matrix_formulation_thread
	matrix_formulation_worker = None
	matrix_formulation_thread = None
def delete_analytical_from_thread():
	global analytical_worker,analytical_thread
	analytical_worker = None
	analytical_thread = None
def delete_transient_from_thread():
	global transient_worker,transient_thread
	transient_worker = None
	transient_thread = None

class LoadingIcon(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setFixedSize(400,400)
		self.setWindowFlags(Qt.Widget)
		self.setAttribute(Qt.WA_TranslucentBackground)

		self.label_animation = QLabel(self)
		self.movie = QMovie(os.path.join(INSTALLATION_FOLDER, 'media/loading-23.gif'))
		size = QSize(400,226)
		self.movie.setScaledSize(size)
		self.label_animation.setMovie(self.movie)

		self.startAnimation()
		self.show()

	def startAnimation(self):
		self.movie.start()

	def stopAnimation(self):
		self.movie.stop()
		self.close()
		self.setParent(None)

	def showEvent(self, event):
		self.raise_()
		super().showEvent(event)


def discr_line(discr_button, tech, temp, width, discr_param, points, step):
	global window, directory, SELECTED_LINE, matrix_formulation_worker, matrix_formulation_thread
	global TECHNOLOGY, TEMPERATURE, WIDTH

	print("pressed discretize line!!")
	print(f"Technology: {tech}")
	print(f"Temperature: {temp}")
	print(f"Width: {width}")
	
	try:
		if float(temp) <= 0:
			generate_popup_message('Temperature should be a positive number.','error')
			return
	except Exception:
		generate_popup_message('Temperature should be a positive number.','error')
		return

	try:
		if float(width) <= 0:
			generate_popup_message('Width should be a positive number.','error')
			return
	except Exception:
		generate_popup_message('Width should be a positive number.','error')
		return

	if discr_param == "Discret. points":
		print(f"Points: {points}")
		temp_str = " Discret points: " + points

		try:
			if int(points) <= 0:
				generate_popup_message('Discretization points should be a positive integer.','error')
				return
		except Exception:
				generate_popup_message('Discretization points should be a positive integer.','error')
				return

		json_data_sim['discretization']['parameter'] = 'points'
		json_data_sim['discretization']['points'] = int(points)
	elif discr_param == "Discret. step":
		print(f"Step: {step}")
		temp_str = " Spatial step: " + step
		
		try:
			if float(step) <= 0:
				generate_popup_message('Discretization step should be a positive floating point number.','error')
				return
		except Exception:
			generate_popup_message('Discretization step should be a positive floating point number.','error')
			return
		json_data_sim['discretization']['parameter'] = 'step'
		json_data_sim['discretization']['step'] = float(step)
	else:
		print("Something went terribly wrong with discr. param!")
		generate_popup_message('Something went terribly wrong with discr. parameter.','error')
		return
	
	json_data_sim['line']['technology'] = tech
	json_data_sim['line']['temperature'] = float(temp)
	json_data_sim['line']['width'] = float(width)

	print(f"directory: {directory}")
	print(f"benchmark: {spice_function.benchmark}")
	if SELECTED_LINE:
		print(f"Selected line: {SELECTED_LINE.text(0)}")
		json_data_sim['workspace_details']['selected_line'] = SELECTED_LINE.text(0)
	else:
		print("No line was selected")
		json_data_sim['workspace_details']['selected_line'] = SELECTED_LINE
		generate_popup_message('No line was selected.','error')
		return
	
	TECHNOLOGY = tech
	TEMPERATURE = float(temp)
	WIDTH = float(width)
	print(f'TECHNOLOGY: {TECHNOLOGY}')
	print(f'TEMPERATURE: {TEMPERATURE}')
	print(f'WIDTH: {WIDTH}')

	csv_filename = spice_function.benchmark + "/" + SELECTED_LINE.text(0).split("_")[0] + "/" + SELECTED_LINE.text(0)+".csv"

	if matrix_formulation_thread:
		matrix_formulation_worker = None
		matrix_formulation_thread.quit()
		matrix_formulation_thread.wait()
		matrix_formulation_thread = None

	if discr_param == "Discret. points":
		matrix_formulation_worker = Matrix_Formulation_Class(csv_file=csv_filename,project_location=directory,sp_step=None,given_disc_point=points,technology=tech,temperature=float(temp),givenWidth=float(width))
	else:
		matrix_formulation_worker = Matrix_Formulation_Class(csv_file=csv_filename,project_location=directory,sp_step=step,given_disc_point=None,technology=tech,temperature=float(temp),givenWidth=float(width))
	
	# Create thread and assign it to worker
	matrix_formulation_thread = QThread()
	matrix_formulation_worker.moveToThread(matrix_formulation_thread)

	# Run the desired function
	matrix_formulation_thread.started.connect(matrix_formulation_worker.matrix_formulation)

	# Destroy both thread and worker when job is done
	matrix_formulation_worker.nx_total_message.connect(handle_nx_total_message)
	matrix_formulation_worker.return_message.connect(handle_discretization_messages)
	matrix_formulation_worker.finished.connect(matrix_formulation_thread.quit)
	matrix_formulation_worker.finished.connect(matrix_formulation_thread.wait)
	# matrix_formulation_worker.finished.connect(matrix_formulation_worker.deleteLater)
	# matrix_formulation_thread.finished.connect(matrix_formulation_thread.deleteLater)
	matrix_formulation_worker.finished.connect(delete_matrix_form_thread)

	discr_button.setEnabled(False)
	matrix_formulation_worker.finished.connect(lambda: discr_button.setEnabled(True))

	loading_screen = LoadingIcon(window)
	loading_screen.move(int(window.width() // 2 - loading_screen.width() // 3), int(window.height() // 2 - loading_screen.height()// 3))
	loading_screen.move(int(window.width() // 2 - loading_screen.width() // 4), int(window.height() // 2 - loading_screen.height()// 4))
	matrix_formulation_worker.finished.connect(lambda: loading_screen.stopAnimation())

	# Start the thread
	matrix_formulation_thread.start()
	print("Reached here")

def discr_param_select(step_label, step_field, points_label, points_field, discr_param_text):
	

	if discr_param_text == "Discret. step":
		step_label.show()
		step_field.show()
		points_label.hide()
		points_field.hide()
		# points_label.setFixedHeight(0)
		# points_field.setFixedHeight(0)
		# step_label.setFixedHeight(30)
		# step_field.setFixedHeight(30)
	else:
		step_label.hide()
		step_field.hide()
		points_label.show()
		points_field.show()
		# points_label.setFixedHeight(30)
		# points_field.setFixedHeight(30)
		# step_label.setFixedHeight(0)
		# step_field.setFixedHeight(0)

def create_form(json_path):
	global json_data_sim, TECHNOLOGY, TEMPERATURE, WIDTH
	# read json file
	with open(json_path, "r") as json_file:
		json_data_sim = json.load(json_file)
	
	#print(json_data_sim)
	# create form layout
	form_layout = QFormLayout()
	
	# line group box
	line_group = QGroupBox("Line")
	line_layout = QFormLayout()
	line_tech_combo = QComboBox()
	line_tech_combo.addItems(["CuDD", "Al"])
	line_tech_combo.setCurrentText(json_data_sim["line"]["technology"])
	line_layout.addRow(QLabel("Technology"), line_tech_combo)
	TECHNOLOGY = json_data_sim["line"]["technology"]
	# print(f"JSON TECHNOLOGY: {TECHNOLOGY}")
	
	# Add Temperature field
	temp_line_edit = QLineEdit(str(json_data_sim["line"]["temperature"]), alignment=Qt.AlignRight)
	line_layout.addRow(QLabel("Temperature (K)"), temp_line_edit)
	TEMPERATURE = float(json_data_sim["line"]["temperature"])

	width_edit = QLineEdit(str(json_data_sim["line"]["width"]), alignment=Qt.AlignRight)
	line_layout.addRow(QLabel("Width (um)"), width_edit)
	WIDTH = float(json_data_sim["line"]["width"])
	# save_button = QPushButton("Visualize powergrid line")
	# line_layout.addRow(save_button)
	line_group.setLayout(line_layout)
	form_layout.addRow(line_group)

	# discretization group box
	disc_group = QGroupBox("Spatial Discretization")
	disc_layout = QFormLayout()
	
	disc_param_combo = QComboBox()
	disc_param_combo.addItems(["Discret. points", "Discret. step"])
	disc_param_combo.setCurrentText(json_data_sim["discretization"]["parameter"])
	disc_layout.addRow(QLabel("Parameter"), disc_param_combo)
	
	points_field = QLineEdit(str(json_data_sim["discretization"]["points"]), alignment=Qt.AlignRight)
	
	step_field = QLineEdit(str(json_data_sim["discretization"]["step"]), alignment=Qt.AlignRight)
	
	points_label = QLabel("Discretization points")
	disc_layout.addRow(points_label, points_field)
	
	step_label =   QLabel("Discret. step (um)   ")
	disc_layout.addRow(step_label, step_field)
	
	if disc_param_combo.currentText() == "Discret. step":
		points_label.setVisible(False)
		points_field.setVisible(False)
	else:
		step_label.setVisible(False)
		step_field.setVisible(False)
	# discr_button = QPushButton("Discretize powergrid line")
	# disc_layout.addRow(discr_button)
	disc_param_combo.currentTextChanged.connect(lambda: discr_param_select(step_label, step_field, points_label, points_field, disc_param_combo.currentText()))
	disc_group.setLayout(disc_layout)
	form_layout.addRow(disc_group)
	
	# create buttons
	discr_button = QPushButton("Discretize powergrid line")

	buttons_layout = QHBoxLayout()
	# # buttons_layout.addWidget(save_button)
	buttons_layout.addWidget(discr_button)
	discr_button.clicked.connect(lambda: discr_line(discr_button,line_tech_combo.currentText(), temp_line_edit.text(),
						 width_edit.text(), disc_param_combo.currentText(), points_field.text(), step_field.text()))

	# add buttons to form layout
	form_layout.addRow(buttons_layout)

	return form_layout

#--------------------------------------------------------------------------------------------------------------------------------

def analytical_wrapper(sim_time, time_measuring):
	global window, directory, SELECTED_LINE, analytical_thread, analytical_worker
	global IS_LINUX

	time_coeff = 1
	if time_measuring == "years":
		# Turn years to seconds
		time_coeff = 31536000

	try:
		sim_time = float(sim_time)*time_coeff
		if sim_time < 0:
			raise ValueError
	except ValueError:
		generate_popup_message("Simulation time must be a non-negative number.", "error")
		return

	if analytical_thread:
		analytical_worker = None
		analytical_thread.quit()
		analytical_thread.wait()
		analytical_thread = None
	
	analytical_worker=Analytical_Class(sim_time=sim_time,directory=directory,SELECTED_LINE=SELECTED_LINE,TECHNOLOGY=TECHNOLOGY,TEMPERATURE=TEMPERATURE,WIDTH=WIDTH,IS_LINUX=IS_LINUX, INSTALLATION_FOLDER=INSTALLATION_FOLDER)

	analytical_thread = QThread()
	analytical_worker.moveToThread(analytical_thread)

	analytical_thread.started.connect(analytical_worker.analytical_function)

	analytical_worker.return_message.connect(lambda return_message: handle_analytical_messages(return_message, sim_time))
	analytical_worker.finished.connect(analytical_thread.quit)
	analytical_worker.finished.connect(analytical_thread.wait)
	analytical_worker.finished.connect(delete_analytical_from_thread)

	loading_screen = LoadingIcon(window)
	loading_screen.move(int(window.width() // 2 - loading_screen.width() // 3), int(window.height() // 2 - loading_screen.height()// 3))
	loading_screen.move(int(window.width() // 2 - loading_screen.width() // 4), int(window.height() // 2 - loading_screen.height()// 4))
	analytical_worker.finished.connect(lambda: loading_screen.stopAnimation())

	analytical_thread.start()

def transient_function(sim_time, timestep,mor_enabled,reduced_order, time_measuring, timestep_measuring):
	global directory , SELECTED_LINE, log_keeper, transient_worker, transient_thread
	global TECHNOLOGY, TEMPERATURE, WIDTH, DISCR_SIZE, IS_LINUX

	is_via=True
	via_point=1
	internal_point=False

	if not SELECTED_LINE:
		message = 'No line was selected and discretized prior to simulation.'
		generate_popup_message(message)
		log_keeper.track_history_messages(message, False, "error") 
		return

	if not sim_time or not timestep:
		generate_popup_message("Analysis time and timestep are requried fields.", "error")
		return

	time_coeff = 1
	if time_measuring == "years":
		# Turn years to seconds
		time_coeff = 31536000

	try:
		sim_time = float(sim_time)*time_coeff
		if sim_time < 0:
			raise ValueError
	except ValueError:
		generate_popup_message("Simulation time must be a non-negative number.", "error")
		return
	
	time_coeff = 1
	if timestep_measuring == "years":
		# Turn years to seconds
		time_coeff = 31536000

	try:
		timestep = float(timestep)*time_coeff
		if timestep < 0:
			raise ValueError
	except ValueError:
		generate_popup_message("Timestep must be a non-negative number.", "error")
		return
	
	if timestep > sim_time:
		generate_popup_message('Timestep must be less than simulation time.', 'error')
		return

	print(f"Going to perform transient analysis on line {SELECTED_LINE.text(0)} at t={sim_time} with timestep={timestep}")
	print(f"is_via: {is_via}")
	if is_via:
		print("It is a via point!")
		print(f"In particular, {via_point}")
	else:
		print("It is an internal point")
		print(f"In particular, {internal_point}")

	print(f"Going to perform MOR: {mor_enabled}")
	if mor_enabled:
		print(f"reduced_order: {reduced_order}")

	if transient_thread:
		transient_worker = None
		transient_thread.quit()
		transient_thread.wait()
		transient_thread = None
	
	transient_worker=Transient_Class(sim_time=sim_time, timestep=timestep, directory=directory, 
				SELECTED_LINE=SELECTED_LINE, TECHNOLOGY=TECHNOLOGY, TEMPERATURE=TEMPERATURE, WIDTH=WIDTH, NX_TOTAL = DISCR_SIZE,
				mor_enabled=mor_enabled, reduced_order=reduced_order, IS_LINUX=IS_LINUX, INSTALLATION_FOLDER=INSTALLATION_FOLDER)
	
	transient_thread = QThread()
	transient_worker.moveToThread(transient_thread)

	transient_thread.started.connect(transient_worker.transient_function)

	transient_worker.return_message.connect(lambda return_message: handle_transient_messages(return_message, sim_time, timestep, via_point, mor_enabled))
	transient_worker.info_message.connect(lambda message: log_keeper.track_history_messages(message, False, "info") )
	transient_worker.finished.connect(transient_thread.quit)
	transient_worker.finished.connect(transient_thread.wait)
	transient_worker.finished.connect(delete_transient_from_thread)

	loading_screen = LoadingIcon(window)
	loading_screen.move(int(window.width() // 2 - loading_screen.width() // 3), int(window.height() // 2 - loading_screen.height()// 3))
	loading_screen.move(int(window.width() // 2 - loading_screen.width() // 4), int(window.height() // 2 - loading_screen.height()// 4))
	transient_worker.finished.connect(lambda: loading_screen.stopAnimation())

	transient_thread.start()

