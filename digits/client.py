import sys
import struct
import socket
import training_msg_pb2 as proto
import StringIO
# import cv2
import logging
import os
import time
import threading
class ProtoTCP:

    def __init__(self, sock):
        self._isDebug = False
            
        loglevel = logging.DEBUG
        # loglevel = logging.INFO

        logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='Socket: %H:%M:%S %d/%m/%Y')
        self.log = logging.getLogger(__name__)

        self.packformat = '>Q'

        self.sock = sock

    def get_proto_message(self, proto_req):

        # self.log.debug('entering get_proto_message')

        msg_buf = self.get_message()
        proto_req.ParseFromString(msg_buf)

        # self.log.debug('Return from get_proto_message')

        return proto_req

    def get_message(self):

        # self.log.debug('entering get_message')
        len_buf = self.socket_read_n(9)
        # msg_len = struct.unpack(self.packformat, len_buf)[0]
        msg_len = int(len_buf) - 100000000

        self.log.debug('Received msg of length: {0}'.format(msg_len))
        msg_buf = self.socket_read_n(msg_len)
        # self.log.debug('return from get_message')

        return msg_buf

    def socket_read_n(self, n):
        """ Read exactly n bytes from the socket.
            Raise RuntimeError if the connection closed before
            n bytes were read.
        """
        # self.log.debug('entering socket_read_n loop')
        buf = ''        
        while n > 0:

            print 'listening...'
            data = self.sock.recv(n)
            if data == '':
                raise RuntimeError('unexpected connection close')
                # self.log.debug('no response')
                # time.sleep(5)
            buf += data
            n -= len(data)

        # self.log.debug('return from socket_read_n')
            
        return buf

    def send_message(self, proto_rep):
        print 'sending....'
        """ Send a serialized message (protobuf Message interface)
            to a socket, prepended by its length packed in 4
            bytes (big endian).
        """
        #s = message.SerializeToString()
        # packed_len = struct.pack(self.packformat, len(message))
        message = proto_rep.SerializeToString()
        packed_len = str(len(message) + 100000000)
        self.log.debug("Sending msg of length: {0}".format(packed_len))
        self.sock.sendall(packed_len + message)

class thread_read_log(threading.Thread):

    def __init__(self, tcp, res):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.res = res
        self.log_list=[]
        self.stopped = False

    def run(self):
        while not self.stopped:

            try:
                response = self.tcp.get_proto_message(self.res)
                
                for line in response.log_line:
                    self.log_list.append( line )
                    # print line
                    # write in the file
                if response.log_end:
                    self.stopped = True
                    

            except socket.error as err:
                print err

        print 'thread_read_log ends'

    def stop(self):
        print 'stop thread_read_log'
        self.stopped = True

def training_request(args, job_dir, job_id):
    req = proto.Request()
    res = proto.Response()

    f = open ( job_dir + '/solver.prototxt' )
    solver_lines = f.readlines()
    solver = ('').join( solver_lines )
    f.close()

    f = open ( job_dir + '/train_val.prototxt' )
    train_net_lines = f.readlines()
    train_net = ('').join( train_net_lines )
    f.close()

    req.job_id = job_id
    # req.command = proto.Request.ABORT
    req.command = proto.Request.TRAIN
    req.arguments = args
    req.solver = solver
    req.train_val_net = train_net

    port = 2133
    ip = "localhost"
    # ip = "118.201.243.15"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # sock.bind( (ip , 2134) )
    sock.connect((ip , port))
    sock.settimeout(50)

    tcp = ProtoTCP(sock)
    tcp.send_message(req)

    t_read_log = thread_read_log(tcp, res)
    t_read_log.daemon = False
    t_read_log.start()
    return t_read_log

def abort_request(job_dir, job_id):
    req = proto.Request()
    req.job_id = job_id
    req.command = proto.Request.ABORT
    port = 2133
    ip = "localhost"
    # ip = "118.201.243.15"
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # sock.bind( (ip , 2134) )
    sock.connect((ip , port))
    sock.settimeout(50)

    tcp = ProtoTCP(sock)
    tcp.send_message(req)

if __name__ == '__main__':

    args = '/home/wills/Projects/caffe-ssd/build/tools/caffe train --solver=/home/wills/Projects/digits/digits/jobs/20171201-012550-f273/solver.prototxt'
    job_dir = '/home/wills/Projects/digits/digits/jobs/20171201-012550-f273'
    # job_dir = '.'
    job_id = 'job1'

    thread_log = training_request(args, job_dir, job_id)

    n = 0
    m = 0

    while ( not thread_log.stopped ) or ( n < len( thread_log.log_list ) ):
        # print '------------len:', len( thread_log.log_list )
        if n < len( thread_log.log_list ):
            print thread_log.log_list[n]
            n += 1
        else:
            time.sleep(1)
            m+=1
        if m == 15:
            thread_log.stop()

    print '-----------thread_log.stopped', thread_log.stopped




