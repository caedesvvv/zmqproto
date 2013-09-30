import struct

from twisted.internet.protocol import Protocol, Factory

FLAG_MORE = 1
FLAG_LONG = 2
FLAG_CMD = 4

SIGNATURE = chr(0xFF)+chr(0)*8+chr(0x7F)

DEBUG = False

class Zmq3Protocol(Protocol):
    version = 3
    header_size = 11
    send_handshake = True
    # http://rfc.zeromq.org/spec:23
    def __init__(self):
        if DEBUG:
            print "Connecting"
        self._zmqconnected = 0
        self.next_part = 0
        self.proto_state = 0
        self._data = ''
        self._frames = []
        self._cbs = []
        self._queue = []

    # Events
    def register(self, cb):
        self._cbs.append(cb)

    def frameReceived(self, data, cmd, wants_more):
        self._frames.append(data)
        for cb in self._cbs:
            cb(data, wants_more)

    # Base protocol events
    def connectionMade(self):
        if DEBUG:
            print "Connected"
        self.sendRaw(self.buildGreeting())
        if self.send_handshake:
            self.send(self.buildHandshake())

    # High level protocol
    def buildGreeting(self, mechanism='NULL', is_server=0):
        # signature
        data = SIGNATURE
        # version
        data += struct.pack('BB', 0x03, 0x00)
        # mechanism
        data += mechanism+(20-len(mechanism))*chr(0)
        # as-server
        data += struct.pack('B', int(is_server))
        # filler
        data += chr(0)*31

        return data

    def buildReadyHandshake(self):
        cmd = 'READY'
        data = struct.pack('B', len(cmd)) + cmd
        #data = struct.pack('BB', len(cmd), 0xd5) + cmd
        return data

    def buildHandshake(self):
        data = self.buildReadyHandshake()
        data += self.buildProperty('Socket-Type', 'DEALER')
        data += self.buildProperty('Identity', '')
        return data

    def buildProperty(self, name, value):
        data = struct.pack('B', len(name)) + name
        data += struct.pack('I', len(value)) + value
        return data

    def parseHeader(self, data):
        if not data.startswith(SIGNATURE):
            print "Incorrect signature"
        else:
            print "Signature ok"
        version = struct.unpack('B', data[10])[0]
        if not version == self.version:
            print "Incorrect version", version
        if DEBUG:
            print "Version ok", self.version
        if len(data) >= 64:
            self.parseMinorHeader(data, self.header_size)
        else:
            self.proto_state = 1
            self._data = data[self.header_size:]

    def parseMinorHeader(self, data, offset=0):
        self.proto_state = 2
        minor = struct.unpack_from('B', data, offset)[0]
        mechanism = data[offset+1:offset+21]
        as_server = struct.unpack_from('B', data, offset+21)[0]
        #print " minor header", minor, mechanism, as_server
        if len(data) > offset + 53:
            self.parseFrameData(data, offset+53)

    # Frame functions
    def buildFrame(self, data, more=0):
        data_len = len(data)
        if more:
            flags = FLAG_MORE
        else:
            flags = 0
        if data_len < 255:
            msg = struct.pack('BB', flags, data_len)
        else:
            flags = flags | FLAG_LONG
            msg = struct.pack('BQ', flags, data_len)
        msg += data
        return msg

    def parseFrameDataChunk(self, data, offset=0):
        # If offset is too big we're finished parsing
        data_len = len(data)
        if data_len <= offset:
            self._data = data[offset:]
            return
        # Flags
        if self.next_part == 0:
            flags = struct.unpack_from('B', data, offset)[0]
            self.more = flags & FLAG_MORE         # only for messages
            long_size = flags & FLAG_LONG         # both commands and messages
            self.is_command = flags & FLAG_CMD
            print " flags", self.more, long_size, self.is_command
            if long_size:
                self.next_part = 2
            else:
                self.next_part = 1
            return offset + 1
        # Short size
        elif self.next_part == 1:
            size = struct.unpack_from('B', data, offset)[0]
            self.size = size
            self.next_part = 3
            print " start short size", self.size
            return offset
        # Extended size
        elif self.next_part == 2:
            print " start extended size"
            if data_len < 8 + offset:
                self._data = data[offset:]
            else:
                self.size = struct.unpack_from('Q', data, offset)[0]
                self.next_part += 1
                return offset + 8
        # Data
        elif self.next_part == 3:
            print " check_data", data_len, offset+self.size
            if data_len >= offset + self.size:
                self.frameReceived(data[offset:offset+self.size], self.is_command, self.more)
                self.next_part = 0
                return offset + self.size
            else:
                # save for later
                self._data = data[offset:]

    def parseFrameData(self, data, offset=0):
        offset = self.parseFrameDataChunk(data, offset)
        while not offset == None:
            offset = self.parseFrameDataChunk(data, offset)

    def getNext(self):
        if self._frames:
            return self._frames.pop(0)

    # Main receiving loop
    def dataReceived(self, data):
        if DEBUG:
            print "data received", len(data)
        curr_data = self._data + data
        self._data = ''
        if self.proto_state == 0:
            if len(curr_data) >= self.header_size:
                self.parseHeader(curr_data)
                self._zmqconnected = 1
                while self._queue:
                    self.sendRaw(*self._queue.pop(0))
            else:
                self._data = curr_data
        elif self.proto_state == 1:
            if len(curr_data) >= 53:
                self.parseMinorHeader(curr_data)
            else:
                self._data = curr_data
        else:
            self.parseFrameData(curr_data)

    # Sending
    def send(self, data, more=0):
        frame = self.buildFrame(data, more)
        self.sendRaw(frame, more)

    def sendRaw(self, data, more=0, force=False):
        if self._zmqconnected or force:
            return self.transport.write(data)
        else:
            if DEBUG:
                print "send", data
            self._queue.append((data, more))
class Zmq3Factory(Factory):
    def buildProtocol(self, addr):
        return Zmq3Protocol()


