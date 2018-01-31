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
import threading
import subprocess
import time
import gzip
import rarfile
import zipfile
import tarfile
import io

loglevel = logging.INFO # DEBUG/INFO
logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S %d/%m/%Y')
server_log = logging.getLogger(__name__)

def unpack(file_path, extract_dir):
    ext = '.'+file_path.split('.')[-1]
    server_log.debug( 'package file type: '.format(ext) )
    if ext == '.zip':
        """unzip zip file"""
        zip_file = zipfile.ZipFile(file_path)
        if  not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        for names in zip_file.namelist():
            zip_file.extract(names, extract_dir)
        zip_file.close()
        # os.rename(extract_dir, dataset_dir)

    if ext == '.rar':
        """unrar zip file"""
        rar = rarfile.RarFile(file_path)
        if not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        os.chdir(extract_dir)
        rar.extractall()
        rar.close()

    if ext == '.gz':
        """ungz gz file"""
        f_name = file_path.replace(".gz", "")
        g_file = gzip.GzipFile(file_path)
        open(f_name, "w+").write(g_file.read())
        g_file.close()
        """untar tar file"""
        tar = tarfile.open(file_path)
        names = tar.getnames()
        if os.path.isdir(extract_dir):
            pass
        else:
            os.mkdir(extract_dir)
        for name in names:
            tar.extract(name, extract_dir)
        os.remove(f_name)
        tar.close()


    if ext == '.tar':
        """untar tar file"""
        tar = tarfile.open(file_path)
        names = tar.getnames()
        if os.path.isdir(extract_dir):
            pass
        else:
            os.mkdir(extract_dir)
        for name in names:
            tar.extract(name, extract_dir)
        tar.close()

def pack(file_path, extension):
    """
    Return a tarball of all files required to run the model
    """
    package_dir = file_path.split('.')[0] + '.' + extension
    print 'package_dir', package_dir
    name = file_path.split('/')[-1]

    if extension in ['tar', 'tar.gz', 'tgz', 'tar.bz2']:
        # tar file
        mode = ''
        if extension in ['tar.gz', 'tgz']:
            mode = 'gz'
        elif extension in ['tar.bz2']:
            mode = 'bz2'
        with tarfile.open(name=package_dir, mode='w:%s' % mode) as tar:
            tar.add(file_path, arcname=name)
    elif extension in ['zip']:
        with zipfile.ZipFile(b, 'w') as zf:
            zf.write(file_path, arcname=name)
    else:
        pass

    return package_dir

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


class thread_train_job(threading.Thread):

    def __init__(self, proto_req, tcp, interval):
        threading.Thread.__init__(self)
        self.proto_req = proto_req
        self.tcp = tcp
        self.interval = interval
        self.stopped = False
        self.job_done = False

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

        ### run job in subprocess
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

        self.tcp.proto_res.Clear()
        self.tcp.proto_res.log_end = is_end
        line_num = len(lines)
        self.tcp.proto_res.line_num = str( line_num )
        # send log if get lines
        self.tcp.proto_res.log_line.extend(lines)
        self.tcp.send_proto_res()
        server_log.debug( 'is_end-----{}'.format(is_end) )
        server_log.debug( '{} lines sent'.format(self.tcp.proto_res.line_num) )

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
                        # print 'line-----', line
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
            self.job_done = True
            
        
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

            server_log.debug('Training job thread Error: {}'.format(thread_err) )
            server_log.debug('Training job thread was interupted')
            self.sent_log(lines, True)
            self.stop()
            self.tcp.close()
            return

        

    def stop(self):
        server_log.debug('stop training thread') 
        # self.sub_p.terminate()
        self.stopped = True        

    def is_job_done(self):
        return self.job_done

    def close_tcp(self):
        self.tcp.close()

class thread_test_job(threading.Thread):
    def __init__(self, req_in, tcp):
        threading.Thread.__init__(self)
        self.tcp = tcp
        self.req_in = req_in
        self.job_done = False
        self.stopped = False
        self.args = self.req_in.arguments.split()

    def execute_args(self):
        server_log.debug('training thread begins')
        job_dir = './jobs/' + self.req_in.job_id ### set job dir

        server_log.debug( 'test job argument: {}'.format(self.req_in.arguments) )
        # args = self.req_in.arguments.split()
        # args[2] = '--solver=./solver.prototxt'
        # args = ['/home/server/DigitsProj/training/bin/TrainProcess', '../job/solver', '../job/model','pretrained.caffemodel']
        # execute train job in sub process 
        # self.sub_p = subprocess.Popen( self.args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
        #     cwd=job_dir, close_fds=True, )
        # return self.sub_p.stdout
        # os.system(args)

    def sent_log(self, lines, is_end):
        pass

    def run(self):
        try:
            job_dir = './jobs/'+self.req_in.job_id
            extract_dir = job_dir + '/extract'
            model_path = job_dir+'/model_iter_'+self.req_in.model_iter+'.tar.gz'
            if os.path.exists(model_path):
                self.tcp.proto_res.model_exists = True
                self.tcp.send_proto_res()
            else:
                if not os.path.exists(job_dir):
                    os.mkdir(job_dir)
                self.tcp.proto_res.model_exists = False
                self.tcp.send_proto_res()
                f = open(model_path, 'wb')
                model_seg = 'initialized'
                n = 0
                while model_seg:
                    server_log.debug('receiving data_{}'.format(n))
                    n += 1
                    req_model_seg = self.tcp.get_proto_req()
                    model_seg = req_model_seg.model_seg
                    f.write(model_seg)
                server_log.debug('---received data done---')
                f.close()
            unpack(model_path, extract_dir)
            # self.execute_args()
            self.tcp.proto_res.test_ready = True
            self.tcp.send_proto_res()
            # while self.p.poll() is None:
            # self.tcp.send_proto_res()
            self.stop()
            self.job_done = True

        except Exception as thread_err:
            server_log.debug('Test job thread Error: {}'.format(thread_err) )
            server_log.debug('Test job thread was interupted')
            self.stop()
            self.job_done = True
            return

    def stop(self):
        server_log.debug('stop training thread') 
        # self.sub_p.terminate()
        self.stopped = True

    def is_job_done(self):
        return self.job_done

    def close_tcp(self):
        self.tcp.close()

class thread_req_test(threading.Thread):

    def __init__(self, req_in, tcp_in, tcp):
        threading.Thread.__init__(self)
        self.tcp_in = tcp_in
        self.tcp = tcp
        self.req_in = req_in
        self.job_done = False
        self.stopped = False

    def send_req_test(self):
        self.tcp.proto_req.job_id = self.req_in.job_id
        self.tcp.proto_req.command = proto.Request.TEST
        self.tcp.send_proto_req() # send test arguments

    def run(self):
        self.tcp.proto_req.arguments = 'caffe/predict jobxxxx/model'
        self.tcp.proto_req.model_iter = self.req_in.model_iter
        self.send_req_test() #send a test job request

        proto_res_test = self.tcp.get_proto_res()

        if not proto_res_test.model_exists:
        # if True:
            try:
                model_path = '/home/wills/Projects/pos.vec'
                filename = pack(model_path, 'tar.gz')
                # filename = './test/222.tar.gz'
                f = open(filename, 'rb')
                model_seg = 'initialized' #make it not empty
                n = 0
                while (model_seg) and (not self.stopped):
                    # print('sent ', repr(model_seg))
                    server_log.debug( 'send model segment_{}'.format(n) )
                    n += 1
                    model_seg = f.read(1024)
                    self.tcp.proto_req.model_seg = model_seg
                    self.tcp.proto_req.arguments = '--transfering'
                    self.send_req_test()

                self.tcp.proto_req.arguments = '--transfered'
                self.send_req_test()
                f.close()
                
                if self.stopped:
                    server_log.info('transfering test job is aborted!')
                    # self.sub_p.terminate()
                else:
                    server_log.info('transfering test job is done!')
                    # self.sub_p.terminate()
                
            except Exception as thread_err:
                server_log.info('Test request thread Error: {}'.format(thread_err) )
                server_log.info('Test request thread was interupted')
                self.stop()
                self.job_done = True

        response = self.tcp.get_proto_res()
        self.tcp_in.proto_res.test_ready = response.test_ready
        self.tcp_in.send_proto_res()

        self.stop()
        self.job_done = True

    def stop(self):
        server_log.debug('stop transfering test job thread') 
        # self.sub_p.terminate()
        self.stopped = True
        
    def is_job_done(self):
        return self.job_done

    def close_tcp(self):
        self.tcp.close()

def run_job_server(ip, port):

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind( (ip , port) )
    sock.settimeout(300)
    sock.listen( 5 )
    
    job_list = {}


    while True:
        try:
            server_log.info('Server is waiting for connection......')
            # check if job is done or stopped, if is, remove job
            for key in list(job_list):
                server_log.debug( 'job_id: {}'.format(key) )
                if job_list[key].is_job_done():
                    server_log.debug('delete job: {}'.format(job_list[key]) )
                    del job_list[key]

            sock_client, sock_client_address = sock.accept()
            server_log.debug( 'sock_client_address: {}'.format(sock_client_address) )
            tcp_pb = ProtoTCP(sock_client)
            req_in = tcp_pb.get_proto_req()

            server_log.debug( '---req_in.command: {}'.format(req_in.command) )
            server_log.debug( '---req_in.arguments: {}'.format(req_in.arguments) )
            server_log.debug( '---job_list: {}'.format(job_list) )

            if req_in.command == proto.Request.TRAIN:
                if req_in.job_id not in job_list:
                    job_list[req_in.job_id] = thread_train_job(req_in, tcp_pb, 0.5)
                    job_list[req_in.job_id].start()
                elif job_list[req_in.job_id].is_job_done():
                    del job_list[req_in.job_id]
                    job_list[req_in.job_id] = thread_train_job(req_in, tcp_pb, 0.5)
                    job_list[req_in.job_id].start()
                else:
                    raise RuntimeError('job existed, cannot be created')

            if req_in.command == proto.Request.ABORT:
                if req_in.job_id in job_list:
                    job_list[req_in.job_id].stop()
                    del job_list[req_in.job_id]
                else:
                    raise RuntimeError('job not existed, cannot be stopped')

            if req_in.command == proto.Request.DELETE:
                pass

            if req_in.command == proto.Request.REQTEST:
                # create socket object
                ip = req_in.test_server_ip
                port = req_in.test_server_port
                server_log.debug( 'trainging server send to test server({}:{})'.format(ip, port) )
                sock_test = socket.socket()
                sock_test.connect((ip, port))
                tcp_test_req = ProtoTCP(sock_test)

                if req_in.job_id not in job_list:
                    job_list[req_in.job_id] = thread_req_test(req_in, tcp_pb, tcp_test_req)
                    job_list[req_in.job_id].start()
                else:
                    server_log.debug('job {} exists, restart job'.format(req_in.job_id) ) 
                    job_list[req_in.job_id].stop()
                    del job_list[req_in.job_id]
                    job_list[req_in.job_id] = thread_req_test(req_in, tcp_pb, tcp_test_req)
                    job_list[req_in.job_id].start()

            if req_in.command == proto.Request.TEST:
                if req_in.job_id not in job_list:
                    job_list[req_in.job_id] = thread_test_job(req_in, tcp_pb)
                    job_list[req_in.job_id].start()
                else:
                    server_log.debug('job {} exists, restart job'.format(req_in.job_id) ) 
                    job_list[req_in.job_id].stop()
                    del job_list[req_in.job_id]
                    job_list[req_in.job_id] = thread_test_job(req_in, tcp_pb)
                    job_list[req_in.job_id].start()

            # check if job is done or stopped, if is, remove job
            for key in list(job_list):
                if job_list[key].is_job_done():
                    server_log.debug('delete job: {}'.format(job_list[key]) )
                    job_list[key].close_tcp()
                    del job_list[key]
            
        except socket.error as err:
            print 'Secket Error:', err
        except Exception as other_err:
            print 'Other Error:', other_err

if __name__ == '__main__':
    import sys
    ### reserve a port for a service
    ip = "0.0.0.0"
    # ip = "118.201.243.15"
    # ip = socket.gethostname()
    print 'ip', ip
    ### reserve a port for a service
    port = int(sys.argv[1])
    # port = 2133
    server_log.info( 'server is running in {}:{}'.format(ip, port) )
    run_job_server(ip, port)