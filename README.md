# PROTON
PROTON - A Python Framework for Physics-Based Electromigration Assessment on Contemporary VLSI Power Grids

PROTON is an _open-source_ cross-platform EDA tool for  Electromigration (EM) assessment in contemporary VLSI power grids. The main key points of this tool are:
- PROTON can be straightforwardly integrated into any commercial design flow for physical synthesis in order to calculate the EM stress since it only requires files in SPICE format and the corresponding currents. 
- It employs a complete set of accurate numerical and analytical techniques, that can significantly reduce the simulation complexity of large-scale EM problems. In particular, the analytical solution used for the line analysis is exact for the chosen spatial discretization guaranteeing a perfectly accurate and robust solution.
- It is built with an easy-to-use interface, that allows the user to explore different EM stress scenarios, for multiple time stamps, providing plots for the physical structures of the power grid.

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
   - path/to/oneAPI/Intel/mkl/latest/redist/intel64
   - path/to/oneAPI/Intel/compiler/latest/windows/redist/intel64_win/compile

### Linux
1. After the installation of Intel onAPI, try sourcing the top-level `vars.sh` script with `. path/to/intel/oneapi/mkl/latest/env/vars.sh`. This command sets the ONEAPI_ROOT variable.

## Installation Guide (Windows/Linux)
In order to create the executable for PROTON, the following steps need to be run (provided that the above requirements are met):
1. Clone/Download this repo. _Note_ that the location of the cloned/downloaded repo is going to be the same as the installation folder
2. Double-click on `PROTON_installer.py` or navigate to the folder of the repo and run `python PROTON_installer.py`. The executable is then created at the top level of the repo directory under the name `PROTON.exe` for Windows and `PROTON` for Linux.
3. The user can create a shortcut to the executable or add the folder to the environment variables (or use the `export` command in `~/.bashrc` for Linux) in order to run it from anywhere in the system


### Windows
In order to check for the dependencies, try executing the C kernels by themselves. That means to execute:
`./path/to/PROTON/bin/EMtool_analytical.exe` for the line analysis C kernel
`./path/to/PROTON/bin/EMtool_MOR.exe` for the MOR C kernel (point analysis)

### Linux
Analogously for Linux, execute:
`./path/to/PROTON/bin/EMtool_analytical` for the line analysis C kernel
`./path/to/PROTON/bin/EMtool_MOR` for the MOR C kernel (point analysis)


