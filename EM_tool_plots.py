import csv
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from matplotlib.patches import Rectangle
from colorspacious import cspace_converter
from matplotlib.figure import Figure
matplotlib.use("Qt5Agg")

from random import randint
import numpy as np

from spice_function import *

title_fontdict = {
	"family": "Calibri",
	"size": 13,
	"weight": "bold",
}

label_fontdict = {
	#"family": "Calibri",
	"size": 11,
	"style": "normal",
}

ax = None
grid_state = True
def toggle_grid(new_state, canv):
    global ax, grid_state
    grid_state = new_state
    print(f"Going to change the state of the grid to {new_state}")
    print(f"ax: {ax}")
    ax.grid(new_state, which='both')
    canv.draw()

def plot_powergrid(qframe, benchmark, selected_line):
	line_data_list = []
	segments = []
	the_line = selected_line
	sub_folder = selected_line.split("_")[0]
	path_to_line_file = benchmark + "/" + sub_folder + "/" + the_line + ".csv"
	total_length = 0
	
	with open(path_to_line_file, newline ='') as file:
		reader = csv.DictReader(file)
		
		for row in reader:
			line_data_list.append(row)
			segments.append(int(row[" length"]))
			total_length = total_length + int(row[" length"])

	NUM_OF_VIAS = len(segments) + 1
	# line width
	width = 1

	# Compute total length of line
	length = 0
	for segment in segments:
		length += segment

	if (width/length) < 0.01:
		width = length*0.005
		
	# if width >= min(segments):
	# 	width = min(segments)*0.95
	# 	print("width set as min(segments)*0.95")

	# text_fontsize = 8
	text_fontsize = int(width*0.2)
	if text_fontsize > 10:
		text_fontsize = 10
	
	if text_fontsize < 8:
		text_fontsize = 8

	x_total = [-width/2, length+width/2, length+width/2, -width/2, -width/2]
	y_total = [-width/2, -width/2, width/2, width/2, -width/2]
	#y_total = [-width/2,-width/2, -1000 ,1000 , -width/2]

	# create a figure and add the square to it
	fig, ax = plt.subplots(dpi=100)
	fig.subplots_adjust(top=1, bottom=0.001, left=0.001, right=1, wspace=0.9, hspace=0.9)
	# fig.set_size_inches(15,15)

	# plot the line
	ax.plot(x_total, y_total, c='#222222', linewidth=1)

	# initialize x and y coordinates
	x = [0]
	y = [0]

	# display labels flag
	if len(segments) <= 1000:
		labels_flag = True
	else:
		labels_flag = False

	# calculate x and y coordinates for each segment
	i = 1
	rect_color = "black"
	prev_segment = 0

	for segment in segments:
		if i == 1:
			label_distance = 3
		elif prev_segment + 1 < x[-1] + segment:
			label_distance = 0
		else:
			label_distance = 5
			
		rect = Rectangle((x[-1]-width/1,y[-1]-width/2),width/1,width,color=rect_color, alpha=0.7)
		ax.add_patch(rect)  

		if labels_flag:
			label_text = f'{i}'
			label_pos = (x[-1],y[-1]+5*width)
			ax.annotate(label_text, xy=label_pos, xytext=label_pos, ha='left', va='top',
				bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='gray', lw=1))

		x.append(x[-1]+segment)
		y.append(y[-1])
		
		i += 1
		prev_segment = x[-1]+segment
	
	if prev_segment + 2 < x[-1] + segment:
		label_distance = 0
	else:
		label_distance = 2
	
	rect = Rectangle((x[-1]+width/2,y[-1]-width/2),width/1,width,color=rect_color, alpha=0.7)
	ax.add_patch(rect) 

	if labels_flag:
		label_text = f'{i}'
		label_pos = (x[-1],y[-1]+5*width)
		ax.annotate(label_text, xy=label_pos, xytext=label_pos, ha='left', va='top',
				bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='gray', lw=1))

	plt.ylim(min(y_total)-width*8,max(y_total)+width*5)
	plt.xlim(-width*7,length+width*7)
	# plt.xlabel("Distance from origin (um)", fontdict=label_fontdict)
	plt.gca().spines['top'].set_visible(False)
	plt.gca().spines['left'].set_visible(False)
	plt.gca().spines['right'].set_visible(False)
	plt.gca().set_yticks([])

	fig.set_facecolor("#F6F6F6") 
	ax.set_facecolor("#F0F0F0")
	ax.set_aspect('equal')

	fig.tight_layout()
	plt.tight_layout()

	return fig, total_length, NUM_OF_VIAS

def create_heatmap(data, N):
	# Create the heatmap plot
	fig, ax = plt.subplots(nrows=1, figsize=(10, 2.1), dpi=100)
	# fig.subplots_adjust(top=1 , bottom=0, left=0, right=0.1)
	# fig.subplots_adjust(left=0, bottom=0, top=1, right=0.8)
	# ax.set_title(f'Heatmap', fontsize=14)
	im = ax.imshow(data, aspect='auto', cmap=matplotlib.colormaps['turbo'])
	ax.yaxis.set_visible(False)
	# ax.set_xlim(0,N)
	ax.set_xticks(np.linspace(0, N, 20))
	plt.xlabel('discretization point (um)', font=label_fontdict)
	# Add a colorbar to the plot
	cbar = fig.colorbar(im, anchor=(0,1), fraction=0.05)
	cbar.ax.get_yaxis().labelpad = 15
	cbar.ax.set_ylabel('hydrostatic stress (Pa)', rotation=270)
	# ax.text(-0.01, 0.5, 'turbo', va='center', ha='right', fontsize=10, transform=ax.transAxes)
	fig.tight_layout()
	return fig, ax

def create_transient(timestep, x, y):
	global ax, grid_state

	# Plot the data
	fig, ax = plt.subplots(nrows=1, dpi=100)
	x = timestep * x
	ax.grid(grid_state, which='both')

	# Create a numpy array of y values
	ax.plot(x, y, marker='.', markersize=9, lw=2)

	# ax.set_ylim(min(y)*0.999, max(y)*1.001)
	# ax.set_xlim(min(x)*0.999, max(x)*1.001)

	plt.xlabel("Time (s)", fontdict=label_fontdict)
	plt.ylabel("Hydrostatic stress (Pa)", fontdict=label_fontdict)

	# ax.grid(False)
	fig.tight_layout()
	return fig, ax


