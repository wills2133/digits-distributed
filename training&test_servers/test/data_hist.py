import os
from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import numpy as np
import math

def draw_hist(filename, frames):
	# print frames
	fig = plt.figure(1)
	ax1 = plt.subplot(111)
	bins = int( math.ceil( frames[-1] / 750 ) )
	max_frame = bins * 750

	ax1.hist(frames, bins, range=[0, max_frame], normed=False, histtype='bar', 
		facecolor='lightblue', alpha=1)
	ax1.set_xlabel('frame', horizontalalignment='right')
	ax1.set_ylabel('pedestrian num')
	ax1.set_title('Pedestrian Statistic')
	xmajorLocator = MultipleLocator(750)
	# xmajorFormatter = FormatStrFormatter('%5.1f')
	ax1.xaxis.set_major_locator(xmajorLocator)
	# ax1.xaxis.set_major_formatter(xmajorFormatter)
	ax1.xaxis.grid(True, which='major')
	# fig.subplots_adjust(bottom=0.2)
	plt.savefig('./figures/' + filename + '.jpg')
	# plt.show()
	plt.close()

def get_data_hist(data_dir):
	filename_set = os.listdir(data_dir)
	filenames = sorted(filename_set)
	dict_calss_labels = {} # record all classes
	f2 = open('./new_annot.txt', 'w')
	for file in filenames:
		print file
		filepath = os.path.join(data_dir,file)
		f = open(filepath)
		lines = f.readlines()
		num_obj = lines[0]
		frames = []
		for line in lines:
			items = line.split()
			for n in range( int(items[2]) ):
				frames.append( int(items[1]) )
		f.close()
		
		draw_hist(file, frames)
	f2.close()

if __name__ == '__main__':
    get_data_hist('./CountDataLogs')