import os
import PIL
import shutil
# pred_label_file_dir = './Labels'
# gr_truth_label_file_dir = './Labels'
# false_alarm_dir = './labels_false_alarm' #dir to save false alarm labels
# miss_det_dir = './labels_miss_detect' #dir to save miss detection labels
use_same_dir = False #use same dir for pred_label_file_dir and gr_truth_label_file_dir for testing
threshold_error = 10 #pixel, thresold to decide whether a detection is correct
# sum of error between detectd object and ground truth ojbect in height and width



def count_dict(list_x, dict_x):
	if list_x[0] in dict_x:
		dict_x[list_x[0]] += 1
	else:
		dict_x[list_x[0]] = 1

## calculate the sum error between detectd object and ground truth ojbect in height and width
def box_error(list_predict, list_truth, img_width, img_height):
	mat_coeff = zip( list_predict[1:], list_truth[1:], 
		[img_width, img_height, img_width, img_height,] )
	error = lambda x: ( abs( x[0] - x[1] ) ) * x[2]
	# print map( error, mat_coeff )
	sum_error = sum( map( error, mat_coeff ) )
	return sum_error

def cal_average_rate(name, dict_rate_list, dict_calss_labels, dict_class_rate):

	for key in dict_calss_labels:
		average_rate = sum( dict_rate_list[key] ) / len( dict_rate_list[key] )
		# print name.ljust(17), key.ljust(20), average_rate

		if key in dict_class_rate:
			dict_class_rate[key].append( ( name.ljust(17) + str(average_rate) ) )
		else:
			dict_class_rate[key] = [ ( name.ljust(17) + str(average_rate) ) ]


def calculate_map(gt_lbl_path, pd_lbl_path):

	# img = PIL.Image.open()
	img_w = 1152#img.size[0]
	img_h = 648#img.size[1]

	pred_label_file_dir = pd_lbl_path
	gr_truth_label_file_dir = gt_lbl_path
	false_alarm_dir = gt_lbl_path + '/../'  + 'labels_false_alarm' #dir to save false alarm labels
	miss_det_dir = gt_lbl_path + '/../' + 'labels_miss_detect' #dir to save miss detection labels
	performance_data_dir = gt_lbl_path + '/../' + 'performance_data.txt'
	##### save ground label to dict

	### get filepath
	filename_set = os.listdir(gr_truth_label_file_dir)
	gr_truth_dict = {}
	filenames = sorted(filename_set)
	dict_calss_labels = {} # record all classes
	for file in filenames:
		filepath = os.path.join(gr_truth_label_file_dir,file)
		f = open(filepath)
		lines = f.readlines()
		num_obj = lines[0]
		label = []
		for n in range(1, int(num_obj)+1):
			items = lines[n].split()
			label.append([items[0]] + map(float, items[1:]))
			count_dict(items[0], dict_calss_labels)
		gr_truth_dict[file] = label
		f.close()
	#####  save perdict label to dict

	### get filepath
	filename_set2 = os.listdir(pred_label_file_dir)
	predict_dict = {}
	filenames2 = sorted(filename_set2)
	for file in filenames2:
		filepath = os.path.join( pred_label_file_dir, file )
		f = open(filepath)
		lines = f.readlines()
		num_obj = lines[0]
		label = []
		for n in range(1, int(num_obj)+1):
			items = lines[n].split()
			label.append([items[0]] + map(float, items[1:]))
		predict_dict[file] = label
		f.close()

	# record all classes
	dict_calss_labels = {}
	for key in gr_truth_dict:
		for gt_obj in gr_truth_dict[key]:
				count_dict(gt_obj, dict_calss_labels)
	print dict_calss_labels

	dict_precision_rate = {k:[] for k in dict_calss_labels}
	dict_reacall_rate = {k:[] for k in dict_calss_labels}
	dict_miss_detect_rate = {k:[] for k in dict_calss_labels}
	dict_false_alarm_rate = {k:[] for k in dict_calss_labels}

	for key in gr_truth_dict:
		# print key
		if key in predict_dict:
			dict_precise = {k:0 for k in dict_calss_labels}
			dict_miss_detect = {k:0 for k in dict_calss_labels}
			dict_false_alarm = {k:0 for k in dict_calss_labels}

			dict_save_by_label = {}

			for obj_gt in gr_truth_dict[key]:

				#save key by label
				if obj_gt[0] not in dict_save_by_label:
					dict_save_by_label[obj_gt[0]] = [obj_gt]
				else:
					dict_save_by_label[obj_gt[0]].append(obj_gt)

				#find matched objects
				if obj_gt[0] == 'matched':
					continue		
				for obj_det in predict_dict[key]:
					if obj_det[0] == 'matched':
						continue
					if (obj_det[0] == obj_gt[0] and 
						box_error(obj_det, obj_gt, img_w, img_h) < threshold_error):
						### mark matched object
						count_dict(obj_det, dict_precise)
						obj_det[0] = 'matched'
						obj_det[0] = 'matched'

			### record and write down labels by class
			for key2 in dict_save_by_label:
				dir_by_class = gt_lbl_path + '/../' + 'labels_' + key2
				if not os.path.exists(dir_by_class):
					os.mkdir(dir_by_class)
				f = open(dir_by_class + '/' + key, 'w')
				f.write( str( len( dict_save_by_label[key2] ) )  + '\n')
				for obj_by_class in dict_save_by_label[key2]:
					f.write( (' ').join( map(str, obj_by_class) ) + '\n')
				f.close()

			### record and write down the false_alarm labels

			if os.path.exists(false_alarm_dir):
				shutil.rmtree(false_alarm_dir)
			else:
				os.mkdir(false_alarm_dir)
			n = 0
			for obj_det in predict_dict[key]:
				if obj_det[0] != 'matched':
					n += 1
			if n > 0:
				f2 = open(false_alarm_dir + '/' + key , 'w')
				f2.write( str( n )  + '\n')
				for obj_det in predict_dict[key]:
					if obj_det[0] != 'matched':
						count_dict(obj_det, dict_false_alarm)
						f2.write( (' ').join( map(str, obj_det ) )+ '\n' )
				f2.close()

			### record and write down the miss_detect labels
			if os.path.exists(miss_det_dir):
				shutil.rmtree(miss_det_dir)
			else:
				os.mkdir(miss_det_dir)
			n = 0
			for obj_det in predict_dict[key]:
				if obj_det[0] != 'matched':
					n += 1
			if n > 0:
				f3 = open(miss_det_dir + '/' + key , 'w')
				f3.write( str( len( gr_truth_dict[key] ) ) + '\n')
				for obj_gt in gr_truth_dict[key]: 
					if obj_gt[0] != 'matched':
						count_dict(obj_gt, dict_miss_detect)
						f3.write( (' ').join( map(str, obj_gt ) )+ '\n' )
				f3.close()

			# print "dict_precise    ", dict_precise
			# print "dict_miss_detect", dict_miss_detect
			# print "dict_false_alarm", dict_false_alarm
			# raw_input('...')

			### calculate precision, recall
			for key2 in dict_calss_labels:
				if ( dict_precise[key2] + dict_false_alarm[key2] != 0 ):
					dict_precision_rate[key2].append( 
						float(dict_precise[key2]) / ( dict_precise[key2] + dict_false_alarm[key2] ) )
					dict_false_alarm_rate[key2].append( 
						float(dict_false_alarm[key2]) / ( dict_precise[key2] + dict_false_alarm[key2] ) )
				else :
					dict_precision_rate[key2].append(1)
					dict_false_alarm_rate[key2].append(0)

				if ( dict_precise[key2] + dict_miss_detect[key2] != 0 ):
					dict_reacall_rate[key2].append( 
						float(dict_precise[key2]) / ( dict_precise[key2] + dict_miss_detect[key2] ) )
					dict_miss_detect_rate[key2].append( 
						float(dict_miss_detect[key2]) / ( dict_precise[key2] + dict_miss_detect[key2] ) )
				else:
					dict_reacall_rate[key2].append(1)
					dict_miss_detect_rate[key2].append(0)
				
			# print "dict_precision_rate  ", dict_precision_rate
			# print "dict_false_alarm_rate", dict_false_alarm_rate
			# print "dict_reacall_rate    ", dict_reacall_rate
			# print "dict_miss_detect_rate", dict_miss_detect_rate

	dict_class_rate = {} ##store by class
	## calculate average rate
	cal_average_rate('precision_rate', dict_precision_rate, dict_calss_labels, dict_class_rate)
	cal_average_rate('false_alarm_rate', dict_false_alarm_rate, dict_calss_labels, dict_class_rate)
	cal_average_rate('reacall_rate', dict_reacall_rate, dict_calss_labels, dict_class_rate)
	cal_average_rate('miss_detect_rate', dict_miss_detect_rate, dict_calss_labels, dict_class_rate)

	## write down performance by class
	f = open(performance_data_dir, 'w')
	for key in dict_class_rate:
		f.write( (' ').join(key.split('_') ) + '|' + ('|').join( dict_class_rate[key] ) + '|' + '\n' )
	f.close()


if __name__ == '__main__':
    calculate_map('./', './')