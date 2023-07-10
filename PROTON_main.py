import GUI_auxiliary
import spice_function
import history_handling
import shutil
import sys
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

from GUI_auxiliary import *

menu = None
spice_parser_worker = None
spice_parser_thread = None

def simulate(window):
	#global GUI_auxiliary.json_data_sim

	print("hello from simulate widow")
	simulate_dialog = QDialog()
	simulate_dialog.setWindowTitle("Simulation")
	icon = QtGui.QIcon(os.path.join(GUI_auxiliary.INSTALLATION_FOLDER, "media/proton_logo.png"))
	simulate_dialog.setWindowIcon(icon)
	
	form_layout = QFormLayout(simulate_dialog)

	palette = QPalette()
	palette.setColor(QPalette.Window, Qt.transparent)
	
	# # Add a title to the form
	# title_layout = QHBoxLayout()
	# title_label = QLabel("<h3>Electromigration stress - transient analysis</h3>")
	# title_label.setTextFormat(Qt.RichText)
	# title_layout.addWidget(title_label)
	# title_layout.setAlignment(Qt.AlignHCenter)
	# form_layout.addRow(title_layout)

	add_space(form_layout, 3)


	print(f"JSON: {GUI_auxiliary.json_data_sim}")
	# analysis group box
	analysis_group = QGroupBox()
	analysis_group.setPalette(palette)
	analysis_group.setAutoFillBackground(True)
	analysis_layout = QFormLayout()

	# if "analysis" in GUI_auxiliary.json_data_sim and "time" in GUI_auxiliary.json_data_sim["analysis"]:
	# 	analysis_qlineedit = QLineEdit(str(GUI_auxiliary.json_data_sim["analysis"]["time"]), alignment=Qt.AlignRight)
	# else:
	# 	analysis_qlineedit = QLineEdit(alignment=Qt.AlignRight)
	# analysis_layout.addRow(QLabel("Analysis time (s) "), analysis_qlineedit)

	# method radio buttons
	Method = None
	# method_group = QButtonGroup()
	analytical_button = QRadioButton("Line Analysis")
	numerical_button = QRadioButton("Point Analysis")
	# method_group.addButton(analytical_button)
	# method_group.addButton(numerical_button)
	if "analysis" in GUI_auxiliary.json_data_sim and "method" in GUI_auxiliary.json_data_sim["analysis"]:
		if GUI_auxiliary.json_data_sim["analysis"]["method"] == "analytical":
			analytical_button.setChecked(True)
			Method = "Analytical"
		else:
			numerical_button.setChecked(True)
			Method = "Numerical"
	else:
		analytical_button.setChecked(True)
	
	method_box = QGroupBox("Type")
	method_layout = QHBoxLayout()
	
	method_layout.addWidget(analytical_button)
	method_layout.addWidget(numerical_button)
	
	method_box.setLayout(method_layout)
	analysis_layout.addRow(method_box)
	
	# analytical group box
	analytical_group = QGroupBox()
	analytical_group.setPalette(palette)
	analytical_group.setAutoFillBackground(True)
	
	# analytical_layout = QFormLayout()

	if "analysis" in GUI_auxiliary.json_data_sim and "time" in GUI_auxiliary.json_data_sim["analysis"]:
		analytical_qlineedit = QLineEdit(str(GUI_auxiliary.json_data_sim["analysis"]["time"]), alignment=Qt.AlignRight)
	else:
		analytical_qlineedit = QLineEdit(alignment=Qt.AlignRight)
	# analytical_qlineedit.setFixedWidth(30)

	analytical_time_dropdown = QComboBox()
	analytical_time_dropdown.addItem('years')
	analytical_time_dropdown.addItem('seconds')

	analytical_layout = QHBoxLayout()
	analytical_layout.addWidget(QLabel("Analysis time"))
	analytical_layout.addWidget(analytical_qlineedit)
	analytical_layout.addWidget(analytical_time_dropdown)

	analytical_group.setLayout(analytical_layout)

	# numerical subgroup
	numerical_group = QGroupBox()
	numerical_group.setPalette(palette)
	numerical_group.setAutoFillBackground(True)
	numerical_layout = QFormLayout()
	reduced_order_qlineedit = None
	if "analysis" in GUI_auxiliary.json_data_sim and "numerical" in GUI_auxiliary.json_data_sim["analysis"] and "mor" in GUI_auxiliary.json_data_sim["analysis"]["numerical"]:
	
		if "reduced order" in GUI_auxiliary.json_data_sim["analysis"]["numerical"]["mor"]:
			reduced_order_qlineedit = QLineEdit(str(GUI_auxiliary.json_data_sim["analysis"]["numerical"]["mor"]["reduced order"]), alignment=Qt.AlignRight)
	
	if "analysis" in GUI_auxiliary.json_data_sim and "time" in GUI_auxiliary.json_data_sim["analysis"]:
		numerical_qlineedit = QLineEdit(str(GUI_auxiliary.json_data_sim["analysis"]["time"]), alignment=Qt.AlignRight)
	else:
		numerical_qlineedit = QLineEdit(alignment=Qt.AlignRight)
	# numerical_qlineedit.setFixedWidth(30)

	numerical_time_dropdown = QComboBox()
	numerical_time_dropdown.addItem('years')
	numerical_time_dropdown.addItem('seconds')

	numerical_time_layout = QHBoxLayout()
	analytical_qlabel = QLabel("Analysis time")
	analytical_qlabel.setFixedWidth(110)
	numerical_time_layout.addWidget(analytical_qlabel)
	numerical_time_layout.addWidget(numerical_qlineedit)
	numerical_time_layout.addWidget(numerical_time_dropdown)

	numerical_layout.addRow(numerical_time_layout)

	# numerical_layout.addRow(QLabel("Analysis time (s) "), numerical_qlineedit)

	if "analysis" in GUI_auxiliary.json_data_sim and "numerical" in GUI_auxiliary.json_data_sim["analysis"] and "transient" in GUI_auxiliary.json_data_sim["analysis"]["numerical"] and "timestep" in GUI_auxiliary.json_data_sim["analysis"]["numerical"]["transient"]:
		timestep_qlineedit = QLineEdit(str(GUI_auxiliary.json_data_sim["analysis"]["numerical"]["transient"]["timestep"]), alignment=Qt.AlignRight)
	else:
		timestep_qlineedit = QLineEdit(alignment=Qt.AlignRight)

	numerical_timestep_dropdown = QComboBox()
	numerical_timestep_dropdown.addItem('years')
	numerical_timestep_dropdown.addItem('seconds')

	numerical_timestep_layout = QHBoxLayout()
	numerical_qlabel = QLabel("Timestep")
	numerical_qlabel.setFixedWidth(110)
	numerical_timestep_layout.addWidget(numerical_qlabel)
	numerical_timestep_layout.addWidget(timestep_qlineedit)
	numerical_timestep_layout.addWidget(numerical_timestep_dropdown)

	numerical_layout.addRow(numerical_timestep_layout)

	# numerical_layout.addRow(QLabel("Timestep (s) "), timestep_qlineedit)

	add_space(numerical_layout, 6)

	# Create the checkbox or radiobutton MOR
	mor_checkbox = QCheckBox("Model Order Reduction (MOR)")
	# Add it to the numerical_group using numerical_layout
	numerical_layout.addRow(mor_checkbox)
	
	if not reduced_order_qlineedit:
		reduced_order_qlineedit = QLineEdit(alignment=Qt.AlignRight)
	
	reduced_order_label = QLabel("Reduced Order")
	reduced_order_label.setFixedWidth(110)
	numerical_layout.addRow(reduced_order_label, reduced_order_qlineedit)

	reduced_order_label.setVisible(mor_checkbox.isChecked())
	reduced_order_qlineedit.setVisible(mor_checkbox.isChecked())

	def show_hide_mor_fields(state):
		if state:
			reduced_order_label.show()
			reduced_order_qlineedit.show()
		else:
			reduced_order_label.hide()
			reduced_order_qlineedit.hide()
			
	mor_checkbox.toggled.connect(show_hide_mor_fields)

	numerical_group.setLayout(numerical_layout)
	analysis_group.setLayout(analysis_layout)
	form_layout.addRow(analysis_group)

	analysis_layout.addRow(numerical_group)
	numerical_group.setVisible(not analytical_button.isChecked())
	numerical_button.toggled.connect(analytical_group.setHidden)

	analysis_layout.addRow(analytical_group)
	analytical_group.setVisible(analytical_button.isChecked())
	analytical_button.toggled.connect(numerical_group.setHidden)
	
	# add_line(form_layout)
	add_space(form_layout, 5)

	# Add the done & cancel buttons
	button_layout = QHBoxLayout()

	# done_button = QPushButton("Done")
	# button_layout.addWidget(done_button)

	simulate_button = QPushButton("Simulate")
	simulate_button.setDefault(True)
	button_layout.addWidget(simulate_button)
	#simulate_button.clicked.connect(lambda: add_plot(analytical_button.isChecked()))

	# if analytical_button.isChecked():
	# 	simulate_button.clicked.connect(lambda: GUI_auxiliary.analytical_function(analytical_qlineedit.text()))
	# else:
	# 	simulate_button.clicked.connect(lambda: GUI_auxiliary.transient_function()) #numerical_qlineedit.text()))

	simulate_button.clicked.connect(simulate_dialog.accept)

	simulate_button.clicked.connect(lambda: GUI_auxiliary.analytical_wrapper(analytical_qlineedit.text(), analytical_time_dropdown.currentText()) 
				 if analytical_button.isChecked() 
				 else GUI_auxiliary.transient_function(sim_time=numerical_qlineedit.text(),
					   timestep=timestep_qlineedit.text(), 
					#	is_via=monitor_point_layout.itemAt(0).widget().isChecked(),
					#	via_point=via_point_selection.currentText(),
					#	internal_point=internal_point_qlineedit.text(),
					   mor_enabled=mor_checkbox.isChecked(), reduced_order=reduced_order_qlineedit.text(),
					   time_measuring=numerical_time_dropdown.currentText(), timestep_measuring=numerical_timestep_dropdown.currentText()))
	
	cancel_button = QPushButton("Cancel", simulate_dialog)
	cancel_button.clicked.connect(simulate_dialog.reject)
	button_layout.addWidget(cancel_button)
	

	button_layout.setAlignment(Qt.AlignHCenter)
	form_layout.addRow(button_layout)

	simulate_dialog.adjustSize()
	simulate_dialog.exec_()

def update_lines(lines_dropdown, lines_list):
	lines_dropdown.clear()
	lines_dropdown.addItems(lines_list)

def get_times_for_analytical_line(analytical_lines, line):
	times_list = []
	print(analytical_lines)
	if analytical_lines:
		for time in analytical_lines[line]:
			times_list.append(f"{time:.2f}")
	return times_list

def change_time_dropdown(time_dropdown, analytical_lines, is_analytical, line):
	if is_analytical and line:
		time_dropdown.clear()
		times_list = []
		if analytical_lines:
			if line in analytical_lines:
				times_list = get_times_for_analytical_line(analytical_lines, line)
			else:
				times_list = get_times_for_analytical_line(analytical_lines, list(analytical_lines)[0])
		time_dropdown.addItems(times_list)


def plot_dialog_window(window):
	print("hello from plot widow")
	plot_dialog = QDialog()
	plot_dialog.setWindowTitle("Plot results")
	icon = QtGui.QIcon(os.path.join(GUI_auxiliary.INSTALLATION_FOLDER, "media/proton_logo.png"))
	plot_dialog.setWindowIcon(icon)
	form_layout = QFormLayout(plot_dialog)

	# Find all the available simulated lines 
	GUI_auxiliary.directory = os.path.normpath(GUI_auxiliary.directory)
	print(GUI_auxiliary.directory)
	simulated_lines_folder = os.path.join(GUI_auxiliary.directory,"output")

	lines = []
	transient_lines = {}
	analytical_lines = {}
	print(f'simulated_lines_folder: {simulated_lines_folder}')
	if os.path.exists(simulated_lines_folder):
		for item in os.listdir(simulated_lines_folder):
			item_path = os.path.join(simulated_lines_folder, item)
			print(f"item_path: {item_path}")
			stress_pattern = r"stress_([\d.]+)\."
			for technology in os.listdir(item_path):
				# Going to find all analytical lines
				print(f'Line with technology: {os.path.join(item_path,technology)}')
				for filename in os.listdir(os.path.join(item_path,technology)):
					print(f"\nFilename: {filename}")
					if filename.endswith(".txt") and filename.startswith("stress"):
						match = re.search(stress_pattern, filename)
						print(f"match: {match.group(1)}")
						if match:
							data = (match.group(1), os.path.join(os.path.join(item_path,technology), filename))
							line_w_tech = item + " - " + technology.split("_")[0] + " " + technology.split("_")[1] + " " + technology.split("_")[2]
							if line_w_tech not in analytical_lines:
								analytical_lines[line_w_tech] = {float(match.group(1)):(os.path.join(os.path.join(item_path,technology), filename))}
							else:
								analytical_lines[line_w_tech][float(match.group(1))] = (os.path.join(os.path.join(item_path,technology), filename))

				# Going to find all transient lines
				print(f"Going to check if {os.path.join(item_path+'/transient/', technology)} exists.")
				technology_path = os.path.join(item_path, technology)
				print(f'Path to check:{os.path.join(technology_path, "transient")}')
				transient_path = os.path.join(technology_path, "transient")
				if os.path.exists(transient_path):
					line_w_tech = item + " - " + technology.split("_")[0] + " " + technology.split("_")[1] + " " + technology.split("_")[2]
					if os.path.exists(os.path.join(transient_path, "original")):
						files_path = os.path.join(transient_path, "original")
						is_rom = False
					else:
						files_path = os.path.join(transient_path, "reduced")
						is_rom = True
					
					with open(os.path.join(files_path, 'simulation_time.txt'), 'r') as time_file:
						time_lines = time_file.readlines()
					print(f"Timestep: {float(time_lines[1].split()[0])}")
					print(f"Sim time: {float(time_lines[-1].split()[0])}")

					data = (float(time_lines[1].split()[0]), float(time_lines[-1].split()[0]), transient_path, is_rom)
					transient_lines[line_w_tech] = data
			if os.path.isdir(item_path):
				lines.append(item)
	print(f"Simulated lines: {lines}")
	print(f"analytical lines: {analytical_lines}")
	print(f"transient lines: {transient_lines}")


	analytical_button = QRadioButton("Line Analysis")
	analytical_button.setChecked(True)
	numerical_button = QRadioButton("Point Analysis")

	method_box = QGroupBox("Type")
	method_layout = QHBoxLayout()
	
	method_layout.addWidget(analytical_button)
	method_layout.addWidget(numerical_button)
	
	analytical_button.toggled.connect(lambda _: update_lines(lines_dropdown, list(analytical_lines.keys())))
	analytical_button.toggled.connect(lambda _: time_label.setVisible(True))
	analytical_button.toggled.connect(lambda _: time_dropdown.setVisible(True))

	numerical_button.toggled.connect(lambda _: update_lines(lines_dropdown, list(transient_lines.keys())))
	numerical_button.toggled.connect(lambda _: time_label.setVisible(False))
	numerical_button.toggled.connect(lambda _: time_dropdown.setVisible(False))
	method_box.setLayout(method_layout)
	form_layout.addRow(method_box)

	lines_layout = QFormLayout()

	lines_dropdown = QComboBox()
	lines_dropdown.addItems(list(analytical_lines.keys()))
	lines_dropdown.currentTextChanged.connect(lambda line: change_time_dropdown(time_dropdown, analytical_lines, analytical_button.isChecked(), line))
	lines_layout.addRow(QLabel("Lines:"), lines_dropdown)

	time_label = QLabel("Time (s):")
	time_dropdown = QComboBox()
	time_list = get_times_for_analytical_line(analytical_lines, lines_dropdown.currentText())
	time_dropdown.addItems(time_list)
	lines_layout.addRow(time_label, time_dropdown)
	
	
	palette = QPalette()
	palette.setColor(QPalette.Window, Qt.transparent)
	lines_group = QGroupBox()
	lines_group.setPalette(palette)
	lines_group.setAutoFillBackground(True)
	lines_group.setLayout(lines_layout)
	form_layout.addRow(lines_group)


	# Add the done & cancel buttons
	button_layout = QHBoxLayout()

	plot_button = QPushButton("Plot")
	button_layout.addWidget(plot_button)
	plot_button.setDefault(True)

	plot_button.clicked.connect(plot_dialog.accept) # We need this so that the dialog closes
	plot_button.clicked.connect(lambda _:GUI_auxiliary.plot_result(
		analytical_button.isChecked(), 
		lines_dropdown.currentText(), 
		(analytical_lines[lines_dropdown.currentText()][float(time_dropdown.currentText())] if analytical_lines else None) if analytical_button.isChecked() else transient_lines[lines_dropdown.currentText()], 
		time_dropdown))

	cancel_button = QPushButton("Cancel", plot_dialog)
	# cancel_button.setDefault(False)
	cancel_button.clicked.connect(plot_dialog.reject)
	button_layout.addWidget(cancel_button)
	

	button_layout.setAlignment(Qt.AlignHCenter)
	form_layout.addRow(button_layout)

	plot_dialog.adjustSize()
	plot_dialog.exec_()

def new_open_menu_button(window, mode):
	global MAIN_WINDOW_FLAG

	# print(f"MAIN_WINDOW_FLAG: {MAIN_WINDOW_FLAG}")
	if MAIN_WINDOW_FLAG:
		result = QMessageBox.question(window, ' ', "Are you sure you want to close the current project without saving?", 
			QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		if result == QMessageBox.Yes:
			MAIN_WINDOW_FLAG = False
			#print("ha ha")
			#window.setMinimumSize(550,300)
			window.setMinimumWidth(550)
			if mode == "open":
				height = 200
			else:
				height = 230

			GUI_auxiliary.close_layout(GUI_auxiliary.plot_layout)
			window.setMinimumHeight(height)
			window.resize(550,height)
			menu.clear()
			GUI_auxiliary.SELECTED_LINE = ""
			create_open_project_form(window, mode)
	else:
		create_open_project_form(window, mode)

class HelpMenu(QMainWindow):
	def __init__(self):
		super().__init__()

		self.setWindowTitle("Help Menu")
		self.setGeometry(100, 100, 800, 600)
		icon = QtGui.QIcon(os.path.join(GUI_auxiliary.INSTALLATION_FOLDER, "media/proton_logo.png"))
		self.setWindowIcon(icon)
	

		self.create_help_browser()
		self.create_menu()
		self.show_table_of_contents()

	def create_help_browser(self):
		self.help_browser = QWebEngineView(self)
		self.setCentralWidget(self.help_browser)
		# directory = 'documentation/help/'
		# QDir.setCurrent(directory)

	def create_menu(self):
		menubar = QMenuBar(self)

		help_menu = menubar.addMenu("Help")

		# Add a table of contents action
		toc_action = QAction("Home", self)
		toc_action.triggered.connect(self.show_table_of_contents)
		help_menu.addAction(toc_action)

		# Set the menu bar
		self.setMenuBar(menubar)

	def show_table_of_contents(self):
		file_path = os.path.abspath("documentation/help/help.html")
		self.help_browser.load(QUrl.fromLocalFile(file_path))

def create_menu(window, isProject):
	global menu
	menu = window.menuBar()
	
	# File menu
	file_menu = menu.addMenu("File")

	new_action = QAction("New", window)
	new_action.triggered.connect(lambda: new_open_menu_button(window, "new"))
	file_menu.addAction(new_action)

	open_action = QAction("Open", window)
	open_action.triggered.connect(lambda: new_open_menu_button(window, "open"))
	file_menu.addAction(open_action)

	save_action = QAction("Save", window)
	save_action.triggered.connect(lambda: on_save_action())
	file_menu.addAction(save_action)

	# save_as_action = QAction("Save as", window)
	# file_menu.addAction(save_as_action)

	exit_action = QAction("Exit", window)
	exit_action.triggered.connect(lambda: exit_app(window))
	file_menu.addAction(exit_action)

	# Tools menu
	#tools_menu = menu.addMenu("Import")
	#import_config_action = QAction("Configuration file", window)
	#tools_menu.addAction(import_config_action)

	simulate_action = QAction("Simulate", window)
	simulate_action.triggered.connect(lambda: simulate(window))
	menu.addAction(simulate_action)
	# simulate_action.setEnabled(isProject)

	PLOT_MENU = True
	if PLOT_MENU:
		plot_action = QAction("Plot results", window)
		plot_action.triggered.connect(lambda: plot_dialog_window(window))
		menu.addAction(plot_action)
		# plot_action.setEnabled(isProject)

	export_action = QAction("Export Data", window)
	export_action.triggered.connect(lambda: export_data(window))
	menu.addAction(export_action)
	# export_action.setEnabled(isProject)


	# Help menu
	help_menu = menu.addMenu("Help")
	
	about_action = QAction("About", window)
	about_action.triggered.connect(lambda: help_dialog.show())
	help_menu.addAction(about_action)
	help_dialog = HelpMenu()
	

# # # # # # # # # 
#  MAIN WINDOW 
# 

# # # # # # # # # 
#  MAIN WINDOW - LEFT FRAME
# 

def create_left_frame(h_splitter, right_frame_v_splitter):
	global app
	# Create the left side of the horizontal splitter
	left_frame = QFrame()
	screen = app.primaryScreen()
	size = screen.size()	
	left_frame.setMinimumWidth(LEFT_FRAME_WIDTH if LEFT_FRAME_WIDTH <= int(0.2*size.width()) else int(0.2*size.width()))
	left_frame.setMaximumWidth(400)
	# left_frame.setGeometry(left_frame.x(), left_frame.y(), 350, left_frame.height())
	left_frame.setFrameShape(QFrame.StyledPanel)
	# left_frame.setLineWidth(1)
	left_frame.setAutoFillBackground(True)
	# left_frame.setPalette(QColor(200, 200, 200))
	# left_frame.setStyleSheet("background-color: white;")

	# Create the vertical splitter for the left side
	v_splitter = QSplitter(Qt.Vertical)
	v_splitter.setHandleWidth(1)
	v_splitter.setStyleSheet("QSplitter::handle { background-color: gray; }")


	#-----------------------------------------------------------#

	# Create the upper side of the vertical splitter
	upper_frame = QFrame()
	upper_frame.setFrameShape(QFrame.NoFrame)
	# upper_frame.setLineWidth(2)
	#upper_frame.setMinimumHeight(70)
	# upper_frame.setFixedHeight(380)
	upper_frame.setAutoFillBackground(True)

	layout = QVBoxLayout()
	upper_frame.setLayout(layout)

	# The title of the label
	title_label = QLabel()
	title_label.setAutoFillBackground(True)
	# title_label.setStyleSheet("background-color: rgb(255,0,255);")
	create_label_text(title_label, "<h4>Configuration</h4>", "border: none; color: #444444;", alignment=None)
	title_label.setMaximumHeight(30)
	layout.addWidget(title_label)

	# add here configuration
	
	path_to_config = GUI_auxiliary.directory + "/config.json"
	form_layout = create_form(path_to_config)

	# Add the form layout to the widget
	form_widget = QWidget()
	form_widget.setLayout(form_layout)
	layout.addWidget(form_widget)

	# upper_frame.setMaximumHeight(430)

	v_splitter.addWidget(upper_frame)
	#----------------------------------------------------#
	# Create the lower side of the vertical splitter
	lower_frame = QFrame()
	#lower_frame.setMinimumHeight(500)
	lower_frame.setFrameShape(QFrame.NoFrame)
	lower_frame.setLineWidth(2)
	lower_frame.setAutoFillBackground(True)
	
	
	# lower_frame.setStyleSheet("background-color: rgb(100, 100, 100);")
	# lower_frame.setStyleSheet("padding:1px;border: 1px solid #888888;")

	layout_lower = QVBoxLayout()
	layout_lower.setAlignment(Qt.AlignTop)
	lower_frame.setLayout(layout_lower)

	# The title of the label
	title_label = QLabel()
	title_label.setAutoFillBackground(True)
	# title_label.setStyleSheet("background-color: rgb(255,0,255);")
	create_label_text(title_label, "<h4>Power Grid</h4>", "border: none; color: #444444;", alignment=None)
	title_label.setMaximumHeight(30)
	layout_lower.addWidget(title_label)

	# -alex
	# folder_path = r'/home/atakou/Documents/GitHub/EM_analysis_tool/ibmpg1' # Enter the path of the folder you want to display
	#folder_path = r'ibmpg1' # Enter the path of the folder you want to display
	folder_path = spice_function.benchmark 
	if len(POWERGRID_LOCATION) > 0:
		tree = create_powergrid_tree(folder_path, right_frame_v_splitter)
		layout_lower.addWidget(tree)
	# layout.setAlignment(tree, Qt.AlignTop | Qt.AlignLeft)

	v_splitter.addWidget(lower_frame)
	#-------------------------------------------------------#

	# Add the vertical splitter to the left side of the horizontal splitter
	left_frame.setLayout(QVBoxLayout())
	# left_frame.layout().addWidget(left_frame)

	h_splitter.insertWidget(0, v_splitter)

	# Set the upper side to be one third of the lower side's height
	#v_splitter.setSizes([1, 3])
	v_splitter.setStretchFactor(0, 1)
	v_splitter.setStretchFactor(1, 5)

# # # # # # # # # 
#  MAIN WINDOW - RIGHT FRAME
# 

def create_right_frame(h_splitter):	
	global app
	# Create the right side of the horizontal splitter
	right_frame = QFrame()
	screen = app.primaryScreen()
	size = screen.size()
	right_frame.setMinimumWidth(RIGHT_FRAME_WIDTH if RIGHT_FRAME_WIDTH <= int(0.6*size.width()) else int(0.6*size.width()))
	right_frame.setFrameShape(QFrame.StyledPanel)
	right_frame.setLineWidth(2)
	right_frame.setAutoFillBackground(True)
	# right_frame.setPalette(QColor(250, 250, 250))
	# right_frame.setStyleSheet("background-color: rgb(255, 255, 255);") # THE DESTROYER STYLESHEET
	h_splitter.insertWidget(0, right_frame)

	# Create the vertical splitter for the right side
	v_splitter = QSplitter(Qt.Vertical)
	v_splitter.setHandleWidth(1)
	v_splitter.setStyleSheet("QSplitter::handle { background-color: gray; }")

	# Create the three panels for the right side
	create_main_plot_panel(v_splitter)
	create_analytics_panel(v_splitter)

	v_splitter.setSizes([1, 3, 1])

	# Add the vertical splitter to the right side of the horizontal splitter
	right_frame.setLayout(QVBoxLayout())
	right_frame.layout().addWidget(v_splitter)

	return v_splitter


def create_main_window(window, PROJECT_NAME, project_type, elapsed_time=None):
	global MAIN_WINDOW_FLAG
	
	MAIN_WINDOW_FLAG = True
	
	# print(f"project name: {PROJECT_NAME}")
	if PROJECT_NAME == "":
		window.setWindowTitle(f"PROTON")
	else:
		window.setWindowTitle(f"PROTON - {os.path.normpath(PROJECT_NAME)}")
	
	create_menu(window, True) 
	# Create the horizontal splitter
	h_splitter = QSplitter(Qt.Horizontal)
	h_splitter.setHandleWidth(1)
	# h_splitter.setStyleSheet("QSplitter::handle { background-color: gray; }")
	right_frame_v_splitter = create_right_frame(h_splitter)
	GUI_auxiliary.right_frame_v_splitter = right_frame_v_splitter

	#print("----> ", right_frame_v_splitter)
	create_left_frame(h_splitter, right_frame_v_splitter)

	if project_type == "new":
		message = "Created new project with name " + os.path.normcase(PROJECT_NAME)
		GUI_auxiliary.log_keeper.track_history_messages(message, False)
		message = f"Parsed spice file with name {os.path.normcase(GUI_auxiliary.spice_file)} in {elapsed_time:.3f} seconds." 

	else:
		message = "Opened the project with name " + os.path.normcase(PROJECT_NAME)
	GUI_auxiliary.log_keeper.track_history_messages(message, False)


	
	# Set the left side to be one fourth of the right side's width
	h_splitter.setSizes([1, 5])
	# h_splitter.setStretchFactor(0, 1)
	# h_splitter.setStretchFactor(1, 5)

	if window.size().height() < MIN_MAIN_WINDOW_SIZE[0] or window.size().width() < MIN_MAIN_WINDOW_SIZE[1]:
		#print("Changed the size of the window")
		window.resize(QSize(MIN_MAIN_WINDOW_SIZE[0],MIN_MAIN_WINDOW_SIZE[1]))
		window.move(250,40)
	#window.setMinimumSize(QSize(MIN_MAIN_WINDOW_SIZE[0],MIN_MAIN_WINDOW_SIZE[1]))

	# Set the main window's central widget
	window.setCentralWidget(h_splitter)

# # # # # # # # # 
#  NEW PROJECT WINDOW 
# 

def delete_spice_parser_thread():
	global spice_parser_worker, spice_parser_thread
	spice_parser_worker = None
	spice_parser_thread = None

def extract_number_between(string, start_word, end_word):
	pattern = rf"{re.escape(start_word)}\s+(\d+(\.\d+)?)\s+{re.escape(end_word)}"
	match = re.search(pattern, string)
	
	if match:
		return float(match.group(1))
	else:
		return None

def handle_spice_parser_messages(return_message, window, form_widget, project_name, project_location, spice_file, benchmark):
	exec_time = None
	if "seconds" in return_message:
		generate_popup_message(f'Spice file was successfully parsed {return_message}.','info')

		save_project_details(project_name, project_location, spice_file, benchmark)
		save_config_file( False)

		# Hide the previous layout and delete its widgets 
		if form_widget is not None:
			form_widget.hide()
			remove_children(form_widget)
		# Call the function for the new layout
		exec_time = extract_number_between(return_message, "in", "seconds")
		if exec_time is not None:
			if window is not None:
				create_main_window(window, GUI_auxiliary.directory, "new", exec_time)

	if "seconds" not in return_message or exec_time is None:
		if "seconds" in return_message and exec_time is None:
			return_message = "An error occured while parsing the parsing execution time."
		generate_popup_message(return_message,'error')
		print(f"Going to delete project {GUI_auxiliary.directory}...")
		shutil.rmtree(GUI_auxiliary.directory)
		create_open_project_form(window, "both")

def new_change_window(window, form_widget, buttons, project_name_entry, project_location_entry, spice_file_entry):
	global spice_parser_worker, spice_parser_thread

	if (window is not None and project_name_entry.text() and project_location_entry.text() and spice_file_entry.text()) or (window is None and project_name_entry and project_location_entry and spice_file_entry):
		# -alex
		# Create the folder for the project 
		if window is not None:
			GUI_auxiliary.directory = project_location_entry.text()
			GUI_auxiliary.spice_file = spice_file_entry.text()
		else:
			GUI_auxiliary.directory = project_location_entry
			GUI_auxiliary.spice_file = spice_file_entry

		if not os.path.exists(GUI_auxiliary.directory):
			os.mkdir(GUI_auxiliary.directory)
		if window is not None:
			PROJECT_NAME = os.path.join(GUI_auxiliary.directory, project_name_entry.text() )
		else:
			PROJECT_NAME = os.path.join(GUI_auxiliary.directory, project_name_entry)
		try:
			os.mkdir(PROJECT_NAME, 0o777)
		except:
			if window is not None:
				generate_popup_message(f"\'{project_name_entry.text()}\' project exists already. Choose a different path or project name.", "error")
				return
			else:
				return(f"\'{project_name_entry}\' project exists already. Choose a different path or project name.")
		
		#-----------------------------------------------------#
		GUI_auxiliary.directory = PROJECT_NAME

		message_log_path = PROJECT_NAME + "/history_log.txt"
		open(message_log_path, "x")
		
		for button in buttons:
			button.setEnabled(False)

		if window is not None:
			project_name_entry.setEnabled(False)
			spice_file_entry.setEnabled(False)
			project_location_entry.setEnabled(False)
		# # # # # # THREAD # # # # # # # #

		if spice_parser_thread:
			spice_parser_worker = None
			spice_parser_thread.quit()
			spice_parser_thread.wait()
			spice_parser_thread = None

		spice_parser_worker = Spice_Parser_Class(GUI_auxiliary.spice_file,GUI_auxiliary.directory, GUI_auxiliary.IS_LINUX, GUI_auxiliary.INSTALLATION_FOLDER)

		# Create thread and assign it to worker
		spice_parser_thread = QThread()
		spice_parser_worker.moveToThread(spice_parser_thread)

		# Run the desired function
		spice_parser_thread.started.connect(spice_parser_worker.spice_parser)

		# Destroy both thread and worker when job is done
		if window is not None:
			spice_parser_worker.return_message.connect(lambda return_message: handle_spice_parser_messages(return_message, window, form_widget, project_name_entry.text(), project_location_entry.text(), spice_file_entry.text(), spice_function.benchmark))
		else:
			spice_parser_worker.return_message.connect(lambda return_message: handle_spice_parser_messages(return_message, window, form_widget, project_name_entry, project_location_entry, spice_file_entry, spice_function.benchmark))
		spice_parser_worker.finished.connect(spice_parser_thread.quit)
		spice_parser_worker.finished.connect(spice_parser_thread.wait)
		# spice_parser_worker.finished.connect(spice_parser_worker.deleteLater)
		# spice_parser_thread.finished.connect(spice_parser_thread.deleteLater)
		spice_parser_worker.finished.connect(delete_spice_parser_thread)

		# discr_button.setEnabled(False)
		# spice_parser_worker.finished.connect(lambda: discr_button.setEnabled(True))

		if window is not None:
			loading_screen = LoadingIcon(window)
			# loading_screen.move(int(window.width() // 2 - loading_screen.width() // 3), int(window.height() // 2 - loading_screen.height()// 3))
			loading_screen.move(int(window.width() // 2 - loading_screen.width() // 1.95), int(window.height() // 2 - loading_screen.height()// 4.5))
			spice_parser_worker.finished.connect(lambda: loading_screen.stopAnimation())

		# Start the thread
		spice_parser_thread.start()
		print("Reached here")

		if window is not None:
			return("Success!")
		# # # # # # # # # # # # # #

	else:
		# Fields are not filled, show error message
		generate_popup_message("All fields are required.", "error") #-alex 19/03
		

def open_change_window(window, form_widget,  project_location_entry):
	#global PROJECT_NAME

	if project_location_entry.text():

		# Check if the given dir is a PROTON project
		PROJECT_NAME = project_location_entry.text()
		temp_path_to_json = PROJECT_NAME + "/" + "PROTON_project_details.json" 
		checkExists =os.path.exists(temp_path_to_json)
		
		if checkExists == False:
			generate_popup_message("The given location isn't a PROTON project. Try again.", "error")
			return

		
		#temp_path_to_json = PROJECT_NAME + "/" + "PROTON_project_details.json" 
		with open(temp_path_to_json, "r") as fd:
			details_json = json.load(fd)

		if "magic_word" not in details_json or details_json["magic_word"] != "papaya56":
			generate_popup_message("The given location isn't a PROTON project. Try again.", "error")
			return
		#print(details_json)
		GUI_auxiliary.directory = details_json["full_path_to_project"]
		GUI_auxiliary.spice_file = details_json["spice_path"]
		spice_function.benchmark = details_json["parsed_spice_path"]
		# Hide the previous layout and delete its widgets 
		form_widget.hide()
		remove_children(form_widget)

		message_log_path = os.path.exists(os.path.join(GUI_auxiliary.directory+ "/history_log.txt"))
		path_to_stastitics = os.path.exists(os.path.join(GUI_auxiliary.directory + "/statistics/Statistics.csv"))
		path_to_config = os.path.exists(os.path.join(GUI_auxiliary.directory + "/config.json"))

		print(f'{os.path.join(GUI_auxiliary.directory+ "/history_log.txt")}: {message_log_path}')
		print(f'{os.path.join(GUI_auxiliary.directory+ "/statistics/Statistics.csv")}: {path_to_stastitics}')
		print(f'{os.path.join(GUI_auxiliary.directory+ "/config.json")}: {path_to_config}')
		if os.path.normpath(PROJECT_NAME) != os.path.normpath(GUI_auxiliary.directory) or not message_log_path or not path_to_stastitics or not path_to_config or not os.path.exists(spice_function.benchmark ):
			message = "The given PROTON project is corrupted. Try again."
			if os.path.normpath(PROJECT_NAME) != os.path.normpath(GUI_auxiliary.directory):
				message = f"The given PROTON was initially created at location {GUI_auxiliary.directory} but it is instead at {PROJECT_NAME}. Try recreating the project."
			generate_popup_message(message, "error")
			return

		# Call the function for the new layout
		create_main_window(window, PROJECT_NAME, "open")
	else:
		# Fields are not filled, show error message
		generate_popup_message("All fields are required.", "error") #-alex 19/03
		


def create_open_project_form(window, mode):
	# Create the layout manager and add the label widget to the layout
	vbox = QVBoxLayout()
	#new_project_form(window, vbox)
	margin_value = 15
	vbox.setSpacing(10)

	if mode == "both" or mode == "new":
		#------- NEW PROJECT GUI SUB-WINDOW START -------#
		
			# Create the new project form layout
		new_form_layout = QFormLayout()
		new_form_layout.setContentsMargins(2 * margin_value, margin_value, 2 * margin_value, margin_value)
			#-----------------------------------#

			# Add a title to the new project form
		new_title_layout = QHBoxLayout()
		
		new_title_label = QLabel("<h2>New Project</h2>")
		new_title_label.setTextFormat(Qt.RichText)

		new_title_layout.addWidget(new_title_label)
		new_title_layout.setAlignment(Qt.AlignHCenter)

		new_form_layout.addRow(new_title_layout)
		add_space(new_form_layout, 5)
			#-----------------------------------#

			# Add the new project form entries
		new_project_name_label = QLabel("Project name:")
		new_project_name_entry = QLineEdit()
		new_form_layout.addRow(new_project_name_label, new_project_name_entry)

		
		new_project_location_label = QLabel("Project location:")
		new_project_location_entry = QLineEdit()
		#new_project_location_entry.setFixedWidth(260)
		new_project_location_entry.setMinimumWidth(260)

		browse_new_location_button = QPushButton("...")
		browse_new_location_button.setFixedWidth(40)

		new_project_location_layout = QHBoxLayout()
		new_project_location_layout.addWidget(new_project_location_entry)
		new_project_location_layout.addWidget(browse_new_location_button)
		new_form_layout.addRow(new_project_location_label, new_project_location_layout)

		new_spice_file_label = QLabel("SPICE file:")
		new_spice_file_entry = QLineEdit() 
		#new_spice_file_entry.setFixedWidth(260)
		new_spice_file_entry.setMinimumWidth(260)

		browse_new_spice_button = QPushButton("...")
		browse_new_spice_button.setFixedWidth(40)
		
		new_spice_file_layout = QHBoxLayout()
		new_spice_file_layout.addWidget(new_spice_file_entry)
		new_spice_file_layout.addWidget(browse_new_spice_button)
		new_form_layout.addRow(new_spice_file_label, new_spice_file_layout)
			#--------------------------------------------#

		add_space(new_form_layout, 5)
		
			# Add the done button
		done_top_button = QPushButton("Done")
		done_top_button.setFixedWidth(150)
		# metrics = QtGui.QFontMetrics(done_button.font())
		# text_width = metrics.width(done_button.text())

		top_button_layout = QHBoxLayout()
		top_button_layout.addWidget(done_top_button)
		top_button_layout.setAlignment(Qt.AlignHCenter)
		new_form_layout.addRow(top_button_layout)
			#-------------------------#
		
		#new_form_layout.setSizeConstraint(QLayout.SetFixedSize)
		
			# Add the form layout to the widget
		new_form_widget = QWidget()
		new_form_widget.setLayout(new_form_layout)

			# Add the background
		new_form_widget.setAutoFillBackground(True)
		top_palette = new_form_widget.palette()
		top_palette.setColor(new_form_widget.backgroundRole(), QtGui.QColor("white"))
		new_form_widget.setPalette(top_palette)



			#New Project Buttons actions
		browse_new_location_button.clicked.connect(lambda: browse_location(window, new_project_location_entry))
		browse_new_spice_button.clicked.connect(lambda:browse_spice(window, new_spice_file_entry))

		if mode == "both":
			done_top_button.clicked.connect(lambda:new_change_window(window, new_form_widget, [done_top_button, browse_new_spice_button, browse_new_location_button, done_bottom_button, open_project_location_entry, browse_open_location_button], new_project_name_entry, new_project_location_entry, new_spice_file_entry))
		else:
			done_top_button.clicked.connect(lambda:new_change_window(window, new_form_widget, [done_top_button, browse_new_spice_button, browse_new_location_button], new_project_name_entry, new_project_location_entry, new_spice_file_entry))
		
			
		#------- NEW PROJECT GUI SUB-WINDOW END -------#
		
		#open_project_form(window, vbox)
		vbox.addWidget(new_form_widget)

	if mode == "both" or mode == "open":
		#------- OPEN PROJECT GUI SUB-WINDOW START -------#

			#Create the open form layout
		open_form_layout = QFormLayout()
		open_form_layout.setContentsMargins(2 * margin_value, margin_value, 2 * margin_value, margin_value)

			# Add a title to the form
		open_title_layout = QHBoxLayout()
		
		open_title_label = QLabel("<h2>Open Project</h2>")
		open_title_label.setTextFormat(Qt.RichText)

		open_title_layout.addWidget(open_title_label)
		open_title_layout.setAlignment(Qt.AlignHCenter)

		open_form_layout.addRow(open_title_layout)
			#--------------------------#
		
		add_space(open_form_layout, 5)

			# Add the form to open entries
		open_project_location_label = QLabel("Project location:")

		open_project_location_entry = QLineEdit()
		#open_project_location_entry.setFixedWidth(260)
		open_project_location_entry.setMinimumWidth(260)

		browse_open_location_button = QPushButton("...")
		browse_open_location_button.setFixedWidth(40)

		open_project_location_layout = QHBoxLayout()
		open_project_location_layout.addWidget(open_project_location_entry)
		open_project_location_layout.addWidget(browse_open_location_button)

		open_form_layout.addRow(open_project_location_label, open_project_location_layout)
		
		add_space(open_form_layout, 5)
			#----------------------------#
		
			#Add the done button
		done_bottom_button = QPushButton("Done")
		done_bottom_button.setFixedWidth(150)
		# metrics = QtGui.QFontMetrics(done_button.font())
		# text_width = metrics.width(done_button.text())

		bottom_button_layout = QHBoxLayout()
		bottom_button_layout.addWidget(done_bottom_button)
		bottom_button_layout.setAlignment(Qt.AlignHCenter)

		open_form_layout.addRow(bottom_button_layout)
			#------------------------------------#


			# Add the form layout to the widget
		#open_form_layout.setSizeConstraint(QLayout.SetFixedSize)

		open_form_widget = QWidget()
		open_form_widget.setLayout(open_form_layout)

		open_form_widget.setAutoFillBackground(True)
		open_pallete = open_form_widget.palette()
		open_pallete.setColor(open_form_widget.backgroundRole(), QtGui.QColor("white"))

		open_form_widget.setPalette(open_pallete)

		browse_open_location_button.clicked.connect(lambda: browse_location(window, open_project_location_entry))
		done_bottom_button.clicked.connect(lambda: open_change_window(window, open_form_widget, open_project_location_entry))
		#------- OPEN PROJECT GUI SUB-WINDOW END -------#
		
		vbox.addWidget(open_form_widget)

	vbox.setAlignment(Qt.AlignTop)
	#---------------------------------------------------------------------#
	# Create a wrapper widget that is going to include the layout manager
	central_widget = QWidget()
	# Assign the layout to the new widget
	central_widget.setLayout(vbox)
	

	# Add the widget to the main layout
	window.setCentralWidget(central_widget)
	window.setWindowTitle("PROTON")



# # # # # # # # # 
#  BASIC GUI CODE
# 
def create_window(cli_flag=False, directory=None):
	window = QMainWindow()
	# window.setMinimumSize(400,100)
	window.setWindowTitle("PROTON - New Project")
	# Set the window icon
	icon = QtGui.QIcon(os.path.join(GUI_auxiliary.INSTALLATION_FOLDER, "media/proton_logo.png"))
	# icon = QtGui.QIcon.fromTheme("document-new")
	window.setWindowIcon(icon)
	
	if cli_flag:
		temp_path_to_json = directory + "/" + "PROTON_project_details.json" 
		with open(temp_path_to_json, "r") as fd:
			details_json = json.load(fd)

		if "magic_word" not in details_json or details_json["magic_word"] != "papaya56":
			generate_popup_message("The given location isn't a PROTON project. Try again.", "error")
			return
		#print(details_json)
		GUI_auxiliary.directory = details_json["full_path_to_project"]
		GUI_auxiliary.spice_file = details_json["spice_path"]
		spice_function.benchmark = details_json["parsed_spice_path"]

		create_main_window(window, directory, "open")
	else:
		create_open_project_form(window, "both")
	#create_main_window(window)
	return window

def on_closing(event):
	global MAIN_WINDOW_FLAG, spice_parser_thread, spice_parser_worker

	if MAIN_WINDOW_FLAG or spice_parser_thread is not None:
		# Confirm if the user really wants to close the window
		reply = QMessageBox.question(None, "Confirm Exit",
									"Are you sure you want to exit?",
									QMessageBox.Yes | QMessageBox.No,
									QMessageBox.No)
		if reply == QMessageBox.Yes:
			# Save any unsaved changes or perform any cleanup before exiting
			#print("we save log and qutiing")
			if MAIN_WINDOW_FLAG:
				on_save_action()
				GUI_auxiliary.log_keeper.save_history_log(True)
			else:
				spice_parser_worker.request_interruption()
				spice_parser_thread.quit()
				spice_parser_worker = None
				spice_parser_thread = None
				print(f"Going to remove the created project directory: {GUI_auxiliary.directory}")
				shutil.rmtree(GUI_auxiliary.directory)
				
			app.quit()

		elif reply == QMessageBox.Yes and MAIN_WINDOW_FLAG == False:
			app.quit()
		else:
			event.ignore()
	else:
		app.quit()

def open_project_main(directory):
	global app
	app = QApplication(sys.argv)
	
	window = create_window(cli_flag=True, directory=directory)

	window.show()

	window.setAttribute(Qt.WA_DeleteOnClose)
	window.closeEvent = on_closing

	GUI_auxiliary.window = window

	# Activate the window and bring it to the top
	# window.setWindowFlags(Qt.Window)
	# window.activateWindow()
	# window.raise_()

	sys.exit(app.exec_())
	print("After activate")

def main():
	global app

	# log_file = open('log_file', 'w')
	# sys.stdout = log_file
	# sys.stderr = log_file
	app = QApplication(sys.argv)
	# app.setStyle("macintosh")
	
	# if not os.path.exists('installation_folder.txt'):
	# 	generate_popup_message('PROTON has not been installed yet on this system.', 'error')
	# 	sys.exit(1)
	# else:
	# 	with open('installation_folder.txt', 'r') as f:
	# 		_installation_folder = f.read()
	# 		if os.path.exists(_installation_folder) and os.path.isdir(_installation_folder):
	# 			GUI_auxiliary.INSTALLATION_FOLDER = _installation_folder

	window = create_window()

	window.show()

	window.setAttribute(Qt.WA_DeleteOnClose)
	window.closeEvent = on_closing

	GUI_auxiliary.window = window

	#quit = QAction("Quit")
	#quit.triggered.connect(lambda: closeEvent(window))

	#menubar = window.menuBar()
	#menubar.addAction(quit)
	#sys.exit(app.exec_())
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()
