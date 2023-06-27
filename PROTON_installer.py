#  PROTON Installer
# Simply double click on PROTON_installer.py or run the command: python PROTON_installer.py
# to create the PROTON executable.
# 
# Comment: One can also run the tool directly from the python script PROTON_main.py
#
# Author: Olympia Axelou
# Affiliation: University of Thessaly, Greece
# Date: 19/6/2023

import os
import time
from sys import platform

print("Installing PROTON...")

with open('produce_executable.sh', 'r') as f:
    lines = f.readlines()

pyinstaller_command = ""
for line in lines:
    if line.split()[0] == "pyinstaller":
        pyinstaller_command = line
        break

if not pyinstaller_command:
    print("There was an error with produce_executable.sh file. Terminating the installation.")
    time.sleep(1)
    exit(1)
os.system(pyinstaller_command)

if not os.path.exists('dist/PROTON.exe'):
    print("There was an error with the executable file. Terminating the installation.")
    input("Press any key to exit...")
    exit(1)

# Move executable 
if platform == "win32":
    os.system('move .\dist\PROTON.exe .')

# Delete dist folder
if platform == "win32":
    os.system('del /F /Q dist')

exe_abs_path = os.path.abspath("PROTON.exe")
print(f"\nPROTON has been successfully installed.")
print(f"Executable of the file can be found at {exe_abs_path}")

input("Press any key to exit...")