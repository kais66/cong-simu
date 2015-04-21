class Event(object):
    def __init__(self, simu, timestamp):
        self._timestamp = timestamp
        self._simu = simu
    
    def execute(self):
        pass

    def printEvt(self):
        pass

    def timestamp(self):
        return self._timestamp
        
class DownStackEvt(Event):
    ''' Pushing a chunk from app buffer onto link layer buffer for sending '''
    def __init__(self, simu, timestamp, node, dst_id):
        super(DownStackEvt, self).__init__(simu, timestamp)
        self._node = node
        self._dst_id = dst_id

    def execute(self):
        # see if the app buffer is currently blocked, 
        if not self._node.src:
            raise AttributeError('node.src is None')
        
        self.printEvt()
        chunk = self._node.src.downOneChunk(self._dst_id)
        if chunk:
            chunk.show()
        else:
            print 'DownStackEvt: no chunk to be pushed down'

    def printEvt(self):
        print 'executing DownStackEvt'

class TxEvt(Event):
    def __init__(self, simu, timestamp, buf_man):
        super(TxEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man
        

    def execute(self):
        print 'TxEvt: executing, time: %f, node id: %d, buf_man id: %d' % (self._timestamp, self._buf_man._node._id, self._buf_man._id)
        buf_id = self._buf_man.schedBuffer()
        if buf_id == -1: # nothing to send
            evt = TxEvt(self._simu, self._timestamp + self._buf_man.schedInterval(), self._buf_man)
            self._simu.enqueue(evt)
            return

        print 'TxEvt: executing, time: %f' % (self._timestamp)
        # now, 'Transmit' for this buffer
        chunk = self._buf_man.dequeue(buf_id)
        assert chunk is not None
        chunk.updateTimestamp(self._timestamp)
        
        recv_time = self._timestamp + self._buf_man.schedInterval(chunk)
        next_hop_id = self._buf_man.node().getNextHop(chunk.dst())
        next_hop = self._simu.getNodeById(next_hop_id)

        revt = RxEvt(self._simu, recv_time, chunk, next_hop)
        self._simu.enqueue(revt)

        # somebody needs to receive/enqueue it
        #next_hop.receive(chunk)

        # schedule next Tx
        evt = TxEvt(self._simu, self._timestamp + self._buf_man.schedInterval(chunk), self._buf_man)
        self._simu.enqueue(evt)

class RxEvt(Event):
    ''' Receive-Event. '''
    def __init__(self, simu, timestamp, chunk, node):
        super(RxEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node
        #self._buf_man = buf_man

    def execute(self):
        print 'RxEvt: executing, time: %f, node id: %d' % (self._timestamp, self._node.id())
        self._node.receive(self._chunk)
        self._chunk.updateTimestamp(self._timestamp)

