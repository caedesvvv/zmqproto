from twisted.internet import reactor

from zmqproto import ZmqSocket

if __name__ == '__main__':
    def frame_arrived(frame, is_command):
        print "frame arrived", frame, is_command

    print "Create test client"
    p1 = ZmqSocket(frame_arrived, version=1, type='SUB')
    p1.connect('tcp://85.25.198.97:9094') # block publish
    #p1.connect('tcp://127.0.0.1:5556') # block publish
    #p2 = ZmqSocket(frame_arrived, version=2, type='SUB')
    #p2.connect('tcp://85.25.198.97:9094') # block publish
    #p2.connect('tcp://127.0.0.1:5556') # block publish
    reactor.run()

