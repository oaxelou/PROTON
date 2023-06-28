# PROTON
A Python Framework for Physics-Based Electromigration Assessment on Contemporary VLSI Power Grids

PROTON is an _open-source_ cross-platform EDA tool for  Electromigration (EM) assessment in contemporary VLSI power grids. The main key points of this tool are:
- PROTON can be straightforwardly integrated into any commercial design flow for physical synthesis in order to calculate the EM stress since it only requires files in SPICE format and the corresponding currents. 
- It employs a complete set of accurate numerical and analytical techniques, that can significantly reduce the simulation complexity of large-scale EM problems. In particular, the analytical solution used for the line analysis is exact for the chosen spatial discretization guaranteeing a perfectly accurate and robust solution.
- It is built with an easy-to-use interface, that allows the user to explore different EM stress scenarios, for multiple time stamps, providing plots for the physical structures of the power grid.

## Table of Contents:
- [Requirements](#requirements)
- [Installation guide](#installation_guide)
- [Custom C/C++ kernel integration](#custom_kernels)
  - [Line analysis](#custom_kernel_line)
  - [Model Order Reduction](#custom_kernel_mor)

<a name="requirements"/>

## Requirements
In order to run the tool, the following requirements are needed:

### Cross-platform (Windows/Linux):
1. The python packages in `requirements.txt`. In order to install them in bulk, execute `pip install -r requirements.txt`.
2. Given `$installation_dir` the installation directory, run `python $installation_dir/simulation/setup.py`.
3. Install the Eigen library from [Eigen download page](http://eigen.tuxfamily.org/index.php?title=Main_Page#Download).
4. Install FFTW library from [FFTW download page](https://fftw.org/download.html).
5. Install Intel oneAPI (for MKL) from [Intel oneAPI download page](https://www.intel.com/content/www/us/en/developer/articles/guide/installation-guide-for-oneapi-toolkits.html).

### Windows
1. For Intel oneAPI, the following paths must be added to the system's PATH environment variables (for `mkl_avx2.1.dll`, `mkl_core.1.dll`, `mkl_def.1.dll`, `mkl_intel_thread.1.dll`, `libiomp5md.lib`):
   - `path/to/oneAPI/Intel/mkl/latest/redist/intel64`
   - `path/to/oneAPI/Intel/compiler/latest/windows/redist/intel64_win/compile`

### Linux
1. After the installation of Intel onAPI, try sourcing the top-level `vars.sh` script with `. path/to/intel/oneapi/mkl/latest/env/vars.sh`. This command sets the ONEAPI_ROOT variable.

<a name="installation_guide"/>
## Installation Guide (Windows/Linux)
In order to create the executable for PROTON, the following steps need to be run (provided that the above requirements are met):
1. Clone/Download this repo. _Note_ that the location of the cloned/downloaded repo is going to be the same as the installation folder
2. Double-click on `PROTON_installer.py` or navigate to the folder of the repo and run `python PROTON_installer.py`. The executable is then created at the top level of the repo directory under the name `PROTON.exe` for Windows and `PROTON` for Linux.
3. The user can create a shortcut to the executable or add the folder to the environment variables (or use the `export` command in `~/.bashrc` for Linux) in order to run it from anywhere in the system


### Windows
In order to check for the dependencies, try executing the C kernels by themselves. That means to execute:
- `./path/to/PROTON/bin/EMtool_analytical.exe` for the line analysis C kernel
- `./path/to/PROTON/bin/EMtool_MOR.exe` for the MOR C kernel (point analysis)

### Linux
Analogously for Linux, execute:
- `./path/to/PROTON/bin/EMtool_analytical` for the line analysis C kernel
- `./path/to/PROTON/bin/EMtool_MOR` for the MOR C kernel (point analysis)


<a name="custom_kernels"/>
## Integration of custom C/C++ kernels
The user has the option to make use of custom C/C++ kernels of his/her choice. For this purpose, one can simply change the executable file (for Windows and/or Linux respectively) in `bin/` folder. 

<a name="custom_kernel_line"/>
### Line analysis
The line analysis C++ kernel calculates the EM diffusion stress using the implementation of the ICCAD2022 paper with title "A Novel Semi-Analytical Approach for Fast Electromigration Stress Analysis in Multi-Segment Interconnects". 

*Inputs*: It receives as input the `analytical.cfg` configuration file that is inside the corresponding line in the `input/` folder. For example, if we have selected line `M5_n0_3` with Al technology, at 378K and 1 line width, the analytical configuration file will be `project_folder/input/M5_n0_3/Al_378.0_1.0/analytical.cfg`. It contains the following info:
- `A_coeff`: The coefficient of matrix A 
- `num_nodes`: The number of discretization points
- `simulation_time`: The desired time for EM stress calculation
- `input_files`: The number of columns of matrix B.
It also receives as input files `B.csv` and `curden.csv` (which are in the same folder as `analytical.cfg`) and contain matrix `B` of size `num_nodes`x`input_files` and a vector of size `input_files` that contains the current densities at every segment of the line.

*Outputs*: It provides the stress at each discretization point of the line at stores it in the corresponding line's folder inside `output/` with the name `stress_<simulation_time>.txt`. For example, if we run the analytical function for the line above at t=100s, then the stress results will be in `project_folder/output/M5_n0_3/Al_378.0_1.0/stress_100.txt`.

<a name="custom_kernel_mor"/>
### MOR for point analysis
The Model Order Reduction (MOR) C++ kernel implements a Moment-Matching (MM) Extended Krylov Subspace (EKS) method, so that the transient analysis for all points on the line speed up.

*Inputs*: It receives as input the `mor.cfg` configuration file that is inside the corresponding line in the `input/` folder as explained above for the Line analysis C++ kernel. It contains the following info:
- `set_working_directory`: The directory of the project. E.g., if the project is located at `/home/proton/Desktop/first_project`, then this is given.
- `set_output_directory`: The output directory for the reduced matrices. For the above example's line, it would be `output/M5_n0_3/Al_378.0_1.0/reduced_matrices/`
- `set_G`: The location of matrix `A`. For the above example, it would be `input/M5_n0_3/Al_378.0_1.0/G.csv`. _Note_: matrix A is stored as G (simply another notation)
- `set_B`: The location of matrix `B`. For the above example, it would be `nput/M5_n0_3/Al_378.0_1.0/B.csv`.
- `set_L`: The location of matrix `L`. Same as `B`.
- `set_reduced_size`: The desired reduced size. 

*Outputs*: In folder set with `set_output_directory` command, the following reduced matrices are going to be stored:
- `Br.csv`
- `Gr.csv`
- `Cr.csv`
- `Lr.csv`

_Note_ that all original and reduced matrices are stored in sparse triplet format.
