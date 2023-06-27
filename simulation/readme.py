### Note that the Python simulation script (simulation.py) is only for verification purposes since the CHOLMOD solver comes with a GPL license ###

#Execution Prerequisites:

#Prior to the execution of simulation.py, do the following steps:
#Install the Visual Studio https://visualstudio.microsoft.com/downloads/ (recommended version: 16.9). Make sure to check the box "Desktop Development with C++" while choosing which Workloads to install.
#Numpy: pip install numpy
#Cython:pip install cython
#Scipy :pip install scipy
#Pandas: pip install pandas
#Dask:pip install dask
#Matplotlib:pip install matplotlib
#Scikit.sparse: navigate to the path/to/RΟΜ_generation_tool/simulation/scikit.sparse-master and install Scikit.sparse by running the python script setup.py:
#>python setup.py install
#The above command, requires the python's version to be ">=3.6, <3.10", the "numpy>=1.13.3" and the "scipy>=0.19".

#Python simulation script setup:

#The python script is taking as an input argument the "parametric_parts.csv" file which contains the parametric parts and the scaling factors for both the capacitance and the conductance matrices.
#The format of the input file for each row is: <parametric part name>,<capacitance scaling factor>,<conductance scaling factor>.
#The mnt_point_file variable must be set to the full_path/to/monitor_points_file.csv containing the monitor points. 
#The step_time variable determines the timestep of the transient simulation.
#The end_time variable determines the end time of transient simulation.
#The ambient_temp variable is set to the desired ambient temperature.
#The parameters[<non_parametric_parts>], parameters[<first_parametric_part>], … , parameters[<last_parametric_part>] variables determine the desired capacitance and conductance scaling factors for the parametric parts according to the input file "parametric_parts.csv" (also defined in the .cfg of the ROM_generation_tool).
#The parameters['0'] represents the non-parametric parts.
#Outputs of the Python simulation script:

#The Python simulation script produces the transient analysis plots for every monitor point and saves the corresponding .png figures into the full_path/to/output/simulation/. 
#The script also computes the mean and maximum relative error between the original model and the ROM while also providing some runtime results.

#How to run the application:

#Open a command prompt into  path/to/ROM_generation_tool/simulation and run the python script simulation.py:
#>python simulation.py parametric_parts.csv
