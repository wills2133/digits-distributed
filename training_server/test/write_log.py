import os
import time 
import random
# if os.path.exists('./test.log'):
# 	f = open('./test.log', 'r')
# 	lines = f.readlines()
# 	f.close()


# for line in lines:
# 	f2 = open('./create.log', 'a+')
# 	f2.write(line)
# 	time.sleep(1)
# 	f2.close

n=0
while True:
	line = '[I203 solver.cpp:310] Iteration {}, loss = {}\n'.format(n, round(random.random(), 2))
	if n % 10 == 0:
		line = '[I203 solver.cpp:310] model_iter_{} is created\n'.format(n)
	f2 = open('./create.log', 'a+')
	f2.write(line)
	# time.sleep(1)
	f2.close
	n += 1

