from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from twisted.internet.task import LoopingCall

from zmqproto.zre import ZreProtocol
from socket import SOL_SOCKET, SO_BROADCAST

class ZreNode(DatagramProtocol):
    def __init__(self, ipaddr):
        self.proto = ZreProtocol(ipaddr)
        self.peers = {}
        reactor.listenMulticast(5670, self, listenMultiple=True)

    def startProtocol(self):
        # Set the TTL>1 so multicast will cross router hops:
        self.transport.setTTL(5)
        # Join a specific multicast group:
        #self.transport.joinGroup("224.0.0.1")
        self.loopObj = LoopingCall(self.sendHeartBeat)
        self.loopObj.start(10, now=True)

    def sendHeartBeat(self):
        self.transport.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.transport.write(self.proto.buildBeacon(), ('127.255.255.255', 5670))

    def datagramReceived(self, data, (host, port)):
        uuid, _port = self.proto.parseBeacon(data)
        if not uuid == self.proto.uuid:
            if not uuid in self.peers:
                self.peers[uuid] = [_port, host, port]
                print "[%s] beacon id %s port %s [%s:%d]" % (self.proto.uuid, uuid, _port, host, port)


if __name__ == '__main__':
    node1 = ZreNode('127.0.0.1')
    node2 = ZreNode('127.0.0.2')
    node3 = ZreNode('127.0.0.3')
    reactor.run()
