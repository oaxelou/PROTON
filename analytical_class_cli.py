import time
import os

os.system("")

class Analytical_Class():

  def __init__(self,sim_time,directory,selected_line,TECHNOLOGY,TEMPERATURE,WIDTH,IS_LINUX, INSTALLATION_FOLDER):
    super().__init__()
    self.sim_time=sim_time
    self.directory=directory
    self.selected_line=selected_line
    self.TECHNOLOGY=TECHNOLOGY
    self.TEMPERATURE=TEMPERATURE
    self.WIDTH=WIDTH
    self.IS_LINUX = IS_LINUX
    self.INSTALLATION_FOLDER = INSTALLATION_FOLDER

  def analytical_function(self):
	
    Acoef = ""
    nxTotal = ""

    # print(f"selected_line: {self.selected_line}")

    if not self.selected_line:
      # print('No line was selected and discretized prior to simulation.')
      return('No line was selected and discretized prior to simulation.')

    # Read the internal configuration file for analytical provided by matrix formulation
    line_path = self.selected_line+"/"+self.TECHNOLOGY+"_"+str(self.TEMPERATURE)+"_"+str(self.WIDTH)+"/"
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
      # print(f"No discretization has been performed for line {self.selected_line}.")
      return(f"No discretization has been performed for line {self.selected_line} with params: {self.TECHNOLOGY}, {self.TEMPERATURE}, {self.WIDTH}.")

    # Check that the input files directory exists (not much of a check but for precaution)
    input_files = self.directory + "/input/"+line_path
    if not os.path.exists(input_files):
      # print(f'Input files directory for {self.selected_line} does not exist.')
      return(f'Input files directory for {self.selected_line} does not exist.')

    # Create the configuration file for C++ Analytical code here
    config_file = self.directory+"/input/"+line_path+"analytical.cfg"
    with open(config_file, "w") as f:
      f.write(f"input_files {input_files}\nnum_nodes {nxTotal}\n")
      f.write(f"A_coeff {Acoef}\nsimulation_time {self.sim_time}\n")
      f.close()

    start_time = time.time()
    if self.IS_LINUX:
      # return_value = os.system(". /opt/intel/oneapi/mkl/latest/env/vars.sh")
      exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/EMtool_analytical")
      source_command = ". /opt/intel/oneapi/mkl/latest/env/vars.sh;"
    else:
      source_command = ""
      exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/EMtool_analytical.exe")
    # print(f'Executable full path: {exec_path}')
    return_value = os.system(f"{source_command}{exec_path} " + config_file)
    elapsed_time = time.time() - start_time

    if return_value == 0:
      return_message = f"EM stress analysis was successfully performed in {elapsed_time:.3f} seconds for the line {self.selected_line} (Configuration: {self.TECHNOLOGY}, {self.TEMPERATURE}K, {self.WIDTH}um)."
      
    elif return_value == -1073740791: # 0xc0000409
      return_message = "Line analysis terminated with exception (0xc0000409) in system settings or system files or registry entries or critical utilities."
    elif return_value == -1073741819: # 0xC0000005
      return_message = "Line analysis terminated with Access Violation exception (0xC0000005). The program tried to read or write in a section of memory that does not have access to."
    elif return_value == -1073741676: # 0xC0000094
      return_message = "Line analysis terminated with exception (0xC0000094). Integer division by zero exception code on Windows"
    elif return_value == -1073741515:
      return_message = "Line analysis terminated with exception (-1073741515). Problem with the dependencies"
    elif return_value == 32512:
      return_message = "Line analysis terminated with exception 32512. Problem with the dependencies"
    elif return_value == -1073741510:
      raise KeyboardInterrupt
    else:
      return_message = f"Line analysis terminated with unknown error {return_value}."

    # print(return_message)
    # print("Going to peacefully return")
    return(return_message)

    