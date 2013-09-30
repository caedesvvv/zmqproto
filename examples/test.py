from twisted.internet import reactor

from zmqproto import ZmqSocket
from zmqproto.zmq3 import Zmq3Protocol
from zmqproto.zmq2 import Zmq2Protocol
from zmqproto.zmq1 import Zmq1Protocol

def test_protocol(proto):
    greeting = proto.buildGreeting()
    handshake = proto.buildReadyHandshake()
    prop1 = proto.buildProperty('Socket-Type', 'DEALER')
    prop2 = proto.buildProperty('Identity', '')

    proto.dataReceived(greeting[:4])
    proto.dataReceived(greeting[4:12])
    proto.dataReceived(greeting[12:16])
    proto.dataReceived(greeting[16:])
    proto.dataReceived(proto.buildFrame(handshake+prop1+prop2))

if __name__ == '__main__':

    for proto in [Zmq1Protocol(), Zmq2Protocol(), Zmq3Protocol()]:
        print "Test protocol", proto
        test_protocol(proto)

    def frame_arrived(self, frame, is_command, wants_more):
        print "frame arrived", is_command, wants_more

    print "Create test client"
    p = ZmqSocket(frame_arrived)
    p.connect('tcp://192.168.1.171:9091')
    reactor.run()

