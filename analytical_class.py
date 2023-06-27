import re
from math import floor, ceil , exp
import time
import typing
import numpy as np
from pathlib import Path
import os
import sys
import array
from PyQt5.QtCore import QObject, pyqtSignal
import subprocess

os.system("")

class Analytical_Class(QObject):
  finished = pyqtSignal()
  return_message = pyqtSignal(str)

  def __init__(self,sim_time,directory,SELECTED_LINE,TECHNOLOGY,TEMPERATURE,WIDTH,IS_LINUX, INSTALLATION_FOLDER):
    super().__init__()
    self.sim_time=sim_time
    self.directory=directory
    self.SELECTED_LINE=SELECTED_LINE
    self.TECHNOLOGY=TECHNOLOGY
    self.TEMPERATURE=TEMPERATURE
    self.WIDTH=WIDTH
    self.IS_LINUX = IS_LINUX
    self.INSTALLATION_FOLDER = INSTALLATION_FOLDER

  def analytical_function(self):
	
    Acoef = ""
    nxTotal = ""

    if not self.SELECTED_LINE:
      self.return_message.emit('No line was selected and discretized prior to simulation.')
      self.finished.emit()
      print('No line was selected and discretized prior to simulation.')
      return

    # Read the internal configuration file for analytical provided by matrix formulation
    line_path = self.SELECTED_LINE.text(0)+"/"+self.TECHNOLOGY+"_"+str(self.TEMPERATURE)+"_"+str(self.WIDTH)+"/"
    analytical_file = self.directory+"/"+"input"+"/"+line_path+"analytical.txt"
    # print("Going to open "+ analytical_file)
    try:
      with open(analytical_file) as f_anal:
        lines=f_anal.readlines()
        for line in lines:
          words = line.split()
          if'Acoef'in words: Acoef=words[2]
          if'nx_total'in words: nxTotal = words[2]
        f_anal.close()
    except FileNotFoundError as e:
      self.return_message.emit(f"No discretization has been performed for line {self.SELECTED_LINE.text(0)}.")
      self.finished.emit()
      print(f"No discretization has been performed for line {self.SELECTED_LINE.text(0)}.")
      return

    # Check that the input files directory exists (not much of a check but for precaution)
    input_files = self.directory + "/input/"+line_path
    if not os.path.exists(input_files):
      self.return_message.emit(f'Input files directory for {self.SELECTED_LINE.text(0)} does not exist.')
      self.finished.emit()
      print(f'Input files directory for {self.SELECTED_LINE.text(0)} does not exist.')
      return

    # Create the configuration file for C++ Analytical code here
    config_file = self.directory+"/input/"+line_path+"analytical.cfg"
    with open(config_file, "w") as f:
      f.write(f"input_files {input_files}\nnum_nodes {nxTotal}\n")
      f.write(f"A_coeff {Acoef}\nsimulation_time {self.sim_time}\n")
      f.close()

    #subprocess.run(["cd","C_kernel_code_analytical"])

    # result = subprocess.run(["python","EMtool.py",config_file])
    # if result.returncode == 0:
      # print("Analytical ran successfully!")
    # else:
      # print("There was a problem with analytical")

    start_time = time.time()
    if self.IS_LINUX:
      # return_value = os.system(". /opt/intel/oneapi/mkl/latest/env/vars.sh")
      exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/EMtool_analytical")
      source_command = ". /opt/intel/oneapi/mkl/latest/env/vars.sh;"
    else:
      source_command = ""
      exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/EMtool_analytical.exe")
    # print(f'Executable full path: {exec_path}')

    if not self.IS_LINUX:
      si = subprocess.STARTUPINFO()
      si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      return_value = subprocess.call(f"{source_command}{exec_path} {config_file}", startupinfo=si)
    else:
      return_value = subprocess.call(f"{source_command}{exec_path} {config_file}")
    # return_value = os.system(f"{source_command}{exec_path} {config_file}")
    
    elapsed_time = time.time() - start_time

    if return_value == 0:
      self.return_message.emit(f"EM stress analysis was successfully performed in {elapsed_time:.3f} seconds for the line {self.SELECTED_LINE.text(0)} (Configuration: {self.TECHNOLOGY}, {self.TEMPERATURE}K, {self.WIDTH}um).")
      self.finished.emit()
      # print(f"EM stress analysis was successfully performed in {elapsed_time:.3f} seconds for the line {self.SELECTED_LINE.text(0)} (Configuration: {self.TECHNOLOGY}, {self.TEMPERATURE}K, {self.WIDTH}um).")
      
    elif return_value == -1073740791: # 0xc0000409
      self.return_message.emit("Line analysis terminated with exception (0xc0000409) in system settings or system files or registry entries or critical utilities."f'Input files directory for {self.SELECTED_LINE.text(0)} does not exist.')
      self.finished.emit()
      print("Line analysis terminated with exception (0xc0000409) in system settings or system files or registry entries or critical utilities.")
    elif return_value == -1073741819: # 0xC0000005
      self.return_message.emit("Line analysis terminated with Access Violation exception (0xC0000005). The program tried to read or write in a section of memory that does not have access to.")
      self.finished.emit()
      print("Line analysis terminated with Access Violation exception (0xC0000005). The program tried to read or write in a section of memory that does not have access to.")
    elif return_value == -1073741676: # 0xC0000094
      self.return_message.emit("Line analysis terminated with exception (0xC0000094). Integer division by zero exception code on Windows")
      self.finished.emit()
      print("Line analysis terminated with exception (0xC0000094). Integer division by zero exception code on Windows")
    elif return_value == -1073741515:
      self.return_message.emit("Line analysis terminated with exception (-1073741515). Problem with the dependencies")
      self.finished.emit()
      print("Line analysis terminated with exception (-1073741515). Problem with the dependencies")
    elif return_value == 32512:
      self.return_message.emit("Line analysis terminated with exception 32512. Problem with the dependencies")
      self.finished.emit()
      print("Line analysis terminated with exception 32512. Problem with the dependencies")
    else:
      self.return_message.emit(f"Line analysis terminated with unknown error {return_value}.")
      self.finished.emit()
      print(f"Line analysis terminated with unknown error {return_value}.")

    # self.finished.emit()
    # self.return_message.emit(None)
    # print("Going to peacefully return")

    