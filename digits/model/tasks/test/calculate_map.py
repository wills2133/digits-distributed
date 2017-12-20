import os

# pred_label_file_dir = './Labels'
# gr_truth_label_file_dir = './Labels'
# false_alarm_dir = './labels_false_alarm' #dir to save false alarm labels
# miss_dir_dir = './labels_miss_detect' #dir to save miss detection labels
use_same_dir = True #use same dir for pred_label_file_dir and gr_truth_label_file_dir for testing
labels_item = ['people', 'smallExcavator', 'concreteMixerTruck', 'excavator', 'truck']
img_height = 648
img_width = 1152
threshold_error = 10 #pixel, thresold to decide whether a detection is correct
# sum of error between detectd object and ground truth ojbect in height and width

dict_class_rate = {} ##store by class


def count_dict(list_x, dict_x):
	if list_x[0] in dict_x:
		dict_x[list_x[0]] += 1
	else:
		dict_x[list_x[0]] = 1

## calculate the sum error between detectd object and ground truth ojbect in height and width
def box_error(list_predict, list_truth):
	mat_coeff = zip( list_predict[1:], list_truth[1:], 
		[img_width, img_height, img_width, img_height,] )
	error = lambda x: ( abs( x[0] - x[1] ) ) * x[2]
	# print map( error, mat_coeff )
	sum_error = sum( map( error, mat_coeff ) )
	return sum_error

def cal_average_rate(name, dict_rate_list):
	print ''
	for key in labels_item:
		average_rate = sum( dict_rate_list[key] ) / len( dict_rate_list[key] )
		print name.ljust(17), key.ljust(20), average_rate

		if key in dict_class_rate:
			dict_class_rate[key].append( ( name.ljust(17) + str(average_rate) ) )
		else:
			dict_class_rate[key] = [ ( name.ljust(17) + str(average_rate) ) ]


def cal_map(job_dir, gt_label_dir):
	pred_label_file_dir = job_dir + '/Labels'

	if use_same_dir:
		gr_truth_label_file_dir = pred_label_file_dir
	else:
		gr_truth_label_file_dir = gt_label_dir
	
	false_alarm_dir = job_dir + '/labels_false_alarm' #dir to save false alarm labels
	miss_dir_dir = job_dir + '/labels_miss_detect' #dir to save miss detection labels

	performance_data_dir = job_dir + '/performance_data.txt'
	##### save ground label to dict

	### get filepath
	dirpaths = []
	filename_sets = []
	for dirpath,dirnames,filename_set in os.walk(gr_truth_label_file_dir):
		dirpaths.append(dirpath)
		filename_sets.append(filename_set)

	gr_truth_dict = {}
	filenames = sorted(filename_sets[0])
	for file in filenames:
		filepath = os.path.join(dirpaths[0],file)
		f = open(filepath)
		lines = f.readlines()
		num_obj = lines[0]
		label = []
		for n in range(1, int(num_obj)+1):
			items = lines[n].split()
			label.append([items[0]] + map(float, items[1:]))
		gr_truth_dict[file] = label
		f.close()

	#####  save perdict label to dict

	### get filepath
	dirpaths = []
	filename_sets = []
	for dirpath,dirnames,filename_set in os.walk(pred_label_file_dir):
		dirpaths.append(dirpath)
		filename_sets.append(filename_set)

	predict_dict = {}
	filenames = sorted(filename_sets[0])
	index = 1;
	label_pre = []
	for file in filenames:
		filepath = os.path.join(dirpaths[0],file)
		f = open(filepath)
		lines = f.readlines()
		num_obj = lines[0]
		label = []
		for n in range(1, int(num_obj)+1):
			items = lines[n].split()
			label.append([items[0]] + map(float, items[1:]))

		### make confuse prediction
		if use_same_dir:
			index += 1;
			if (index % 3) == 0: 
				predict_dict[file] = label_pre
			else:
				predict_dict[file] = label
			label_pre = label
		### make confuse prediction
		else:
			predict_dict[file] = label
		f.close()


	dict_precision_rate = {k:[] for k in labels_item}
	dict_reacall_rate = {k:[] for k in labels_item}
	dict_miss_detect_rate = {k:[] for k in labels_item}
	dict_false_alarm_rate = {k:[] for k in labels_item}

	for key in predict_dict:
		print key
		if key in gr_truth_dict:

			dict_precise = {k:0 for k in labels_item}
			dict_miss_detect = {k:0 for k in labels_item}
			dict_false_alarm = {k:0 for k in labels_item}

			for obj_det in predict_dict[key]:
				if obj_det[0] == 'matched':
					continue		
				for obj_gt in gr_truth_dict[key]:
					if obj_gt[0] == 'matched':
						continue				
					if (obj_det[0] == obj_gt[0] and box_error(obj_det, obj_gt) < threshold_error):
						### mark matched object
						count_dict(obj_det, dict_precise)
						obj_det[0] = 'matched'
						obj_gt[0] = 'matched'

			### record and write down the false_alarm labels
			if not os.path.exists(false_alarm_dir):
				os.mkdir(false_alarm_dir)
			n = 0
			for obj_det in predict_dict[key]:
				if obj_det[0] != 'matched':
					n += 1 
			if n > 0:
				f2 = open(false_alarm_dir + '/false_alarm_' + key , 'w')
				f2.write( str( n )  + '\n')
				for obj_det in predict_dict[key]:
					if obj_det[0] != 'matched':
						count_dict(obj_det, dict_false_alarm)
						f2.write( (' ').join( map(str, obj_det ) )+ '\n' )
				f2.close()

			### record and write down the miss_detect labels
			if not os.path.exists(miss_dir_dir):
				os.mkdir(miss_dir_dir)
			n = 0
			for obj_det in predict_dict[key]:
				if obj_det[0] != 'matched':
					n += 1
			if n > 0:
				f3 = open(miss_dir_dir + '/miss_detect_' + key , 'w')
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
			for key2 in labels_item:
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




	## calculate average rate
	cal_average_rate('precision_rate', dict_precision_rate)
	cal_average_rate('false_alarm_rate', dict_false_alarm_rate)
	cal_average_rate('reacall_rate', dict_reacall_rate)
	cal_average_rate('miss_detect_rate', dict_miss_detect_rate)

	## write down performance by class
	f = open(performance_data_dir, 'w')
	for key in dict_class_rate:
		f.write( key + '|' + ('|').join( dict_class_rate[key] ) + '|' + '\n' )
	f.close()