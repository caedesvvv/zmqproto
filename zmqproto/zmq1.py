import struct

from twisted.internet.protocol import Factory

from zmq3 import Zmq3Protocol, FLAG_MORE, DEBUG

class Zmq1Protocol(Zmq3Protocol):
    header_size = 2
    send_handshake = False
    # http://rfc.zeromq.org/spec:13
    def parseHeader(self, data):
        # http://rfc.zeromq.org/spec:23#toc28
        if data[0] == chr(0xFF) and len(data) < 12:
            self.header_size = 12
            self._data = data
            self.proto_state = 0
            if DEBUG:
                print "wait for data"
            return
        if DEBUG:
            print "Checking header"
        if data[0] == chr(0xFF):
            if (ord(data[9]) & 0x01) == 0:
                print "version one, long length for identity"
            else:
                print "zmq 2.0 or later", ord(data[10])
            self.header_size = 12
            v = data[10:]
        else:
            v = data
        if not v.startswith(struct.pack('BB', 0x01, 0x00)):
            print "Incorrect server version"
        elif DEBUG:
            print "Server ok"
        #print "Server version ok"
        self.proto_state = 2 # no minor header

        # go on if there is any data left
        self.parseFrameData(data, self.header_size)

    def buildGreeting(self):
        # anonymous
        data = struct.pack('BB', 0x01, 0x00)
        return data

    def buildFrame(self, data, more=0, is_cmd=False):
        data_len = len(data)+1
        if more:
            flags = FLAG_MORE
        else:
            flags = 0

        # headers
        if data_len < 255:
            msg = struct.pack('BB', data_len, flags)
        else:
            msg = struct.pack('BQB', 0xFF, data_len, flags)
        # data
        msg += data
        return msg

    def parseFrameDataChunk(self, data, offset):
        # If offset is too big we're finished parsing
        data_len = len(data)
        if data_len <= offset:
            self._data = data[offset:]
            return
        # Flags and size
        if self.next_part == 0:
            # if not enough data save for later
            if data_len < offset + 3:
                self._data = data[offset:]
                return
            self.size = struct.unpack_from('B', data, offset)[0]-1
            offset += 1
            if self.size == 254:
                if data_len < offset + 9:
                    self._data = data[offset-1:]
                    return
                self.size = struct.unpack_from('>Q', data, offset)[0]-1
                offset += 8
            flags = struct.unpack_from('B', data, offset)[0]
            offset += 1
            self.more = flags & FLAG_MORE         # only for messages
            self.next_part += 1
            return offset
        # Data
        else:
            if data_len >= offset + self.size:
                self.frameReceived(data[offset:offset+self.size], False, self.more)
                self.next_part = 0
                return offset+self.size
            else:
                # save for later
                self._data = data[offset:]


    def parseFrameData(self, data, offset=0):
        offset = self.parseFrameDataChunk(data, offset)
        while not offset == None:
            offset = self.parseFrameDataChunk(data, offset)


class Zmq1Factory(Factory):
    def __init__(self, type):
        self.type = type
    def buildProtocol(self, addr):
        return Zmq1Protocol(self.type)


