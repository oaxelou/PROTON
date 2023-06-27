import re
from math import floor, ceil , exp
import numpy as np
from pathlib import Path
import os
import sys
import array
import time
import traceback

os.system("")

class Matrix_Formulation_Class():
  def __init__(self, csv_file,project_location,sp_step,given_disc_point,technology,temperature,givenWidth):
    super().__init__()
    self.csv_file = csv_file
    self.project_location = project_location
    self.sp_step = sp_step
    self.given_disc_point = given_disc_point
    self.technology = technology
    self.temperature = temperature
    self.givenWidth = givenWidth

  def matrix_formulation(self):

    # print("In matrix formulation")
    start_time = time.time()

    csv_filename=self.csv_file
    dx = 0.0
    scale = 'um'
    nx_total = num_segments = 0 #nx_total is the number of the nodes totally
    vias_nodes = [] #the via nodes
    curden_list = [] #the list with curden for each segment
    vias = {} #the via nodes with the segment
    left_node = right_node = None
    length = 0
    result = 0.0
    total_length=0.0
    disc_points = 0
    acoef=0.0

    if(self.sp_step == None and self.given_disc_point==None):
      print("Error no discretization method is choosen!")
      return("Error no discretization method is choosen!")

    # Physical parameters - Cu DD
    if(self.technology == "CuDD"):
      D0=1.3e-9;              # Diffusivity Constant (m^2/s)
      Ea=1.609e-19;           # Activation Energy 
      kB=1.3806e-23;          # Boltzmann constant (J/K).
      T = float(self.temperature); # Temperature (K)
      Da=D0*exp(-Ea/(kB*T));  # Diffusion coefficient 
      B0=28e9;                # Bulk Modulus for the metal (Pa)
      Omega=1.182e-29;        # Atomic Volume foe the metal (m^3)
      rho=2.25e-8;            # Electrical Resistivity (Ohm m)
      Z=1;                    # Effective Charge Number

      kappa=(Da*B0*Omega)/(kB*T)
      b = Ea*Z*rho/Omega
    else :
      D0=1e-4;              # Diffusivity Constant (m^2/s)
      Ea=1.92e-29;           # Activation Energy 
      kB=1.3806e-23;          # Boltzmann constant (J/K).
      T = float(self.temperature); # Temperature (K)
      Da=D0*exp(-Ea/(kB*T));  # Diffusion coefficient 
      B0=80e9;                # Bulk Modulus for the metal (Pa)
      Omega=2e-29;        # Atomic Volume foe the metal (m^3)
      rho=3.16e-8;            # Electrical Resistivity (Ohm m)
      Z=1;                    # Effective Charge Number

      kappa=(Da*B0*Omega)/(kB*T)
      b = Ea*Z*rho/Omega




    try:
      with open(csv_filename) as f:
        lines = f.readlines()

        #when given the disc_points add all lengths and divide by the disc_points in order to find the dx
        #for each segment and then have the exact same steps with the sp_step method

        
        if(self.given_disc_point!=None):
          #find total length of all segments 
          for line1 in lines:
            if line1[0] == 'R':
              line_components = line1.split(',')
              total_length=total_length+float(line_components[3])

          #when given the disc_points there are and the vias nodes between the segments 
          #that are not calculated (two segments share the same point that is calculated as one)
          # we should add the vias to the disc_points in order to find the right dx because then we calculate  
          # for each segment .The vias to be add is the total segments-1
          # len(lines)-1 is because len adds the header to the result
          self.given_disc_point = float(self.given_disc_point) + (len(lines)-2) 
          
          #when total length is calculated find the dx
          dx=round(float(total_length/self.given_disc_point),2) #round with 2 decimal points
          dx = dx * 1e-6

        for line in lines:

          if line[0] == 'R':
            line_components = line.split(',')
            num_segments = num_segments+1

            length = float(line_components[3])  #keep the length of each segment
            
            # exponent = math.floor(math.log10(length)) 
            # if exponent != -6:
            #   # Multiply by the minus exponent before transforming it into m
            #   length = length * (10 ** (-1*))
            #   print('Length transformed from um to m')
            
            length = length * 1e-6

            # self.givenWidth = self.givenWidth *1e-6
            result = float(line_components[4])/(self.givenWidth*1e-6*self.givenWidth*1e-6) #curden=current/width*width

            curden_list.append(result)

            if(self.sp_step!=None):
              dx=float(self.sp_step)*1e-6

            if length < dx:
              print("The given discretization is not dense enough for the geometry of the given line.")
              return("The given discretization is not dense enough for the geometry of the given line.")
            
            #disc_points for each segment . Must be int thats why and the round 
            disc_points = round(length/dx) 
                
            nx_total = nx_total + disc_points

            #######################################################
            # check if the segment is a via #
            # Get the coordinates of the previous line's nodes
            prev_left_node, prev_right_node = left_node, right_node
            if prev_left_node and prev_right_node:
              prev_left_coords, prev_right_coords = prev_left_node.split('_'), prev_right_node.split('_')

            # Current nodes
            left_node, right_node = line_components[1], line_components[2]
            left_coords, right_coords = left_node.split('_'), right_node.split('_')

            if left_coords[2] == right_coords[2]:
              same_coordinate = 2
            else:
              same_coordinate = 1

            if prev_left_node and prev_right_node and prev_left_coords[same_coordinate]==left_coords[same_coordinate]:
              key = nx_total-disc_points  #the key for the vias{} is the node
              vias[key] = num_segments  #the segmnet of the second segment is the value
              vias_nodes.append(key)  # keep the keys in a list
              nx_total = nx_total - 1  #-1 because of the same node(via)

    except ValueError as e:
      print("Corrupted CSV segments file.")
      return("Corrupted CSV segments file.")
    except FileNotFoundError as e:
      print("CSV file not found.") 
      return("CSV file not found.") 
    except Exception as e:
      print(e)
      traceback.print_exc()
      print("An error occured while parsing CSV file.")
      return("An error occured while parsing CSV file.")

    ###### Create Matrices C, G & B
    matrix_G = [[0.0 for x in range(nx_total)] for y in range(nx_total)] 
    matrix_B = [[0.0 for x in range(num_segments)] for y in range(nx_total)]
    matrix_L = [[0.0 for x in range(nx_total)] for y in range(num_segments+1)]
    curden = [0.0 for x in range(num_segments)]
    monitor_points = [0.0 for x in range(num_segments+1)]

    #######################################
    #Create matrix curden
    curden = array.array('f',curden_list)

    ######################################
    #Create matrix G
    help_matrix = np.ones((nx_total, nx_total), float) #an array with ones
    matrix_G = np.diag(np.diag(help_matrix, 1), 1) + np.diag(np.diag(help_matrix, 1), -1) #the lines left and right of the diag
    np.fill_diagonal(matrix_G, -2.0)
    matrix_G[0][0] = -1.0
    matrix_G[nx_total-1][nx_total-1] = -1.0

    #Create matrix_B
    matrix_B[0][0] = 1.0
    matrix_L[0][0] = 1.0
    monitor_points[0] = 1
    i = 1
    # print(vias)
    for node in vias_nodes:                       #via_nodes has the via nodes that are key to the dictionary vias
      segment = vias[node]
    #   print(f"{node}: {segment}")
      matrix_B[node-1][segment-2] = -1.0     #each via node is at the second segment that why we decrease 2 einai mia thesi pio mesa apo tin teleytaia stili poy einai segents-1 ara segments-2
      matrix_B[node-1][segment-1] = 1.0
      matrix_L[segment-1][node-1] = 1.0
      monitor_points[segment-1] = node
      i += 1
    matrix_B[nx_total-1][num_segments-1] = -1.0  #the last line of the array B
    matrix_L[num_segments][nx_total-1] = 1.0
    monitor_points[num_segments] = nx_total

    # print(vias_nodes)
    ########
    acoef = kappa/(dx*dx)
    bcoef = kappa * b / dx
    
    selected_line = os.path.splitext(os.path.basename(csv_filename))[0]

    # folder = self.project_location + "/" + "System" + "/"+selected_line
    # if not os.path.exists(folder):
    #   os.makedirs(folder)

    input_folder = self.project_location+"/"+"input"+"/"+selected_line+"/"+self.technology+"_"+str(self.temperature)+"_"+str(self.givenWidth)+"/"

    if not os.path.exists(input_folder):
      os.makedirs(input_folder)

    try:

      # Write matrix G
      filename=input_folder+"/"+"G.csv" #the G array has nx_total lines 
      with open(filename,"w")as f_G:
        i = j = 0
        for row in matrix_G:
          # loop through the columns of the row and write each element to the file
          j=0
          for item in row:
            if float(item) != 0.0:
              f_G.write(f"{i},{j},{item*acoef}\n")
            j += 1
          i += 1
        f_G.close()

      # Write matrix B
      filename=input_folder+"/"+"B.csv" #the B array has nx_total lines 
      with open(filename,"w")as f_B:
        i = j = 0
        for row in matrix_B:
          # loop through the columns of the row and write each element to the file
          j=0
          for item in row:
            if float(item) != 0.0:
              f_B.write(f"{i},{j},{item*bcoef}\n")
            j += 1
          i += 1
        f_B.close()

      # Write matrix L
      filename=input_folder+"/"+"L.csv" #the L array has num_segments+1 lines 
      with open(filename,"w")as f_L:
        i = j = 0
        for row in matrix_L:
          # loop through the columns of the row and write each element to the file
          j=0
          for item in row:
            if float(item) != 0.0:
              f_L.write(f"{i},{j},{item}\n")
            j += 1
          i += 1
        f_L.close()

      # Write vector u (curden)
      filename=input_folder+"/"+"curden.csv"  
      with open(filename, "w") as f_u:
        for value in curden:
          f_u.write(f"{value}\n")
      f_u.close()

      # Write vector monitor_points
      filename=input_folder+"/"+"monitor_points.csv"  
      with open(filename, "w") as f_u:
        for value in monitor_points:
          f_u.write(f"{value}\n")
      f_u.close()

      # Write analytical confugiration file
      filename = input_folder + "/analytical.txt"
      with open(filename,"w")as f_analytical:
        f_analytical.write(f"nx_total = {nx_total}\nAcoef = {acoef}\n")
        f_analytical.close()
    except PermissionError as e:
      print(f"File {filename} could not be opened. Check if it is opened by another application.")
      return(f"File {filename} could not be opened. Check if it is opened by another application.")
    except FileNotFoundError as e:
      print(f"File {filename} was not found in the system. Try performing discretization again.")
      return(f"File {filename} was not found in the system. Try performing discretization again.")
    except Exception as e:
      print(f"An error occured while writing file {filename}.")
      return(f"An error occured while writing file {filename}.")

    elapsed_time = time.time() - start_time
    # print("Going to peacefully return")
    return(f"{nx_total} nodes in {elapsed_time:.3f} seconds")