import re

f = open('train_val.prototxt')
s = ''
for each_line in f:
	s += each_line

res, n = re.subn('(?<=source:)(.+)?(?=\n)', '"/home/wills/Projects/caffe-ssd/examples/VOC0712/VOC0712_trainval_lmdb"', s)
# print field
print n


f2 = open('test.prototxt', 'wb')

f2.write(res)

f.close()
f2.close()