from __future__ import absolute_import
from io import BlockingIOError
import locale
import os
import fcntl

import sys
import struct
import socket
import training_msg_pb2 as proto
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

def nonblocking_readlines(f):
	"""Generator which yields lines from F (a file object, used only for
	   its fileno()) without blocking.  If there is no data, you get an
	   endless stream of empty strings until there is data again (caller
	   is expected to sleep for a while).
	   Newlines are normalized to the Unix standard.
	"""
	fd = f.fileno()
	fl = fcntl.fcntl(fd, fcntl.F_GETFL)
	fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
	enc = locale.getpreferredencoding(False)

	buf = bytearray()
	while True:
		try:
			block = os.read(fd, 8192)
		except (BlockingIOError, OSError):
			yield ""
			continue

		if not block:
			if buf:
				yield buf.decode(enc)
			break

		buf.extend(block)

		while True:
			r = buf.find(b'\r')
			n = buf.find(b'\n')
			if r == -1 and n == -1:
				break

			if r == -1 or r > n:
				yield buf[:(n + 1)].decode(enc)
				buf = buf[(n + 1):]
			elif n == -1 or n > r:
				yield buf[:r].decode(enc) + '\n'
				if n == r + 1:
					buf = buf[(r + 2):]
				else:
					buf = buf[(r + 1):]

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
		print(msg_buf)
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

	def send_message(self, proto_rep):
		# print 'sending....'
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

class thread_train_job(threading.Thread):
	def __init__(self, proto_req, proto_rep, tcp, interval):
		threading.Thread.__init__(self)
		self.tcp = tcp
		self.interval = interval
		self.proto_req = proto_req
		self.proto_rep = proto_rep
		self.job_done = False
		self.stopped = False

		

	def execute_args(self):
		server_log.debug('training thread begins')
		job_dir = './' + self.proto_req.job_id
		if not os.path.exists(job_dir):
			os.mkdir(job_dir)

		# save solver.protxt
		f = open( os.path.join( job_dir, 'solver.prototxt' ), 'w' )
		f.write( self.proto_req.solver )
		f.close()
		# save train_net.protxt
		f = open( os.path.join( job_dir, 'train_val.prototxt' ), 'w' )
		f.write( self.proto_req.train_val_net )
		f.close()
		server_log.debug( 'job argument: {}'.format(self.proto_req.arguments) )
		args = self.proto_req.arguments.split()


		args = ['/home/server/DigitsProj/training/bin/TrainProcess', '../job/solver', '../job/model','pretrained.caffemodel']

		job_dir = '/home/server/DigitsProj/training/bin/'
		#job_dir = '/home/server/DigitsProj/training/bin/20171201-012717-3d11/'
		# execute train job in sub process 
		self.sub_p = subprocess.Popen( 
			args,
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
			cwd=job_dir, 
			close_fds=True, 
			)
		# get log_file
		return self.sub_p.stdout

	def sent_log(self, lines, is_end):

		self.proto_rep.Clear()
		self.proto_rep.log_end = is_end
		line_num = len(lines)
		self.proto_rep.line_num = str( line_num )
		# send log if get lines
		if line_num > 0:
			self.proto_rep.log_line.extend(lines)
			self.tcp.send_message(self.proto_rep)
			print '{} lines sent'.format(self.proto_rep.line_num)

	def run(self):

		log_file = self.execute_args()
		# interval = interval * 1000
		last_line_num = 0
		then = time.time()
		lines = []

		try:
			#send log line produce in each interval
			#while self.sub_p.poll() is None:
				for line in nonblocking_readlines(log_file):
					if self.stopped:
						break
					if line is not None:
						# Remove whitespace
						line = line.strip()
					if line:
						lines.append(line)
						print 'line-----', line
					else:
						time.sleep(0.05)
					now = time.time()
					if (now - then) > self.interval:
						then = now
						self.sent_log(lines, False)
						lines = []

				if not self.stopped:
					self.sent_log(lines, True)
		except Exception as thread_err:
			server_log.debug('Thread Error: {}'.format(thread_err) )
			server_log.debug('Thread was interupted')
			self.stop()
			self.job_done = True
			return

		server_log.debug('training job done!')
		self.sub_p.terminate()
		self.job_done = True

	def stop(self):
		server_log.debug('stop training thread') 
		self.sub_p.terminate()
		self.stopped = True

	def is_job_done(self):
		return self.job_done

def run_training_server():
	req = proto.Request()
	res = proto.Response()

	port = 5055
	#ip = "localhost"
	ip = "192.168.2.173"

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind( (ip , port) )
	sock.settimeout(200)
	sock.listen( 5 )
	
	job_list = {}

	while True:

		try:
			server_log.debug('Server is waiting for connection...')

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
	run_training_server()