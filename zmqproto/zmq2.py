import struct

from twisted.internet.protocol import Factory

from zmq3 import Zmq3Protocol, SIGNATURE

DEBUG = False
types = { 'DEALER': 0x05,
          'SUB': 0x02 }

class Zmq2Protocol(Zmq3Protocol):
    # http://rfc.zeromq.org/spec:15
    send_handshake = False
    def buildGreeting(self):
        # signature
        data = SIGNATURE
        # version
        data += struct.pack('B', 0x01)
        # socket type
        data += struct.pack('B', types[self.type])
        # Identity, final short
        data += struct.pack('B', 0x01)
        identity = ''
        data += struct.pack('B', len(identity)) + identity
        if self.type == 'SUB':
            data += self.buildHandshake()
        return data

    def buildHandshake(self):
        subscribe = chr(0x01) + ''
        data = struct.pack('B', len(subscribe)) + subscribe
        return data

    def connectionMadeX(self):
        print "Connected to zmq server v2"


class Zmq2Factory(Factory):
    def __init__(self, type):
        self.type = type
    def buildProtocol(self, addr):
        return Zmq2Protocol(self.type)


