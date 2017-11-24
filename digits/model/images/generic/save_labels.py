import sys
import struct
import socket
import attribute_pb2 as proto
import StringIO
# import cv2
import logging
import os
class ProtoTCP:

    def __init__(self):
        self._isDebug = False
            
        loglevel = logging.DEBUG
        # loglevel = logging.INFO

        logging.basicConfig(level=loglevel, format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y')
        self.log = logging.getLogger(__name__)

        self.packformat = '>Q'

    def get_proto_message(self, client, proto_data):

        self.log.debug('entering get_proto_message')

        msg_buf = self.get_message(client)
        proto_data.ParseFromString(msg_buf)

        self.log.debug('Return from get_proto_message')

        return proto_data

    def get_message(self, client):

        self.log.debug('entering get_message')
        
        len_buf = self.socket_read_n(client, 9)
        # msg_len = struct.unpack(self.packformat, len_buf)[0]
        msg_len = int(len_buf) - 100000000

        self.log.debug('Received msg of length: {0}'.format(msg_len))
        msg_buf = self.socket_read_n(client, msg_len)

        self.log.debug('return from get_message')

        return msg_buf

    def socket_read_n(self, client, n):
        """ Read exactly n bytes from the socket.
            Raise RuntimeError if the connection closed before
            n bytes were read.
        """
        self.log.debug('entering socket_read_n loop')
        buf = ''        
        while n > 0:            
            data = client.recv(n)
            if data == '':
                raise RuntimeError('unexpected connection close')
            buf += data
            n -= len(data)

        self.log.debug('return from socket_read_n')
            
        return buf

    def send_message(self, sock, message):
        """ Send a serialized message (protobuf Message interface)
            to a socket, prepended by its length packed in 4
            bytes (big endian).
        """
        #s = message.SerializeToString()
        # packed_len = struct.pack(self.packformat, len(message))
        packed_len = str(len(message) + 100000000)
        self.log.debug("Sending msg of length: {0}".format(packed_len))
        sock.sendall(packed_len + message)


def print_response(response):
    print "Status {}".format(proto.Response.Status.Name(response.status))
    detec = response.detec
    print "Number of detections {}".format(len(detec))
    for d in detec:
        print "\tType: {}".format(d.obj_name)
        print "\tScore: {}".format(d.score)
        print "\tRect: ({}, {}), {}, {}, {}".format(d.p1.x, d.p1.y, d.p2, d.p3, d.p4)

def label_response(response, label_path, w, h):
    print "Status {}".format(proto.Response.Status.Name(response.status))
    detec = response.detec
    # print label_path
    f = open(label_path, 'w')

    f.write( str( len( detec ) ) + '\n' )
    for d in detec:
        # print (' ').join( [ d.obj_name, str(d.p1.x), str(d.p1.y), str(d.p3.x), str(d.p3.y) ] )
        # print (' ').join( [ d.obj_name, 
            # str(float(d.p1.x)/w), str(float(d.p1.y)/h), str(float(d.p3.x)/w), str(float(d.p3.y)/h) ] )
        f.write( (' ').join( [ d.obj_name, 
            str(float(d.p1.x)/w), str(float(d.p1.y)/h), str(float(d.p3.x)/w), str(float(d.p3.y)/h) ] ) + '\n')

    f.close()


def get_response_label(img_path, w, h, ip, port):
    req = proto.Request()
    res = proto.Response()

    req.detect = 1
    req.attr = 0
    req.action = 0
    req.cartype = 0
    req.carmake = 0
    req.dtthres = 0.4 #dtThres_
    req.dtnms = 0.2
    req.attrW = 224
    req.attrH = 224
    req.maxObjNum = 30
    req.nmsmethod = 0
    req.nmssigma = 0.5

    req.width = 800
    req.high = 1061

    req.requestid = "xhounddetection-REQID"
    img = open(img_path, "rb").read()
    # img = cv2.imread("adams.jpg")

    # img_s = StringIO.StringIO()
    # img_s.write(img)
    # print type(img_s)
    # sys.exit(1)
    # imgs = cv2.imencode('.jpg', img)[1].tostring()
    # print type(imgs)
    req.image = img

    msg = req.SerializeToString()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(50)

    sock.connect((ip , port))

    tcp = ProtoTCP()
    tcp.send_message(sock, msg)
    # sock.sendall(msg)
    # a = sock.recv(1024)

    # sock.setblocking(False)

    img_dir, img_name_ext = os.path.split(img_path)
    img_name, ext = os.path.splitext(img_name_ext)
    label_dir = img_dir + '/../labels_prediction'

    
    
    if not os.path.exists(label_dir):
        os.mkdir(label_dir)
    label_path = os.path.join( label_dir, img_name) + '.txt'

    try:
        response = tcp.get_proto_message(sock, res)
        label_response(response, label_path, w, h)

    except socket.error as err:
        print err


if __name__ == '__main__':

    from PIL import ImageDraw, Image, ImageFont

    img_path = './testpic/345.jpg'

    img = Image.open(img_path)
    # img_pd = img.copy()
    img_w = img.size[0]
    img_h = img.size[1]

    get_response_label(img_path, img_w, img_h)

    labels = os.listdir('./labels_prediction')

    print './labels_prediction/' + labels[0]
    f = open('./labels_prediction/' + labels[0])

    lines = f.readlines()
    num_obj = lines[0]

    f.close()
    font_size = 30
    rect_thick = 15
    font = ImageFont.truetype('ubuntu_font_family/Ubuntu-B.ttf', font_size)
    for n in range(1, int(num_obj)+1):

        items = lines[n].split()

        x_Ltop = int( float(items[1]) * img_w )
        y_Ltop = int( float(items[2]) * img_h )
        x_Rbtm = int( float(items[3]) * img_w )
        y_Rbtm = int( float(items[4]) * img_h )
        # print items[0]
        # print (x_Ltop, y_Ltop , x_Rbtm, y_Rbtm)
        # write down label on image
        write = ImageDraw.Draw(img)
        write.text( ( (x_Ltop - font_size*0.5) if (img_w - x_Ltop) > font_size*2 else (x_Ltop - font_size*2), 
            (y_Ltop - font_size * 1.5) if (y_Ltop - font_size * 1.5) > 0 else (y_Rbtm + font_size*0.5) ), 
            items[0], font = font, fill = 'green')
        # thicken the line
        
        mask = Image.new('1', img.size)
        draw = ImageDraw.Draw(mask)
        for pix in (rect_thick, -rect_thick+1):
            x_Ltop -= pix /2
            y_Ltop -= pix /2
            x_Rbtm += pix /2
            y_Rbtm += pix /2

            draw.rectangle( ( (x_Ltop, y_Ltop , x_Rbtm, y_Rbtm) ), fill = (pix+rect_thick-1 and 255) )
        img.paste('green', mask = mask)
    img.show()
