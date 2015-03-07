import zmq
import pickle
from zmq.eventloop import ioloop, zmqstream
import threading
import ipc
import numpy
import json

class ZmqServer(object):
    def __init__(self):
        self._zmq_key = bytes('hummingbird')
        self._context = zmq.Context()
        self._data_socket = self._context.socket(zmq.PUB)
        self._data_port = 13132
        self._data_socket.bind("tcp://*:%d" % (self._data_port))
        ioloop.install()
        self._ctrl_socket = self._context.socket(zmq.REP)
        self._ctrl_socket.bind("tcp://*:13131")
        self._ctrl_stream = zmqstream.ZMQStream(self._ctrl_socket)
        self._ctrl_stream.on_recv_stream(self.answer_command)
        ipc.uuid = ipc.hostname+':'+str(self._data_port)
        t = threading.Thread(target=self.ioloop)
        # Make sure the program exists even when the thread exists
        t.daemon = True
        t.start()


    def send_array(self, key, A, flags=0, copy=True, track=False):
            """send a numpy array with metadata"""
            md = dict(
                dtype = str(A.dtype),
                shape = A.shape,
            )
            self._data_socket.send_multipart([bytes(key),json.dumps(md)], flags)
            return self._data_socket.send_multipart([bytes(key), A], flags, copy=copy, track=track)

    def send(self, title, data):
        array_list = []
        for i in range(len(data)):
            if(isinstance(data[i],numpy.ndarray)):
                array_list.append(data[i])
                data[i] = '__ndarray__'
        self._data_socket.send_multipart([bytes(title),json.dumps(data)])
        for a in array_list:
            self.send_array(title, a)

    def answer_command(self, stream, msg):
        if(msg[0] == 'keys'):
            stream.socket.send_json(['keys',ipc.broadcast.data_conf])
#            stream.socket.send_multipart(['keys']+ipc.broadcast.data_titles+
#                                         ipc.broadcast.data_types)
        if(msg[0] == 'data_port'):
            stream.socket.send_json(['data_port',bytes(self._data_port)])
        if(msg[0] == 'uuid'):
            stream.socket.send_json(['uuid',bytes(ipc.uuid)])

    def ioloop(self):
        ioloop.IOLoop.instance().start()
        print "ioloop ended"
                
