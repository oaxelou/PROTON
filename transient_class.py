from math import floor, ceil , exp
import time
import os
import csv
from PyQt5.QtCore import QObject, pyqtSignal
import subprocess

# os.system("")

class Transient_Class(QObject):
  finished = pyqtSignal()
  return_message = pyqtSignal(str)
  info_message = pyqtSignal(str)

  def __init__(self,sim_time,timestep,directory,SELECTED_LINE, TECHNOLOGY, TEMPERATURE, WIDTH, NX_TOTAL, mor_enabled=None, reduced_order=None, IS_LINUX=False, INSTALLATION_FOLDER=""):
    super().__init__()
    self.sim_time=sim_time
    self.timestep=timestep
    self.directory=directory
    self.seleted_line=SELECTED_LINE
    self.technology=TECHNOLOGY
    self.temperature=TEMPERATURE
    self.width=WIDTH
    self.nx_total = NX_TOTAL
    self.mor_enabled = mor_enabled
    self.reduced_order = reduced_order
    self.IS_LINUX = IS_LINUX
    self.INSTALLATION_FOLDER = INSTALLATION_FOLDER

  def transient_function(self):
	
    if not self.seleted_line:
      self.return_message.emit('No line was selected and discretized prior to simulation.')
      self.finished.emit()
      print('No line was selected and discretized prior to simulation.')
      return

    line_path = self.seleted_line.text(0)+"/"+self.technology+"_"+str(self.temperature)+"_"+str(self.width)+"/"
    input_files = self.directory + "/input/"+line_path
    output_files = self.directory + "/output/"+line_path
    
    mor_elapsed_time = 0
    # Model Order Reduction
    if self.mor_enabled:
      reduced_files = self.directory + "/output/"+line_path+"reduced_matrices/"

      run_mor_flag = False
      if os.path.exists(reduced_files) and os.path.exists(input_files+"mor_specs.csv"):
        with open(input_files+"mor_specs.csv", "r") as f:
          lines = f.readlines()

        for line in lines:
            key, value = line.strip().split(", ")
            if key == "line":
                old_selected_line = value
            elif key == "technology":
                old_technology = value
            elif key == "temperature":
                old_temperature = float(value)
            elif key == "width":
                old_width = float(value)
            elif key == "nx_total":
                old_nx_total = int(value)
            elif key == "reduced":
                old_reduced_order = int(value)
        
        if self.seleted_line.text(0) != old_selected_line or self.technology != old_technology or \
          float(self.temperature) != old_temperature or float(self.width) != old_width or int(self.nx_total) != old_nx_total or int(self.reduced_order) != old_reduced_order:
          run_mor_flag = True
          print("Going to run MOR again!")
        else:
          print("No need to run MOR again!")
      else:
        run_mor_flag = True
        print("Going to run MOR!")

      if run_mor_flag:
        print("Write a file with the specs of MOR")
        try:
          with open(input_files+"mor_specs.csv", "w") as f:
            f.write(f"line, {self.seleted_line.text(0)}\n")
            f.write(f"technology, {self.technology}\n")
            f.write(f"temperature, {self.temperature}\n")
            f.write(f"width, {self.width}\n")
            f.write(f"nx_total, {self.nx_total}\n")
            f.write(f"reduced, {self.reduced_order}\n")
            f.close()
        except FileNotFoundError as e:
          return(f"No discretization was performed for line {self.selected_line}")
        except PermissionError as e:
          print("mor_specs.csv is open in another app. Close it before running the analysis.")
          self.return_message.emit(f"File {input_files+'mor_specs.csv'} is open in another app. Close it before running the analysis.")
          self.finished.emit()

        # Create configuration file here
        mor_config_file = input_files+"mor.cfg"
        with open(mor_config_file, "w") as f:
          f.write(f"set_working_directory {self.directory}/\n")
          f.write(f"set_output_directory output/{line_path}reduced_matrices/\n")
          f.write(f"set_G input/{line_path}G.csv\n")
          f.write(f"set_B input/{line_path}B.csv\n")
          f.write(f"set_L input/{line_path}L.csv\n")
          f.write(f"set_reduced_size {self.reduced_order}\n")
          f.close()

        start_time = time.time()
        
        if self.IS_LINUX:
          exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/EMtool_mor")
          source_command = ". /opt/intel/oneapi/mkl/latest/env/vars.sh;"
        else:
          exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/EMtool_mor.exe")
          source_command = ""
        
        if not self.IS_LINUX:
          si = subprocess.STARTUPINFO()
          si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
          mor_return_value = subprocess.call(f"{source_command}{exec_path} {mor_config_file}", startupinfo=si)
        else:
          mor_return_value = subprocess.call(f"{source_command}{exec_path} {mor_config_file}")

        # mor_return_value = os.system(f"{source_command}{exec_path} {mor_config_file}")
        mor_elapsed_time = time.time() - start_time

        if mor_return_value == 0:
          # self.return_message.emit(f"Model order reduction was successfully performed in {mor_elapsed_time:.3f} seconds.")
          print(f"Model order reduction was successfully performed in {mor_elapsed_time:.3f} seconds.")
        elif mor_return_value == -1073741819: # 0xC0000005
          self.return_message.emit("Model order reduction terminated with Access Violation exception (0xC0000005). The program tried to read or write in a section of memory that does not have access to.")
          self.finished.emit()
          print("Model order reduction terminated with Access Violation exception (0xC0000005). The program tried to read or write in a section of memory that does not have access to.")
        elif mor_return_value == -1073741676: # 0xC0000094
          self.return_message.emit("Model order reduction terminated with exception (0xC0000094). Integer division by zero exception code on Windows")
          self.finished.emit()
          print("Model order reduction terminated with exception (0xC0000094). Integer division by zero exception code on Windows")
        elif mor_return_value == -1073741515:
          self.return_message.emit("Model order reduction terminated with exception (-1073741515). Problem with the dependencies")
          self.finished.emit()
          print("Model order reduction terminated with exception (-1073741515). Problem with the dependencies")
        elif mor_return_value == 32512:
          self.return_message.emit("Model order reduction terminated with exception 32512. Problem with the dependencies")
          self.finished.emit()
          print("Model order reduction terminated with exception 32512. Problem with the dependencies")
        else:
          self.return_message.emit('Model order reduction was forcefully termined due to errors.')
          self.finished.emit()
          print(f"Error with value {mor_return_value}.")
          print("Going to peacefully return")
          return
        
        with open(os.path.join(reduced_files, "Br.csv"), 'r') as f:
          reader = csv.reader(f)
          actual_reduced_order = int(list(reader)[-1][1])+1
        self.info_message.emit(f"Reduced order parameter is converted to {ceil(int(self.reduced_order)/actual_reduced_order)*actual_reduced_order}.")
        
      else:
        print("There is no need to re-run MOR.")
        self.info_message.emit("Reduced system has already been constructed for the selected discretization and reduced size. MOR procedure is omitted.")
    
    # Creation of the configuration file for python transient code
    config_file = input_files+"numerical.cfg"
    with open(config_file, "w") as f:
      f.write(f"input_files {input_files}\noutput_files {output_files}\n")
      if self.mor_enabled:
        f.write(f"reduced_matrices {reduced_files}\noutput_files {output_files}\n")
      f.write(f"simulation_time {self.sim_time}\ntimestep {self.timestep}\n")
      f.write(f"is_original {not self.mor_enabled}\n")
      f.close()

    start_time = time.time()
    python_exec_path = os.path.join(self.INSTALLATION_FOLDER, "simulation/simulation.py")
    source_command = ""
    if self.IS_LINUX:
      source_command = ". /opt/intel/oneapi/mkl/latest/env/vars.sh;"
      # source_command += "alias python='python3';"
    
    if not self.IS_LINUX:
      si = subprocess.STARTUPINFO()
      si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
      return_value = subprocess.call(f"{source_command}python {python_exec_path} {config_file}", startupinfo=si)
    else:
      return_value = subprocess.call(f"{source_command}python {python_exec_path} {config_file}")

    # return_value = os.system(f"{source_command}pythonw {python_exec_path} {config_file}")
    elapsed_time = time.time() - start_time

    if return_value == 0:
      self.return_message.emit(f"Point analysis was successfully performed in {(mor_elapsed_time+elapsed_time):.3f} seconds for the line {self.seleted_line.text(0)} (Configuration: {self.technology}, {self.temperature}K, {self.width}um).")
      self.finished.emit()
      print(f"Point analysis was successfully performed in {elapsed_time:.3f} seconds for the line {self.seleted_line.text(0)} (Configuration: {self.technology}, {self.temperature}K, {self.width}um).")
    elif return_value==2:
      self.return_message.emit('Problem with discretization.')
      self.finished.emit()
      print(f"Error with value {return_value}.")
    elif return_value == 256 or return_value == 32512:
      self.return_message.emit(f"Model order reduction terminated with exception {return_value}. Problem with the dependencies")
      self.finished.emit()
      print(f"Model order reduction terminated with exception {return_value}. Problem with the dependencies")
    else:
      self.return_message.emit(f'Point analysis was forcefully termined with error {return_value}.')
      self.finished.emit()
      print(f"Error with value {return_value}.")

    # self.finished.emit()
    # self.return_message.emit(None)
    # print("Going to peacefully return")

    
