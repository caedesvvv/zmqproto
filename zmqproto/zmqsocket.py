
DEBUG = False

class ZmqSocket(object):
    def __init__(self, cb=None, version=1, type='DEALER'):
        self.proto = None
        self._cb = cb
        self._queue = []
        if version == 1:
            from zmq1 import Zmq1Factory
            self.factory = Zmq1Factory(type)
        elif version == 2:
            from zmq2 import Zmq2Factory
            self.factory = Zmq2Factory(type)
        elif version == 3:
            from zmq3 import Zmq3Factory
            self.factory = Zmq3Factory(type)

    def on_protocol(self, proto):
        self.proto = proto
        if self._cb:
            proto.register(self._cb)
        for data in self._queue:
            self.proto.send(*data)
        self._queue = []
        return proto

    def on_connection_error(self, reason):
        from twisted.internet import reactor
        print reason.getErrorMessage()
        print "Reconnect in 10 seconds..."
        reactor.callLater(10, self.connect, self.address)
        return reason

    def parse_address(self, address):
        address, port = address.rsplit(':', 1)
        scheme, host = address.rsplit('/', 1)
        if DEBUG:
            print "Connecting to", host, port
        return host, int(port)

    def connect(self, address):
        from twisted.internet import reactor
        from twisted.internet.endpoints import TCP4ClientEndpoint
        self.address = address
        host, port = self.parse_address(address)
        if DEBUG:
            print "Connecting to", host, port
        point = TCP4ClientEndpoint(reactor, host, port)
        d = point.connect(self.factory)
        d.addCallback(self.on_protocol)
        d.addErrback(self.on_connection_error)
        return d

    def recv(self):
        print "Not implemented"
        return self.proto.getNext()

    def send(self, data, more=0, is_cmd=False):
        if self.proto:
            return self.proto.send(data, more, is_cmd)
        else:
            self._queue.append((data, more, is_cmd))

