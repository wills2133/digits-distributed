import sys
import struct
import socket
import job_msg_pb2 as proto
import StringIO
# import cv2
import logging
import os
import time
import threading

loglevel = logging.DEBUG # DEBUG/INFO
logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S %d/%m/%Y')
server_log = logging.getLogger(__name__)

# if False:
#     ip = "localhost"
#     port = 2133
# else:
#     # ip = "192.168.43.173"
#     ip = "118.201.243.15"
#     port = 955

class ProtoTCP:

    def __init__(self, sock):
        self.packformat = '>Q'

        self.sock = sock
        self.proto_req = proto.Request()
        self.proto_res = proto.Response()

    def get_proto_req(self):
        return self.get_proto_message(self.proto_req)

    def get_proto_res(self):
        return self.get_proto_message(self.proto_res)

    def send_proto_req(self):
        self.send_message(self.proto_req)

    def send_proto_res(self):
        self.send_message(self.proto_res)


    def get_proto_message(self, proto_buf):

        server_log.debug('entering get_proto_message')

        msg_buf = self.get_message()
        proto_buf.ParseFromString(msg_buf)

        server_log.debug('Return from get_proto_message')
   
        return proto_buf

    def get_message(self):

        # server_log.debug('entering get_message')
        len_buf = self.socket_read_n(9)
        # msg_len = struct.unpack(self.packformat, len_buf)[0]
        msg_len = int(len_buf) - 100000000

        server_log.debug('Received msg of length: {0}'.format(msg_len))
        msg_buf = self.socket_read_n(msg_len)
        # server_log.debug('return from get_message')

        return msg_buf

    def socket_read_n(self, n):
        """ Read exactly n bytes from the socket.
            Raise RuntimeError if the connection closed before
            n bytes were read.
        """
        # server_log.debug('entering socket_read_n loop')
        buf = ''        
        while n > 0:

            server_log.debug('listening...')
            data = self.sock.recv(n)
            if data == '':
                raise RuntimeError('unexpected connection close')
                # server_log.debug('no response')
                # time.sleep(5)
            buf += data
            n -= len(data)

        # server_log.debug('return from socket_read_n')
            
        return buf

    def send_message(self, proto_buf):
        # print 'sending....'
        """ Send a serialized message (protobuf Message interface)
            to a socket, prepended by its length packed in 4
            bytes (big endian).
        """
        #s = message.SerializeToString()
        # packed_len = struct.pack(self.packformat, len(message))
        message = proto_buf.SerializeToString()
        packed_len = str(len(message) + 100000000)
        server_log.debug("Sending msg of length: {0}".format(packed_len))
        self.sock.sendall(packed_len + message)


    def close(self):
        self.sock.close()

class thread_read_log(threading.Thread):

    def __init__(self, tcp):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.log_list=[]
        self.stopped = False

    def run(self):
        while not self.stopped:
              
            try:
                response = self.tcp.get_proto_res()
                if response.model_sent:
                    self.stopped = True

            except socket.error as err:
                print err

        print 'thread_read_log ends'

    def stop(self):
        print 'stop thread_read_log'
        self.stopped = True
        tcp.close()

class thread_send_model(threading.Thread):

    def __init__(self, tcp):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.log_list=[]
        self.stopped = False

    def run(self):
        while not self.stopped:
              
            try:
                response = self.tcp.get_proto_res()
                for line in response.log_line:
                    self.log_list.append( line )
                    # write in the file
                if response.log_end:
                    self.stopped = True

            except socket.error as err:
                print err

        print 'thread_read_log ends'

    def stop(self):
        print 'stop thread_read_log'
        self.stopped = True
        tcp.close()

def training_request(addr, job_id, args, job_dir, network_type):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # sock.bind( (ip , 2134) )
    server_log.debug('socket connecting {}:{}'.format(addr[0], addr[1]))
    sock.connect(addr)
    sock.settimeout(300)
    server_log.debug('socket conneced!')

    tcp_pb = ProtoTCP(sock)

    try:
        f = open ( job_dir + '/solver.prototxt' )
        solver_lines = f.readlines()
        solver = ('').join( solver_lines )
        f.close()
    except:
        server_log.debug( 'cannot find solver.txt in digits server' )
        raise

    try:
        f = open ( job_dir + '/train_val.prototxt' )
        train_net_lines = f.readlines()
        train_net = ('').join( train_net_lines )
        f.close()
    except:
        server_log.debug( 'cannot find train_val.txt in digits server' )
        raise

    try:
        f = open(job_dir + '/server_job_info.txt')
        dataset_dir = f.readlines()[2]
        f.close()
    except:
        server_log.debug( 'cannot find server_job_info.txt in digits server' )
        raise

    tcp_pb.proto_req.job_id = job_id
    # tcp_pb.proto_req.command = proto.Request.ABORT
    tcp_pb.proto_req.command = proto.Request.TRAIN
    tcp_pb.proto_req.arguments = args
    tcp_pb.proto_req.solver = solver
    tcp_pb.proto_req.train_val_net = train_net
    tcp_pb.proto_req.image_folder = dataset_dir
    
    if network_type == 'detection':
        tcp_pb.proto_req.network_type = proto.Request.DETECTION
    elif network_type == 'attributes':
        tcp_pb.proto_req.network_type = proto.Request.ATTRIBUTES
    elif network_type == 'face':
        tcp_pb.proto_req.network_type = proto.Request.FACE
    else:
        tcp_pb.proto_req.network_type = proto.Request.CUSTOM
    
    tcp_pb.send_proto_req()

    t_read_log = thread_read_log(tcp_pb)
    t_read_log.daemon = False
    t_read_log.start()
    return t_read_log

def abort_request(addr, job_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # sock.bind( (ip , 2134) )
    sock.connect(addr)
    sock.settimeout(300)

    tcp_pb = ProtoTCP(sock)
    tcp_pb.proto_req.command = proto.Request.ABORT
    tcp_pb.proto_req.job_id = job_id
    
    tcp_pb.send_proto_req()

def test_request(addr, test_addr, job_id, model_iter):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # sock.bind( (ip , 2134) )
    sock.connect(addr)
    sock.settimeout(300)

    tcp_pb = ProtoTCP(sock)
    tcp_pb.proto_req.command = proto.Request.REQTEST
    tcp_pb.proto_req.test_server_ip = test_addr[0]
    tcp_pb.proto_req.test_server_port = test_addr[1]
    tcp_pb.proto_req.job_id = job_id
    tcp_pb.proto_req.model_iter = model_iter

    tcp_pb.send_proto_req()

    response = tcp_pb.get_proto_res()

    if response.test_ready:
        server_log.debug('test server is ready')
        pass
    else:
        server_log.debug('test server is not ready')

if __name__ == '__main__':

    ip = 'localhost'
    port = 2133
    port2 = 2132

    job_id = '20171201-012717-3d11'
    args = '/home/wills/Projects/caffe-ssd/build/tools/caffe train --solver=/home/wills/Projects/digits/digits/jobs/{}/solver.prototxt'.format(job_id)
    job_dir = '/home/wills/Projects/digits/digits/jobs/{}'.format(job_id)
    network_type = '1'

    print 'send request to {}:{}'.format(ip, port)
    test_request((ip , port), (ip , port2), job_id, '80')
    # time.sleep(1)

    # is_test_ready((ip, port2))
    # abort_request((ip , port2), job_id)

    # thread_log = training_request( (ip , port), args , job_dir, job_id, network_type)
    # n = 0
    # while ( not thread_log.stopped ) or ( n < len( thread_log.log_list ) ):
    #     print 'n', n
    #     print 'len', len( thread_log.log_list )
    #     while n < len( thread_log.log_list ):
    #         line = thread_log.log_list[n]
    #         print line
    #         n+=1
    #     time.sleep(1)






