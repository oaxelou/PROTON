#******Just for verification purposes***** 
from scipy.sparse import csc_matrix
from scipy.sparse import coo_matrix
import scipy.sparse as sparse
import numpy as np
import dask.dataframe
from pathlib import Path
from matplotlib import pyplot as plt
import time
import sys
import os
from scipy.linalg import cho_factor, cho_solve
from sksparse.cholmod import cholesky
from decimal import Decimal
from collections import defaultdict


import enum
# Using enum class create enumerations
class system(enum.Enum):
   Original = 1
   Reduced = 2

class Monitor_struct:
  name = ''
  values = None # list cannot be initialized here!


debug = False

PLOT_FLAG = False

class TransientSolver:


    #TransientSolver constructor 
    def __init__(self, system, mnt_point_file, curden_file, path_to_input, path_to_output, step_time, end_time):
        self.system = system
        self.mnt_point_file = mnt_point_file
        self.curden_file = curden_file
        self.path_to_input = path_to_input
        self.path_to_mna_system = path_to_input
        self.step_time = step_time
        self.end_time = end_time
        self.parse_mna_system();

    def parse_mna_system(self):
	
        if self.system == system.Original:
            if debug:
                print("\nReading the original model")
        else:
            if debug:
                print("\nReading the reduced model")
        # read conductance and capacitance table for original and reduced-order model
        
        if self.system == system.Original:
            dataG = dask.dataframe.read_csv(self.path_to_mna_system + 'G.csv', header=None)
            # dataC = dask.dataframe.read_csv(self.path_to_mna_system + 'C.csv', header=None)
        else:
            dataG = dask.dataframe.read_csv(self.path_to_mna_system + 'Gr.csv', header=None)
            dataC = dask.dataframe.read_csv(self.path_to_mna_system + 'Cr.csv', header=None)

        #dataG.info()
        #dataG.describe()
        
        #Get three vectors of rows , columns and values for G matrix 
        dataG = dataG.compute()
        rowsG = dataG.loc[:,0]
        rowsG = rowsG.values
        colsG = dataG.loc[:,1]
        colsG = colsG.values
        valsG = dataG.loc[:,2]
        valsG = valsG.values
        
        
        #dataC.info()
        #dataC.describe()
        
        # #Get three vectors of the rows , columns and values for C matrix 
        # dataC = dataC.compute()
        # rowsC = dataC.loc[:,0]
        # rowsC = rowsC.values
        # colsC = dataC.loc[:,1]
        # colsC = colsC.values
        # valsC = dataC.loc[:,2]
        # valsC = valsC.values

        #Construct Compressed Sparse Column Format  matrices G and C for original model for parametric and non parametric parts
        if self.system == system.Original:
            self.nodes = len(np.unique(colsG))
            self.G_matrix = coo_matrix((valsG,(rowsG,colsG)),shape=(self.nodes,self.nodes)).tocsc()#*3.35858091121507e-21
            # self.C_matrix = coo_matrix((valsC,(rowsC,colsC)),shape=(self.nodes,self.nodes)).tocsc()
            self.C_matrix = sparse.eye(self.nodes, format='coo').tocsc()

            # if np.allclose(self.C_matrix.todense(), self.C_matrix_eye.todense()):
            #     print("The matrices are equal")
            # else:
            #     print("Matrices are not equal")

            if debug:
                print(f"G original:\n{self.G_matrix.toarray()}")
                print(f"C original:\n{self.C_matrix.toarray()}")
        #Construct dense G and C matrices for reduced model for parametric and non parametric parts
        elif  self.system == system.Reduced:
            # Get three vectors of the rows , columns and values for C matrix 
            dataC = dataC.compute()
            rowsC = dataC.loc[:,0]
            rowsC = rowsC.values
            colsC = dataC.loc[:,1]
            colsC = colsC.values
            valsC = dataC.loc[:,2]
            valsC = valsC.values

            self.nodes = len(np.unique(colsG))
            self.G_matrix = coo_matrix((valsG,(rowsG,colsG)),shape=(self.nodes,self.nodes)).todense()#*3.35858091121507e-21
            self.C_matrix = coo_matrix((valsC,(rowsC,colsC)),shape=(self.nodes,self.nodes)).todense()
            # self.C_matrix_eye = sparse.eye(self.nodes, format='coo').todense()

            # if np.allclose(self.C_matrix, self.C_matrix_eye):
            #     print("The matrices are equal")
            # else:
            #     print("Matrices are not equal")

            if debug:
                print(f"G reduced:\n{self.G_matrix}")
                print(f"C reduced:\n{self.C_matrix}")



        # B - read power distribution table
        if self.system == system.Original:
            #print("\nReading the original power distribution reduced matrix in triplet format...\n" + self.path_to_mna_system + "B.csv")
            dataB = dask.dataframe.read_csv(self.path_to_mna_system + 'B.csv', header=None)
        elif  self.system == system.Reduced:
            #print("\nReading the reduced power distribution matrix in triplet format...\n" + self.path_to_mna_system + "Br.csv")
            dataB = dask.dataframe.read_csv(self.path_to_mna_system + 'Br.csv', header=None)
            
        #Get three vectors of the rows , columns and values for B matrix  
        dataB = dataB.compute()
        rowsB = dataB.loc[:,0]
        rowsB = rowsB.values
        colsB = dataB.loc[:,1]
        colsB = colsB.values
        valsB = dataB.loc[:,2]
        valsB = valsB.values
        self.ports = len(np.unique(colsB))
        
        #Construct B matrix in Compressed Sparse Column Format for original system and B dense for reduced-order 
        if self.system == system.Original:
            self.B_matrix = coo_matrix((valsB,(rowsB,colsB)),shape=(self.nodes,self.ports)).tocsc()
        elif self.system == system.Reduced:
            self.B_matrix = coo_matrix((valsB,(rowsB,colsB)),shape=(self.nodes,self.ports)).todense()


        # L - read node-connectivity nodes
        if self.system == system.Original:
            #print("\nReading the original state-to-output connectivity matrix in triplet format...\n" + self.path_to_mna_system + "L.csv");
            dataL = dask.dataframe.read_csv(self.path_to_mna_system + 'L.csv', header=None)
        elif  self.system == system.Reduced:
            #print("\nReading the reduced state-to-output connectivity matrix in triplet format...\n" + self.path_to_mna_system + "Lr.csv")
            dataL = dask.dataframe.read_csv(self.path_to_mna_system + 'Lr.csv', header=None)
        
        #Get three vectors of the rows , columns and values for L matrix       
        dataL = dataL.compute()
        rowsL = dataL.loc[:,0]
        rowsL = rowsL.values
        colsL = dataL.loc[:,1]
        colsL = colsL.values
        valsL = dataL.loc[:,2]
        valsL = valsL.values 
        self.mnt_points = len(np.unique(rowsL))
        
        #Construct L matrix in Compressed Sparse Column Format for original system and L dense for reduced
        if self.system == system.Original:
            self.L_matrix = coo_matrix((valsL,(rowsL,colsL)),shape=(self.mnt_points,self.nodes)).tocsc()
            if debug:
                print(self.L_matrix.toarray())
                print(f"L original:\n{self.L_matrix.toarray()}")
        elif self.system == system.Reduced:
            self.L_matrix = coo_matrix((valsL,(rowsL,colsL)),shape=(self.mnt_points,self.nodes)).todense()
            if debug:
                print(f"L reduced:\n{self.L_matrix}")


        # read monitor points
        monitor_points_data = dask.dataframe.read_csv(self.mnt_point_file, header=None)
        monitor_points_data = monitor_points_data.compute()
        vectorMnt_points = monitor_points_data.loc[:,0]
        vectorMnt_points = vectorMnt_points.values
        self.initialize_monitor_points(vectorMnt_points)

        # read Ut 
        dataU = dask.dataframe.read_csv(self.curden_file, header=None)
        dataU = dataU.compute()
        vectorU = dataU.loc[:,0]
        self.vectorU = vectorU.values
        if debug:
            print(f"vectorU: {self.vectorU}")


    
    def initialize_monitor_points(self, vectorMnt_points):
        self.all_monitor_points = []
        for i in range(0,self.mnt_points):
            each_monitor_point = Monitor_struct()
            each_monitor_point.name = str(int(vectorMnt_points[i]))
            each_monitor_point.values = []
            self.all_monitor_points.append(each_monitor_point)

    def get_monitor_points(self):
        return self.all_monitor_points
    
    def get_time_vector(self):
        return self.time_vector

    def backward_euler(self):
        # self.newRHS =  self.initial_rhs +  self.Ch_matrix.dot( self.current_solution)
        self.newRHS =  self.initial_rhs.dot(self.step_time) + self.current_solution
        self.cur_time = self.cur_time + self.step_time


    def exec_transient(self):
        #Transient analysis for original model
        if self.system == system.Original:
            original_time = time.time()
            #Set 1/h * C matrix for the desired time step
            self.Ch_matrix =  self.C_matrix/self.step_time
            #Set Transient Analysis system matrix
            # self.tran_matrix = self.G_matrix + self.Ch_matrix
            self.tran_matrix = self.C_matrix - self.G_matrix.dot(self.step_time)
            self.cur_time = 0.0
            self.time_vector = [self.cur_time]
            
            #Performing factorization of original transient matrix using cholesky factorization
            cholesky_time = time.time()
            factor = cholesky(self.tran_matrix,use_long=True)
            if debug:
                print('\n*** Transient simulation of the original model ***')
                print("Factorization runtime: %s seconds" % (time.time() - cholesky_time))
               
            #Initialize rhs vector to B*Ut
            self.initial_rhs = self.B_matrix.dot(self.vectorU)
            #Set initial solution to zero 
            self.current_solution = np.zeros(self.nodes)

            #Compute the inital solution  y = L*x 
            y = self.L_matrix.dot(self.current_solution)
            
            # save the current solution for each monitor points
            for i in range(0,self.mnt_points):
                self.all_monitor_points[i].values.append(y[i])
            #update rhs based on backward euler method
            self.backward_euler()

            
            #Transient simulation loop 
            total_time = 0.0 
            while self.cur_time <= self.end_time:
                self.time_vector.append(self.cur_time)
                
                # Solve the trasient matrix for updated rhs vector  for t = cur_time
                solve_time = time.time()
                self.current_solution = factor(self.newRHS)
                total_time = total_time + time.time() - solve_time
                
                # Compute the solution for each time step y = L*x
                y = self.L_matrix.dot(self.current_solution)

                if debug:
                    print(f"{self.cur_time}/{self.end_time}: {y}")
                # save the current solution for each monitor points
                for i in range(0,self.mnt_points):
                    self.all_monitor_points[i].values.append(y[i])
                
                #update rhs based on backward euler method
                self.backward_euler()
            
            if debug:
                print("Simulation runtime for each timestep: %s seconds" % (total_time /( len(self.time_vector) -1)))
                print("Total transient runtime of the original model: %s seconds" % (time.time() - original_time))
        #Transient analysis for reduced-order model
        elif self.system == system.Reduced:
            reduced_time = time.time()
            #Set 1/h * C matrix for the desired time step
            self.Ch_matrix =  self.C_matrix/self.step_time
            #Set Transient Analysis matrix
            # self.tran_matrix = self.G_matrix + self.Ch_matrix
            self.tran_matrix = self.C_matrix - self.G_matrix.dot(self.step_time)
            self.cur_time = 0.0
            self.time_vector = [self.cur_time]
            
            #Performing factorization of reduced transient matrix using cholesky factorization
            if debug:
                print('\n*** Transient simulation of the reduced model ***')
            cholesky_time = time.time()
            self.c, self.low = cho_factor(self.tran_matrix)
            Factorization_time = time.time() - cholesky_time
            if debug:
                print("Factorization runtime: {0:.18F}".format(Factorization_time)," seconds")
            
            #Initialize rhs vector to B*Ut 
            self.initial_rhs = self.B_matrix.dot(self.vectorU).transpose()
            self.current_solution = np.zeros([self.nodes,1])
            
            #Compute the inital solution  y = L*x
            y = self.L_matrix.dot(self.current_solution) 

            # save the current solution for each monitor points
            for i in range(0,self.mnt_points):
                self.all_monitor_points[i].values.append(y[i,0])
            # update rhs based on backward euler method 
            self.backward_euler()
            
            #Transient simulation loop
            total_time = 0.0 
            while self.cur_time <= self.end_time:
                self.time_vector.append(self.cur_time)
                
                # Solve the trasient matrix for updated rhs vector  for t = cur_time
                solve_time = time.time()
                self.current_solution = cho_solve((self.c, self.low), self.newRHS)
                total_time = total_time + time.time() - solve_time
                
                #  Compute the solution for each time step y = L*x
                y = self.L_matrix.dot(self.current_solution)

                if debug:
                    print(f"{self.cur_time}/{self.end_time}: {y}")
                # Save the current solution for each monitor points
                for i in range(0,self.mnt_points):
                    self.all_monitor_points[i].values.append(y[i,0])
                
                #update rhs
                self.backward_euler()
                
            if debug:
                print("Simulation runtime for each timestep: %s seconds" % "{0:.18F}".format(total_time /( len(self.time_vector))))
                print("Total transient runtime of the reduced model: %s seconds" % (time.time() - reduced_time))


#********************* Configuration Parameters *******************************# 

if len(sys.argv) != 2 :
    # print("Invalid number of arguments. Correct usage: python simulation.py <model> <benchmark> <end time (s)> <step time (s)>")
    print("Invalid number of arguments. Correct usage: python simulation.py <config file>")
    sys.exit(0)

config_file = sys.argv[1]
# config_file = "C:/Users/olymp/Desktop/check_B/numerical.cfg"
try:
    with open(config_file, "r") as f:
        lines = f.readlines()

    config = {}
    for line in lines:
        key, value = line.strip().split(" ")
        config[key] = value

    # Get the values of the keys you're interested in
    input_files = config["input_files"]
    output_files = config["output_files"]
    end_time = float(config["simulation_time"])
    step_time = float(config["timestep"])
    EXEC_ORIGINAL = True if config["is_original"] == "True" else False
except Exception as e:
    print("An unexpected error occured. Terminated with errors")
    exit(1)

#Set path where monitor points matrix is saved 
mnt_point_file = config["input_files"] + '/monitor_points.csv'
curden_file = config["input_files"] + '/curden.csv'
input_files = config["input_files"] if config["is_original"] == "True" else config["reduced_matrices"]

#Set path where original and reduced matrices are saved
path_to_output = output_files


#**************************************************************************# 
if EXEC_ORIGINAL:
    # Calling the transient constructor for the original MNA system
    try:
        tran_solver_original = TransientSolver( system.Original, mnt_point_file, curden_file, input_files, path_to_output,step_time, end_time)
    except ValueError as ex :
        exit(2)

    # Performing transient analysis for the original MNA system
    tran_solver_original.exec_transient()

    # Returning the transient analysis results for the original MNA system
    monitor_points_original = tran_solver_original.get_monitor_points()

    time_vector = tran_solver_original.get_time_vector()

else:
    # Calling the transient constructor for the reduced-order MNA system
    tran_solver_reduced = TransientSolver( system.Reduced, mnt_point_file, curden_file, input_files, path_to_output,step_time, end_time)

    # Performing transient analysis for the reduced-order MNA system
    tran_solver_reduced.exec_transient()

    # Returning the transient analysis results for the reduced-order MNA system
    monitor_points_reduced = tran_solver_reduced.get_monitor_points()

    time_vector = tran_solver_reduced.get_time_vector()
  
if EXEC_ORIGINAL:
    monitor_points = monitor_points_original
    #Create directory for plot storing 
    Path(path_to_output + 'transient/original/').mkdir(parents=True, exist_ok=True)
else:
    monitor_points = monitor_points_reduced
    #Create directory for plot storing 
    Path(path_to_output + 'transient/reduced/').mkdir(parents=True, exist_ok=True)

# print("Monitor points values:")
for i in range(0,len(monitor_points)):
    if PLOT_FLAG:
        plt.clf()
        if EXEC_ORIGINAL:
            monitor_point = monitor_points_original[i].name
            plt.plot(time_vector, monitor_points_original[i].values,  color='b', linewidth=2,label='Original Model')
            # print(monitor_points_original[i].values)
        else:
            monitor_point = monitor_points_reduced[i].name
            plt.plot(time_vector, monitor_points_reduced[i].values,  color='r', linewidth=2,linestyle=':',label='ROM')
            # print(monitor_points_reduced[i].values)
        plt.title('Transient response of node ' + monitor_point)
        plt.ylabel('Hydrostatic stress (Pa)')
        plt.xlabel('Time(s)')
        plt.grid() 
        plt.xlim(1, end_time)
        plt.legend()
    
    if EXEC_ORIGINAL:
        filename = path_to_output + 'transient/original/' + str(i+1)
        sim_time_filename = path_to_output + 'transient/original/simulation_time.txt'
        if PLOT_FLAG:
            plt.savefig(filename +'.png')
        with open(filename +'.txt', 'w') as results_file:
            for j in range(0, len(time_vector)):
                results_file.write(str(monitor_points_original[i].values[j]) + "\n")
        results_file.close()


    else:
        filename = path_to_output + 'transient/reduced/' + str(i+1)
        sim_time_filename = path_to_output + 'transient/reduced/simulation_time.txt'
        if PLOT_FLAG:
            plt.savefig(filename +'.png')
        with open(filename +'.txt', 'w') as results_file:
            for j in range(0, len(time_vector)):
                results_file.write(str(monitor_points_reduced[i].values[j]) + "\n")
        results_file.close()

    
    with open(sim_time_filename, 'w') as results_file:
        for timepoint in time_vector:
            results_file.write(str(timepoint) + "\n")
    results_file.close()