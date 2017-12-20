# import ssd_pascal

# # Add non-data layers
# job_path = "self.path(self.train_val_file)"
# solver_file = "self.path('solver.prototxt')"
# train_net_path = "self.path('train_val.prototxt')"
# test_net_path = "self.path('test.prototxt')"
# snapshot_path = "self.path('VOC_Snapshot')"
# train_data_path = "self.data_dir+'/'+'VOC0712_trainval_lmdb'"
# test_data_path = "self.data_dir+'/'+'VOC0712_test_lmdb'"
# label_map_file = "self.data_dir+'/'+'labelmap_voc.prototxt'"
# name_size_file = "self.data_dir+'/'+'test_name_size.txt'"
# output_result_dir = "self.data_dir+'/'+'Main'"

# iter_size = 2133
# ################ end ##################
# print '----------------------------------------------'
# print 'train_ssd'
# print '----------------------------------------------'
# ############## train_net ##############
# ssd_pascal.CreateTrainNet(train_net_path, train_data_path, 2133) 
# ssd_pascal.CreateTestNet(test_net_path, test_data_path, 2133, 
#     label_map_file, name_size_file, output_result_dir)

import calculate_map

calculate_map.cal_map('/home/wills/Projects/digits/digits/jobs/20171013-014002-37fa', '/home/wills/Projects/digits/digits/jobs/20171013-014002-37fa')