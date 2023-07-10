from pathlib import Path
import os
import sys
import subprocess
import traceback
import time
from PyQt5.QtCore import QObject, pyqtSignal

os.system("")

# # # Parameters

benchmark=""

def change_directory_filename(filename, project_location):
    directory = os.path.dirname(filename)
    base_name = os.path.basename(filename)
    root_name, extension = os.path.splitext(base_name)
    new_filename = os.path.join(project_location, f"{root_name}{extension}")
    return new_filename

def remove_strings_with_substring(strings, substring):
    return [string for string in strings if substring not in string]

class Spice_Parser_Class(QObject):
  finished = pyqtSignal()
  return_message = pyqtSignal(str)

  def __init__(self, spice_file, project_location, IS_LINUX, INSTALLATION_FOLDER):
    super().__init__()
    self.spice_file = spice_file
    self.project_location = project_location
    self.IS_LINUX = IS_LINUX
    self.INSTALLATION_FOLDER = INSTALLATION_FOLDER
    self.interrupted = False

  def request_interruption(self):
    self.interrupted = True

  def spice_parser(self): 
    start_time = time.time()

    spice_file = self.spice_file
    project_location = self.project_location
    IS_LINUX = self.IS_LINUX

    foldername= "".join(spice_file.split('/')[-1].split('.')[:-1])
    global benchmark 
    benchmark= project_location+"/"+foldername
    if IS_LINUX:
      # Remove .op if exists
      with open(spice_file, 'r') as f:
        lines = f.readlines()
        lines = remove_strings_with_substring(lines, '.end')
        found_sparse_option = False
        for line in lines:
          if '.options sparse method = be gnuplotl' in line:
            found_sparse_option = True
        if not found_sparse_option:
          lines.append('.options sparse method = be gnuplotl')
        spice_file = change_directory_filename(spice_file, project_location)
        with open(spice_file, 'w') as f_new:
          for line in lines:
            f_new.write(line)

      exec_path = os.path.join(self.INSTALLATION_FOLDER, "bin/circuit_simulation")
      result=subprocess.run([exec_path,spice_file])
      if self.interrupted:
        os.remove(DC_analysis_filename)
        return

      DC_analysis_filename = "DC_analysis.txt"
    else:
      benchmark_name = os.path.splitext(os.path.basename(spice_file))[0]
      if benchmark_name == "ibmpg1":
        DC_analysis_filename = "benchmarks/DC_analyses/DC_analysis_ibmpg1.txt"
      elif benchmark_name == "ibmpg2":
        DC_analysis_filename = "benchmarks/DC_analyses/DC_analysis_ibmpg2.txt"
      else:
        self.return_message.emit(f"There is no DC analysis file for benchmark {benchmark_name}.")
        self.finished.emit()
        return

    spice_filename = spice_file

    ###################################

    if IS_LINUX:
      print(f'Result: {result}')
      if(result.returncode!=0):
        # return (1, "There was an error during the DC analysis. Check the spice file.")
        self.return_message.emit("There was an error during the DC analysis. Check the spice file.")
        self.finished.emit()
        return


    
    ###################################3
    
    
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # # DC Analysis Currents Parser
    #
    # Get all currents from file DC_analysis_filename for all nodes.
    # Then, in SPICE parser we are going to keep the ones we need

    currents = {}
    try:
      with open(DC_analysis_filename) as f_dc_currents:
        lines = f_dc_currents.readlines()
        for line in lines:
          if self.interrupted:
            return
          words = line.split()
          if '|Current' not in words:
            continue
          currents[words[3] + words[4][:-1]] = float(words[5])

      if IS_LINUX:
        os.remove(DC_analysis_filename)
    except ValueError as e:
      # return(1, "Corrupted DC analysis currents file.")
      self.return_message.emit("Corrupted DC analysis currents file.")
      self.finished.emit()
      return
    except FileNotFoundError as e:
      # return(1, "DC analysis currents file not found.") 
      self.return_message.emit("DC analysis currents file not found.")
      self.finished.emit()
      return
    except Exception as e:
      print(e)
      # return(1, "An error occured while parsing DC analysis currents file.")
      self.return_message.emit("An error occured while parsing DC analysis currents file.")
      self.finished.emit()
      return
    

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    # # SPICE Parser
    # 
    # Reads each line of the SPICE file.
    # - We only need the Resistor lines (but not the shorts) -> only the capital 'R'
    # - Each layer is dealt separately from our tool, so if two nodes are in separate 
    #   layer or net, we ignore these lines (aka the vias)


    resistors = {}
    is_left_node_of = {}
    is_right_node_of = {}
    layers_dic = {}


    max_current = 0
    max_current_file = ""
    max_segments = 0
    max_segments_file = ""
    isFirstCurden = True
    found_layers = out = False
    layer = ""
    net = ""
    segment_number = line_number = 0
    left_node = right_node = None
    total_layers=0

    max_lines_per_net = 0
    max_lines_per_net_thenet = ""
    total_lines = total_segments = 0
    
    try:
      with open(spice_filename) as f:
        lines = f.readlines()

        nextLine = False
        for line in lines:
          if self.interrupted:
            return
          i = 0
          if line[i] == '\n':
            nextLine = True
            continue

          while line[i] == ' ' or line[i] == '\t':
            if line[i] == '\n':
              nextLine = True
              break
          if nextLine:
            nextLine = False
            continue

          # If no resistors are found yet, continue until you find one.
          # We do not include shorts.
          if not found_layers:
            line_components = line.split()
            if line_components[0][0] == 'R':
              found_layers = True

              #if net is not in the dictionary then continue
              if line_components[1].split('_')[0] not in layers_dic:
                continue
              layer, net = layers_dic[line_components[1].split('_')[0]] , line_components[1].split('_')[0]
              folder = benchmark + "/"
              if not os.path.exists(folder):
                os.makedirs(folder)

          # Get only the lines with the Resistors
          if line[0] == 'R':

            # If we have found a segment of zero length, then we ignore the rest of this layer's lines
            if out:
              continue

            # Get the coordinates of the previous line's nodes
            prev_left_node, prev_right_node = left_node, right_node
            if prev_left_node and prev_right_node:
              prev_left_coords, prev_right_coords = prev_left_node.split('_'), prev_right_node.split('_')

            # Current nodes
            line_words = line.split()
            left_node, right_node = line_words[1], line_words[2]
            left_coords, right_coords = left_node.split('_'), right_node.split('_')

            # # Add found resistor in the dictionary
            # key: name of resistor
            # val: resistance (Ohm)
            if line_words[0] not in resistors:
              resistors[line_words[0]] = float(line_words[3])
            else:
              # return(1, "{line_words[0]} has already been parsed.")
              self.return_message.emit("{line_words[0]} has already been parsed.")
              self.finished.emit()
              return


            #If new layer is found when the previous left node is different to the left node,
            # change the start of the filename
            if prev_left_node and prev_right_node and prev_left_coords[0] != left_coords[0]:
              out = False

              # if net is not in the dictionary then continue
              if line_words[1].split('_')[0] not in layers_dic:
                continue

              if max_lines_per_net < line_number:
                max_lines_per_net = line_number
                max_lines_per_net_thenet = current_net
              layer, net = layers_dic[line_words[1].split('_')[0]], line_words[1].split('_')[0]
              segment_number = line_number = 0
              folder = benchmark
              if not os.path.exists(folder):
                os.makedirs(folder)

            if left_coords[0] != right_coords[0]:  # via
              # print(f'Nodes are on different nets. {line}')
              continue
            if left_coords[2] == right_coords[2]:
              # Y is the same!
              same_coordinate, diff_corrdinate = 2, 1
            else:
              # X is the same!
              same_coordinate, diff_corrdinate = 1, 2

            # If previous nodes exist (this exists to ensure that it is not the first line found)
            # and if the previous left node has the same coordinate:
            # - Continue writing at the already opened file and increase the number of segments.
            # - Otherwise, it is a new line and what we found is its first segment.
            if prev_left_node and prev_right_node and prev_left_coords[same_coordinate] == left_coords[same_coordinate]:
              segment_number +=1
              total_segments += 1
            else:
              segment_number = 0
            
            # Compute the distance between the 2 nodes by substituing the different coordinate
            length = abs(int(left_coords[diff_corrdinate]) - int(right_coords[diff_corrdinate]))
            
            # if a new line, change the file on which we are writing
            if segment_number == 0:
              line_number += 1
              total_lines += 1

              folder = benchmark+"/"+layer
              if not os.path.exists(folder):
                os.makedirs(folder)

              filename = folder + "/" + layer + "_" + net + "_" + str(line_number) + ".csv"
              f = open(filename, "w")
              segment_str = "segment_name, left_node, right_node, length, curden\n"
              f.write(segment_str)

            if length > 0:
              segment_current = currents[line_words[0]] 
            else:
              segment_current = 0
              print(f'Segment {line_number} has zero length. Out!')
              print(line)
              out = True
              continue

            segment_str = line_words[0] + ", " + line_words[1] + ", " + line_words[2] +  ", " + str(length) + ", " + str(segment_current) + "\n"
            f.write(segment_str)
          
            # (Statistics) Store the maximum value of current density
            if isFirstCurden:
              isFirstCurden = False
              max_curden = segment_current
              max_current = currents[line_words[0]]
              max_curden_filename = filename
              max_current_file = filename
            else:
              if max_curden < segment_current:
                max_curden = segment_current
                #max_current = currents[line_words[0]]
                max_curden_filename = filename
              if max_current < currents[line_words[0]]:
                max_current = currents[line_words[0]]
                max_current_file = filename
            if max_segments < segment_number:
              max_segments = segment_number
              max_segments_file = filename

          # If comment *layer is found , keep layer and node in a dictionary
          elif line[0:7] == '* layer':
            out = False

            # # Add found layer in the dictionary
            # key: net
            # val: layer
            line_components = line.split()
            if 'n'+str(line_components[4]) not in layers_dic:
              layers_dic['n'+str(line_components[4])] = line_components[2].split(',')[0]
              current_net = f'{layers_dic["n"+str(line_components[4])]}_n{line_components[4]}' 
              print(f'Found layer {layers_dic["n"+str(line_components[4])]}, net {line_components[4]}')

    except ValueError as e:
      # return(1, "Corrupted Spice file.")
      self.return_message.emit("Corrupted Spice file.")
      self.finished.emit()
      return
    except FileNotFoundError as e:
      # return(1, "Spice file not found.") 
      self.return_message.emit("Spice file not found.")
      self.finished.emit()
      return
    except Exception as e:
      traceback.print_exc()
      # return(1, "An error occured while parsing Spice file.")
      self.return_message.emit("An error occured while parsing Spice file.")
      self.finished.emit()
      return



    folder_stat = project_location +"/statistics"
    if not os.path.exists(folder_stat):
      os.makedirs(folder_stat)

    filename = folder_stat + "/Statistics.csv"
    f = open(filename,"w")
    segment_str = "layers" + ", " +str(len(set(layers_dic.values()))) +"\n"+\
        "nets" + ", " + str(len(layers_dic))+"\n"+\
        "total lines" + ", " + str(total_lines) +"\n" +\
        "total segments" + ", " + str(total_segments) +"\n"+\
        "Max lines per net" + ", " + str(max_lines_per_net) + ", " + "Location " + max_lines_per_net_thenet + "\n" +\
        "Max segments" + ", " + str(max_segments) + ", " + "Location " + max_segments_file.split("/")[-1] + "\n" +\
        "Max current" + ", " + str(max_current) + ", " + "Location " + max_current_file.split("/")[-1] + "\n"
        
    f.write(segment_str)
    f.close()
    # print("Done with the parsing of spice file")

    elapsed_time = time.time() - start_time
    # return (0,"Successfully parsed spice file.")
    self.return_message.emit(f"in {elapsed_time:.3f} seconds")
    self.finished.emit()
    return
    


  