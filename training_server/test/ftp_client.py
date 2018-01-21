#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
'''
输入文件名，并且上传
'''
import socket
import time
import struct
import os
f = open('socket_test.txt', 'wb')

for i in range(1000000):
    f.write('for socket test, the line number is : ' + str(i) + '\n')

f.close()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(50)
e = 0
try:
    sock.connect(('localhost', 8887))
    print 'connect...'
except socket.timeout, e:
    print 'timeout', e
except socket.error, e:
    print 'error', e
except e:
    print 'any', e
if not e:
    #while (1):
        #filename = raw_input('input your filename------->')  # 输入文件名
    filename = '/home/wills/anaconda2/pkgs/mkl-2017.0.1-0/lib/libmkl_mc.so'
    FILEINFO_SIZE = struct.calcsize('128sI')  # 编码格式大小
    fhead = struct.pack('128sI', filename, os.stat(filename).st_size)  # 按照规则进行打包
    sock.send(fhead)  # 发送文件基本信息数据
    fp = open(filename, 'rb')
    fp2 = open('local_test.txt','wb')
    i = 0
    while 1:  # 发送文件
        filedata = fp.read(10240)
        if not filedata:
            break
        sock.sendall(filedata)
        fp2.write(filedata)
        print i
        i = i + 1
    print "sending over..."
    fp.close()
    fp2.close()