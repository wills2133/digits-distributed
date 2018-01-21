#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import time
'''
等待连接
等待发送文件
读取数据
写入文件并且保存
等待连接
'''
import socket
import threading
import time
import struct


def function(newsock, address):
    FILEINFO_SIZE = struct.calcsize('128sI')
    '''定义文件信息（包含文件名和文件大小）大小。128s代表128个char[]（文件名），I代表一个integer or long（文件大小）'''
    while 1:
        try:
            fhead = newsock.recv(FILEINFO_SIZE)
            filename, filesize = struct.unpack('128sI', fhead)
            '''把接收到的数据库进行解包，按照打包规则128sI'''
            print "address is: ", address
            print filename, len(filename), type(filename)
            print filesize
            #filename = 'new_'+filename.strip('\00')  # 命名新文件new_传送的文件
            filename = filename.strip('\00')
            fp = open(filename, 'wb')  # 新建文件，并且准备写入
            restsize = filesize
            print "recving..."
            while 1:
                if restsize > 102400:  # 如果剩余数据包大于1024，就去1024的数据包
                    filedata = newsock.recv(10240)
                else:
                    filedata = newsock.recv(restsize)
                    fp.write(filedata)
                    #break
                if not filedata:
                    break
                fp.write(filedata)
                restsize = restsize - len(filedata)  # 计算剩余数据包大小
                if restsize <= 0:
                    break
            fp.close()
            print "recv succeeded !!File named:", filename
        except Exception, e:
            print unicode(e).encode('gbk')
            print "the socket partner maybe closed"
            newsock.close()
            break
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # 创建tcp连接
sock.bind(('localhost', 8887))  # 定于端口和ip
sock.listen(5)  # 监听
while True:
    newsock, address = sock.accept()
    print "accept another connection"
    tmpThread = threading.Thread(target=function, args=(newsock, address))  # 如果接收到文件，创建线程
    tmpThread.start()  # 执行线程
print 'end'