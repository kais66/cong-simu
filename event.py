class Event(object):
    def __init__(self, timestamp):
        self._timestamp = timestamp
    
    def execute(self):
        pass

    def printEvt(self):
        pass

    def timestamp(self):
        return self._timestamp
        
class DownStackEvt(Event):
    ''' Pushing a chunk from app buffer onto link layer buffer for sending '''
    def __init__(self, timestamp, node, dst_id):
        super(DownStackEvt, self).__init__(timestamp)
        self.node = node
        self.dst_id = dst_id

    def execute(self):
        # see if the app buffer is currently blocked, 
        if not self.node.src:
            raise AttributeError('node.src is None')
        
        self.printEvt()
        chunk = self.node.src.downOneChunk(self.dst_id)
        if chunk:
            chunk.show()
        else:
            print 'DownStackEvt: no chunk to be pushed down'

    def printEvt(self):
        print 'executing DownStackEvt'

class TxEvt(Event):
    def __init__(self, timestamp, buf_man, simu):
        super(TxEvt, self).__init__(timestamp)
        self.buf_man = buf_man
        self.simulator = simu
        

    def execute(self):
        print 'TxEvt: executing, time: %f, node id: %d, buf_man id: %d' % (self._timestamp, self.buf_man._node._id, self.buf_man._id)
        buf_id = self.buf_man.schedBuffer()
        if buf_id == -1: # nothing to send
            evt = TxEvt(self._timestamp + self.buf_man.schedInterval(), self.buf_man, self.simulator)
            self.simulator.enqueue(evt)
            return

        print 'TxEvt: executing, time: %f' % (self._timestamp)
        # now, 'Transmit' for this buffer
        chunk = self.buf_man.dequeue(buf_id)
        assert chunk is not None
        
        # somebody needs to receive/enqueue it
        next_hop_id = self.buf_man.node().getNextHop(chunk.dst())
        next_hop = self.simulator.getNodeById(next_hop_id)
        next_hop.receive(chunk)

        # schedule next Tx
        evt = TxEvt(self._timestamp + self.buf_man.schedInterval(chunk), self.buf_man, self.simulator)
        self.simulator.enqueue(evt)

