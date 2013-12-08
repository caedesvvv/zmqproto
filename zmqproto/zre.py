import struct
import random

class ZreProtocol:
    # http://rfc.zeromq.org/spec:20
    def __init__(self, ipaddr):
        self.uuid = random.randint(0,20000)
        self.port = 50000 + random.randint(0,10000)
        self.seq = 0
        self.ipaddr = ipaddr
        self.groups = []
        self.group_status_seq = 0

    def buildString(self, text):
        return struct.pack('B', len(text)) + text

    def buildBeacon(self):
        data = 'ZRE' + chr(0x01)
        data += struct.pack('H', self.uuid)
        data += struct.pack('H', self.port)
        return data

    def parseBeacon(self, data):
        uuid = struct.unpack('H', data[4:6])[0]
        port = struct.unpack('H', data[6:])[0]
        return uuid, port

    def buildHeader(self):
        self.seq += 1
        # signature
        data = chr(0xAA) + chr(0xA1)
        # sequence
        data += struct.pack('H', self.seq)
        return data

    def buildHello(self):
        data = self.buildHeader()
        # ip address
        data += buildString(self.ipaddr)
        # sender mailbox port
        data += struct.pack('H', self.port)
        # groups
        data += struct.pack('B', len(self.groups))
        for group in self.groups:
            data += self.buildString(group)
        # sender group status sequence
        data += struct.pack('B', len(self.group_status_seq))
        # header
        header = {}
        data += struct.pack('B', len(header))
        for key, val in header.iteritems():
            data += self.buildString('%s=%s' % (key, val))
        return data

    def buildWhisper(self, content):
        data = self.buildHeader()
        data += chr(0x02)
        data += self.buildFrame(content)
        return data

    def buildShout(self, group, content):
        data = self.buildHeader()
        data += chr(0x03)
        data += self.buildString(group)
        data += self.buildFrame(content)
        return data

    def buildJoin(self, group):
        self.group_status_seq += 1
        data = self.buildHeader()
        data += chr(0x04)
        data += self.buildString(group)
        # sender group status sequence
        data += struct.pack('B', len(self.group_status_seq))
        return data

    def buildLeave(self, group):
        self.group_status_seq += 1
        data = self.buildHeader()
        data += chr(0x05)
        data += self.buildString(group)
        # sender group status sequence
        data += struct.pack('B', len(self.group_status_seq))
        return data

    def buildPing(self, content):
        data = self.buildHeader()
        data += chr(0x06)
        return data

    def buildPingOk(self, content):
        data = self.buildHeader()
        data += chr(0x07)
        return data

if __name__ == '__main__':
    zre = ZreProtocol('127.0.0.1')
    data = zre.buildBeacon()
    print zre.parseBeacon(data)
