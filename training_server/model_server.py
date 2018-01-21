from __future__ import absolute_import
from io import BlockingIOError
import locale
import os
import fcntl

import sys
import struct
import socket
import job_msg_pb2 as proto
import StringIO
# import cv2
import logging
import os
import threading
import subprocess
import time

loglevel = logging.DEBUG
logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S %d/%m/%Y')
server_log = logging.getLogger(__name__)

class ProtoTCP:

    def __init__(self, sock):
        self._isDebug = False
            
        loglevel = logging.DEBUG
        # loglevel = logging.INFO

        logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='SOCKET: %H:%M:%S %d/%m/%Y')
        self.log = logging.getLogger(__name__)

        self.packformat = '>Q'

        self.sock = sock

    def get_proto_message(self, proto_req):

        self.log.debug('entering get_proto_message')

        msg_buf = self.get_message()
        proto_req.ParseFromString(msg_buf)

        self.log.debug('Return from get_proto_message')

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

            self.log.debug('listening...')
            data = self.sock.recv(n)
            if data == '':
                raise RuntimeError('unexpected connection close')
                # self.log.debug('no response')
                # time.sleep(5)
            buf += data
            n -= len(data)

        # self.log.debug('return from socket_read_n')
            
        return buf

    def send_message(self, proto_res):
        # print 'sending....'
        """ Send a serialized message (protobuf Message interface)
            to a socket, prepended by its length packed in 4
            bytes (big endian).
        """
        #s = message.SerializeToString()
        # packed_len = struct.pack(self.packformat, len(message))
        message = proto_res.SerializeToString()
        packed_len = str(len(message) + 100000000)
        self.log.debug("Sending msg of length: {0}".format(packed_len))
        self.sock.sendall(packed_len + message)

    def close(self):
        self.sock.close()
class thread_train_job(threading.Thread):
    def __init__(self, proto_req, proto_res, tcp, interval):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.interval = interval
        self.proto_req = proto_req
        self.proto_res = proto_res
        self.job_done = False
        self.stopped = False

        

    def execute_args(self):

        server_log.debug('training thread begins')
        job_dir = './' + self.proto_req.job_id ### set job dir
        if not os.path.exists(job_dir):
            os.mkdir(job_dir)

        # # save solver.protxt
        # f = open( os.path.join( job_dir, 'solver.prototxt' ), 'w' )
        # f.write( self.proto_req.solver )
        # f.close()
        # # save train_net.protxt
        # f = open( os.path.join( job_dir, 'train_val.prototxt' ), 'w' )
        # f.write( self.proto_req.train_val_net )
        # f.close()
        server_log.debug( 'job argument: {}'.format(self.proto_req.arguments) )
        args = self.proto_req.arguments.split()
        args[2] = '--solver=./solver.prototxt'
        # args = ['/home/server/DigitsProj/training/bin/TrainProcess', '../job/solver', '../job/model','pretrained.caffemodel']
        # execute train job in sub process 
        self.sub_p = subprocess.Popen( args,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            cwd=job_dir, close_fds=True, )
        # return self.sub_p.stdout
        # os.system(args)
        return job_dir + '/log.txt'

    def sent_log(self, lines, is_end):

        self.proto_res.Clear()
        self.proto_res.log_end = is_end
        line_num = len(lines)
        self.proto_res.line_num = str( line_num )
        # send log if get lines
        self.proto_res.log_line.extend(lines)
        self.tcp.send_message(self.proto_res)
        print 'is_end', is_end
        print '{} lines sent'.format(self.proto_res.line_num)

    def run(self):

        # log_file_path = self.execute_args()
        log_file_path = './test/create.log'

        # interval = interval * 1000
        last_line_num = 0
        # sigterm_time = None
        then = time.time()
        lines = []

        try:
            #send log line produce in each interval
            # while self.p.poll() is None:

            n = 0
            while True and (not self.stopped):
                if os.path.exists(log_file_path):
                    f = open(log_file_path, 'r')
                    all_lines = f.readlines()
                    for line in all_lines[n:]:
                        print 'line-----', line
                        if line == '-END-':
                            
                            self.stopped = True
                        if len(line) > 46:
                            lines.append(line)
                            # sigterm_time = time.time()
                            # print 'n-----', n
                            n += 1
                        else:
                            time.sleep(0.05)
                    f.close()
                    
                    time.sleep(1)
                    now = time.time()
                    if (now - then) > self.interval:
                        then = now
                        self.sent_log(lines, False)
                        lines = []
                    # if sigterm_time is not None and (time.time() - sigterm_time > sigterm_timeout):
                    #     self.p.send_signal(signal.SIGKILL)
                    #     self.logger.warning('Sent SIGKILL to task "%s"' % self.name())
                    #     time.sleep(0.1)
                else:
                    server_log.debug('Error, cannot find log file')

            time.sleep(1)
            self.sent_log(lines, True) #sent the rest lines when process is ended
            if self.stopped:
                server_log.debug('training job is aborted!')
                # self.sub_p.terminate()
            else:
                server_log.debug('training job is done!')
                # self.sub_p.terminate()
            self.tcp.close()
            
        
        except Exception as thread_err:

            # if self.p.returncode != 0:
            #     self.logger.error('%s task failed with error code %d' % (self.name(), self.p.returncode))
            #     if self.exception is None:
            #         self.exception = 'error code %d' % self.p.returncode
            #         if unrecognized_output:
            #             if self.traceback is None:
            #                 self.traceback = '\n'.join(unrecognized_output)
            #             else:
            #                 self.traceback = self.traceback + ('\n'.join(unrecognized_output))
            #     self.after_runtime_error()
            #     self.status = Status.ERROR
            #     return False

            server_log.debug('Thread Error: {}'.format(thread_err) )
            server_log.debug('Thread was interupted')
            self.stop()
            self.sent_log(lines, True)
            return

        

    def stop(self):
        server_log.debug('stop training thread') 
        # self.sub_p.terminate()
        self.stopped = True

    def is_job_done(self):
        return self.stopped

class thread_test_job(threading.Thread):
    def __init__(self, proto_req, proto_res, tcp, interval):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.interval = interval
        self.proto_req = proto_req
        self.proto_res = proto_res
        self.job_done = False
        self.stopped = False
        

        
    def create_model_file(self):
        model_dir = './'+self.proto_req.job_id+'/model_iter_'+self.proto_req.job_id
        if os.path.exists(model_dir):
            self.proto_res.model_exists = True
            self.start()
        else:
            self.proto_res.model_exists = False
            self.f = open(model_dir, 'wb')
        self.tcp.send_message(self.proto_res)
        
    def save_model(self, req_test):
        if req_test.model_seg:
            print('----receiving data...')
            self.write(req_test.model_seg)
        else:
            print('----received empty data')


    def execute_args(self):

        server_log.debug('training thread begins')
        job_dir = './' + self.proto_req.job_id ### set job dir
        if not os.path.exists(job_dir):
            os.mkdir(job_dir)

        server_log.debug( 'job argument: {}'.format(self.proto_req.arguments) )
        args = self.proto_req.arguments.split()
        args[2] = '--solver=./solver.prototxt'
        # args = ['/home/server/DigitsProj/training/bin/TrainProcess', '../job/solver', '../job/model','pretrained.caffemodel']
        # execute train job in sub process 
        self.sub_p = subprocess.Popen( args,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            cwd=job_dir, close_fds=True, )
        # return self.sub_p.stdout
        # os.system(args)

    def sent_log(self, lines, is_end):
        pass

    def run(self):
        try:
            self.execute_args()
        except Exception as thread_err:
            server_log.debug('Thread Error: {}'.format(thread_err) )
            server_log.debug('Thread was interupted')
            self.stop()
            self.sent_log(lines, True)
            return

    def stop(self):
        server_log.debug('stop training thread') 
        # self.sub_p.terminate()
        self.stopped = True

    def is_job_done(self):
        return self.stopped

class thread_req_test(threading.Thread):
    def __init__(self, proto_req, proto_req_test, tcp):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.interval = interval
        self.proto_req = proto_req
        self.proto_req_test = proto_req_test
        self.job_done = False
        self.stopped = False

    def send_req_test(self):
        self.proto_req_test.job_id = self.proto_req.job_id
        self.proto_req_test = self.proto_req.TEST
        self.tcp.send_message(self.proto_req_test) # send test arguments

    def run(self):

        
        self.proto_req_test.arguments = 'caffe/predict jobxxxx/model'
        self.send_req_test() #send a test job request

        res_test = proto.Response()
        proto_res_test = self.tcp.get_proto_message(res_test)

        if not proto_res_test.model_exists:

            try:
                filename = '../111.zip'
                f = open(filename, 'rb')
                model_seg = 'initalize' #make it not empty

                while (model_seg) and (not self.stopped):
                    print('sent ', repr(model_seg))
                    model_seg = f.read(1024)
                    self.proto_req_test.model_seg = model_seg
                    self.proto_req_test.arguments = '--transfering'
                    self.send_req_test()

                self.proto_req_test.arguments = '--transfered'
                self.send_req_test()
                f.close()

                
                if self.stopped:
                    server_log.debug('transfering test job is aborted!')
                    # self.sub_p.terminate()
                else:
                    server_log.debug('transfering test job is done!')
                    # self.sub_p.terminate()
                self.tcp.close()
                
            
            except Exception as thread_err:

                server_log.debug('Thread Error: {}'.format(thread_err) )
                server_log.debug('Thread was interupted')
                self.stop()
                self.sent_log(lines, True)

        

    def stop(self):
        server_log.debug('stop transfering test job thread') 
        # self.sub_p.terminate()
        self.stopped = True

    def is_job_done(self):
        return self.stopped


def run_training_server(ip, port):
    req = proto.Request()
    res = proto.Response()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind( (ip , port) )
    sock.settimeout(30)
    sock.listen( 5 )
    
    job_list = {}


    while True:
        try:
            server_log.debug('Server is waiting for connection......')
            # check if job is done or stopped, if is, remove job
            for key in list(job_list):
                server_log.debug( 'job_id: {}'.format(key) )
                if job_list[key].is_job_done():
                    server_log.debug('delete job: {}'.format(job_list[key]) )
                    del job_list[key]

            sock_client, sock_client_address = sock.accept()
            server_log.debug( 'sock_client_address: {}'.format(sock_client_address) )
            tcp_req = ProtoTCP(sock_client)
            request = tcp_req.get_proto_message(req)

            print '-------------request.network_type', request.network_type

            if request.command == proto.Request.TRAIN:
                tcp_res = ProtoTCP(sock_client)
                if request.job_id not in job_list:
                    job_list[request.job_id] = thread_train_job(request, res, tcp_res, 0.5)
                    job_list[request.job_id].start()
                elif job_list[request.job_id].is_job_done():
                    del job_list[request.job_id]
                    job_list[request.job_id] = thread_train_job(request, res, tcp_res, 0.5)
                    job_list[request.job_id].start()
                else:
                    raise RuntimeError('job existed, cannot be created')

            if request.command == proto.Request.ABORT:
                if request.job_id in job_list:
                    job_list[request.job_id].stop()
                    del job_list[request.job_id]
                else:
                    raise RuntimeError('job not existed, cannot be stopped')

            if request.command == proto.Request.DELETE:
                pass

            if request.command == proto.Request.REQTEST:
                # create socket object
                req_test = proto.Request()
                sock_test = socket.socket()

                # get local machine address
                host = socket.gethostname()
                # reserve a port for a service
                port = 2132

                sock_test.connect((host, port))
                tcp_test = ProtoTCP(sock_test)
                if request.job_id not in job_list:
                    job_list[request.job_id] = thread_req_test(request, req_test, tcp_test)
                    job_list[request.job_id].start()
                else:
                    server_log.debug('job {} exists, restart job'.format(request.job_id) ) 
                    job_list[request.job_id].stop()
                    del job_list[request.job_id]
                    job_list[request.job_id] = thread_req_test(request, req_test, tcp_test)
                    job_list[request.job_id].start()

            if request.command == proto.Request.TEST:
                tcp_res = ProtoTCP(sock_client)
                if request.arguments == '--transfering':
                    job_list[request.job_id].save_model()
                    pass
                elif request.arguments == '--transfered':
                    job_list[request.job_id].start()
                    pass
                else:
                    if request.job_id not in job_list:
                        job_list[request.job_id] = thread_test_job(request, res, tcp_res)
                        job_list[request.job_id].create_model_file()
                    else:
                        server_log.debug('job {} exists, restart job'.format(request.job_id) ) 
                        job_list[request.job_id]. stop()
                        del job_list[request.job_id]
                        job_list[request.job_id] = thread_test_job(request, res, tcp_res)
                        job_list[request.job_id].create_model_file()

            # check if job is done or stopped, if is, remove job
            for key in list(job_list):
                if job_list[key].is_job_done():
                    server_log.debug('delete job: {}'.format(job_list[key]) )
                    del job_list[key]
            
        except socket.error as err:
            print 'Secket Error:', err
        except Exception as other_err:
            print 'Other Error:', other_err

if __name__ == '__main__':
    ip = "localhost"
    # ip = "118.201.243.15"
    port = 2133
    run_training_server(ip, port)