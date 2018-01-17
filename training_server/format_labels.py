import os
import PIL
import shutil
# pred_label_file_dir = './Labels'
# gr_truth_label_file_dir = './Labels'
# false_alarm_dir = './labels_false_alarm' #dir to save false alarm labels
# miss_det_dir = './labels_miss_detect' #dir to save miss detection labels
use_same_dir = False #use same dir for pred_label_file_dir and gr_truth_label_file_dir for testing
threshold_error = 50 #pixel, thresold to decide whether a detection is correct
# sum of error between detectd object and ground truth ojbect in height and width


def format_labels(gt_lbl_path):

	# img = PIL.Image.open()
	img_w = 1152#img.size[0]
	img_h = 648#img.size[1]

	gr_truth_label_file_dir = gt_lbl_path

	filename_set = os.listdir(gr_truth_label_file_dir)
	filenames = sorted(filename_set)
	dict_calss_labels = {} # record all classes
	f2 = open('./new_annot.txt', 'w')
	frame_num = 1
	for file in filenames:
		# print filenames
		filepath = os.path.join(gr_truth_label_file_dir,file)
		f = open(filepath)
		lines = f.readlines()
		num_obj = lines[0]
		label = []
		for n in range(1, int(num_obj)+1):
			items = lines[n].split()
			x = float(items[1]) * img_w
			y = float(items[2]) * img_h
			w = float(items[3]) * img_w
			h = float(items[4]) * img_h
			f2.write( '{} -1 {} {} {} {} {} -1 -1 -1\n'.format(frame_num, x, y, w, h, items[-1]) )
		frame_num += 1
		f.close()
	f2.close()
	


if __name__ == '__main__':
    format_labels('./Labels')