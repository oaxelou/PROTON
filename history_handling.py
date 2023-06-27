import sys
import os
import json
import csv
import time
import locale
from collections import deque

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt5 import QtGui
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtGui import QPalette, QColor, QBrush



def write_message_in_log(message_log_path, message, mestype='info'):
	locale.setlocale(locale.LC_TIME, 'en_US.UTF-8') # Language always in Enghlish. Comment out for system language
	cur_time = time.localtime()
	timestamp = time.strftime("%a %d %b %Y %H:%M:%S", cur_time)
	if mestype == 'info':
		message_log_mestype = "INF"
	elif mestype == "error":
		message_log_mestype = "ERR"
	elif mestype == "success":
		message_log_mestype = "SUC"
	else:
		print(f"mestype: {mestype}")
		return
		
	message_log_string = "[" + message_log_mestype + "] " + "[" + timestamp + "] " + message + "\n"
	
	with open(message_log_path, "a") as fd:
		fd.write(message_log_string)
	

class Message_log_handling():

	def __init__(self, parent_tab, path_to_directory):
		self.PROTON_history_list = []
		self.message_log_path = path_to_directory+ "/history_log.txt"

		self.MAX_MESSAGES_TO_ENABLE_SAVE = 50
		self.MAX_LINES_TO_READ = 50

		self.ERROR_COLOR = QColor(220, 20, 60)
		self.SUCCESS_COLOR = QColor(20, 180, 20)
		self.GENERAL_COLOR = QColor(0, 0, 0)
		#-----------------------------------------------------------------------
		self.console_widget = QTableWidget()

		self.console_widget.setColumnCount(2)
		self.console_widget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
		self.console_widget.verticalHeader().setVisible(False)

		self.console_widget.setHorizontalHeaderLabels(["Date", "Message"])

		self.console_widget.horizontalHeader().setStretchLastSection(True)

		self.console_widget.setSelectionMode(QAbstractItemView.ContiguousSelection)
		self.console_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)

		#value = self.console_widget.verticalScrollBar().maximum()
		#-----------------------------------------------------------------------
		
		checkExists =os.path.exists(self.message_log_path)
		
		if checkExists == True:
			
			with open(self.message_log_path, "r") as fd:
				lines = deque(maxlen=self.MAX_LINES_TO_READ)
				for line in fd:
					lines.append(line.strip())

				for line in lines:
					temp_list = line.split("] ")
					temp_list[0] = temp_list[0][1:]
					temp_list[1] = temp_list[1][1:]
					temp_list[2] = temp_list[2]
					self.write_message_log(temp_list)

		else:
			temp_message = "The project was created"
			self.track_history_messages(temp_message, True)
		

	def get_widget(self):
		return self.console_widget

				

	def track_history_messages(self, message, save, mestype='info'):
		locale.setlocale(locale.LC_TIME, 'en_US.UTF-8') # Language always in Enghlish. Comment out for system language
		cur_time = time.localtime()
		timestamp = time.strftime("%a %d %b %Y %H:%M:%S", cur_time)
		if mestype == 'info':
			message_log_mestype = "INF"
		elif mestype == "error":
			message_log_mestype = "ERR"
		elif mestype == "success":
			message_log_mestype = "SUC"
		else:
			print(f"mestype: {mestype}")
			return
			
		message_log_string = "[" + message_log_mestype + "] " + "[" + timestamp + "] " + message + "\n"
		message_log_list = [message_log_mestype, timestamp , message]

		self.PROTON_history_list.append(message_log_string)
		self.write_message_log(message_log_list)

		if (len(self.PROTON_history_list) == 50):
			self.save_history_log(False)
		
		if (save):
			self.save_history_log(True)

	def save_history_log(self, save):
			
		num_of_messages = len(self.PROTON_history_list)
		
		with open(self.message_log_path, "a") as fd:
			for item in self.PROTON_history_list:
				fd.write(item)
		
		if num_of_messages >= self.MAX_MESSAGES_TO_ENABLE_SAVE or save:
			self.PROTON_history_list.clear()

	
	def write_message_log(self, list_to_write):

		num_line = self.console_widget.rowCount()
		self.console_widget.insertRow(num_line)

		date_item = QTableWidgetItem(list_to_write[1])
		date_item.setTextAlignment(Qt.AlignRight |Qt.AlignVCenter)

		self.console_widget.setItem(num_line, 0 ,date_item)

		self.console_widget.resizeColumnToContents(0)
		#------------------------------------------------

		message_item = QTableWidgetItem(list_to_write[2])

		if list_to_write[0] == 'INF':
			text_color = self.GENERAL_COLOR
		elif list_to_write[0] == "ERR":
			text_color = self.ERROR_COLOR
		elif list_to_write[0] == "SUC":
			text_color = self.SUCCESS_COLOR
		else:
			print(f"mestype: {mestype}")
			return
		message_item.setForeground(QBrush(text_color))
		message_item.setTextAlignment(Qt.AlignLeft |Qt.AlignVCenter)

		message_item.setFlags(message_item.flags() | Qt.TextWordWrap)

		self.console_widget.setItem(num_line, 1 ,message_item)
		self.console_widget.resizeColumnToContents(1)
		
		value = self.console_widget.verticalScrollBar().maximum()

		self.console_widget.verticalScrollBar().rangeChanged.connect(lambda: self.autoScroll(value))


	def autoScroll(self, cur_max):
		self.console_widget.verticalScrollBar().setSliderPosition(99+cur_max)
		

#THE MESSAGE LOG WITH LINES
	
# class Message_log_handling():

# 	def __init__(self, parent_tab, path_to_directory):
# 		self.console_widget = QPlainTextEdit(parent_tab)
# 		self.console_widget.setReadOnly(True)
# 		self.PROTON_history_list = []
# 		self.message_log_path = path_to_directory+ "/history_log.txt"

# 		checkExists =os.path.exists(self.message_log_path)
		
# 		if checkExists == True:

# 			with open(self.message_log_path, "r") as fd:
# 				while True:
# 					temp_line = fd.readline()
# 					if temp_line == "":
# 						break
# 					self.write_message_log(temp_line)

# 			self.write_message_log("============================================================\n")
# 		else:
# 			temp_message = "The project was created"
# 			self.track_history_messages(temp_message)
		

# 	def get_widget(self):
# 		return self.console_widget

# 	def track_history_messages(self, message):
# 		cur_time = time.localtime()

# 		timestamp = time.strftime("%a %d %b %Y %H:%M:%S", cur_time)
# 		message_log = "[" + timestamp + "] " + message + "\n"
		
# 		self.PROTON_history_list.append(message_log)
# 		self.write_message_log(message_log)

# 		if (len(self.PROTON_history_list) == 50):
# 			self.save_history_log(False)

# 	def save_history_log(self, save):
			
# 		num_of_messages = len(self.PROTON_history_list)
		
# 		with open(self.message_log_path, "a") as fd:
# 			for item in self.PROTON_history_list:
# 				fd.write(item)
		
# 		if num_of_messages >= 50 or save:
# 			self.PROTON_history_list.clear()

	
# 	def write_message_log(self, line_to_write):
# 		self.console_widget.appendPlainText(line_to_write)


