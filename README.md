ZmqProto
================================

A pure python zmq library.

Barebones python implementation so clients don't need to depend on the binary libraries. Good for portability.

The library implements protocols 1, 2 and 3. Only protocol 1 is really tested for now but more will follow as we polish the implementation.

At the moment depends uses twisted for networking, but it will be optional in the future.

Examples
-------------------------

    print "Create test client"
    p = ZmqSocket()
    p.connect('tcp://192.168.1.171:9091')

    # send some binary data
    p.send('foo!', 1) # second parameter is the 'send more' flag
    p.send('bar')
   
    print "Create a test protocol"
    proto = Zmq3Protocol()
    greeting = proto.buildGreeting()
    handshake = proto.buildReadyHandshake()

    prop1 = proto.buildProperty('Socket-Type', 'DEALER')
    prop2 = proto.buildProperty('Identity', '')

    proto.dataReceived(greeting[:4])
    proto.dataReceived(greeting[4:12])
    proto.dataReceived(greeting[12:16])
    proto.dataReceived(greeting[16:])
    proto.dataReceived(proto.buildFrame(handshake+prop1+prop2))

    reactor.run()

--

unsystem dev

