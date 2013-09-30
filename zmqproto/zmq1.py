import struct

from twisted.internet.protocol import Factory

from zmq3 import Zmq3Protocol, FLAG_MORE

class Zmq1Protocol(Zmq3Protocol):
    header_size = 2
    send_handshake = False
    # http://rfc.zeromq.org/spec:13
    def parseHeader(self, data):
        if not data.startswith(struct.pack('BB', 0x01, 0x00)):
            print "Incorrect server version"
        #print "Server version ok"
        self.proto_state = 2 # no minor header

        # go on if there is any data left
        self.parseFrameData(data, self.header_size)

    def buildGreeting(self):
        # anonymous
        data = struct.pack('BB', 0x01, 0x00)
        return data

    def buildFrame(self, data, more=0):
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

    def parseFrameData(self, data, offset=0):
        # If offset is too big we're finished parsing
        data_len = len(data)
        if data_len <= offset:
            self._data = data[offset:]
            return
        # Flags and size
        if self.next_part == 0:
            self.size = struct.unpack_from('B', data, offset)[0]-1
            offset += 1
            if self.size == 254:
                self.size = struct.unpack_from('>Q', data, offset)[0]-1
                offset += 8
            flags = struct.unpack_from('B', data, offset)[0]
            offset += 1
            self.more = flags & FLAG_MORE         # only for messages
            self.next_part += 1
            self.parseFrameData(data, offset)
        # Data
        else:
            if data_len >= offset + self.size:
                self.frameReceived(data[offset:offset+self.size], False, self.more)
                self.next_part = 0
                self.parseFrameData(data, offset + self.size)
            else:
                # save for later
                self._data = data[offset:]


class Zmq1Factory(Factory):
    def buildProtocol(self, addr):
        return Zmq1Protocol()


