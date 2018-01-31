import os
import time

n = 0
if os.path.exists('./create.log'):
	while True:

		f = open('./create.log', 'r')
		lines = f.readlines()
		for line in lines[n:]:
			if len(line) > 46:
				print line
				print n
				n += 1
			time.sleep(0.5)