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
#Scikit.sparse: navigate to the path/to/PROTON/simulation/scikit.sparse-master and install Scikit.sparse by running the python script setup.py:
#>python setup.py install
#The above command, requires the python's version to be ">=3.6, <3.10", the "numpy>=1.13.3" and the "scipy>=0.19".

#How to test the dependencies for the application:

#Open a command prompt and run the Python script simulation.py:
#>python simulation.py
