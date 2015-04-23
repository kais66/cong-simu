from chunk import Chunk 

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
        print '\n=== begin DownStackEvt: executing, time: %f' % (self._timestamp)

        # see if the app buffer is currently blocked, 
        if not self._node.src:
            raise AttributeError('node.src is None')
        
        self.printEvt()
        chunk = self._node.src.downOneChunk(self._dst_id)
        if chunk:
            chunk.show()
        else:
            print 'DownStackEvt: no chunk to be pushed down'

    #def printEvt(self):
        print '=== end executing DownStackEvt\n'

class TxEvt(Event):
    def __init__(self, simu, timestamp, buf_man):
        super(TxEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man
        

    def execute(self):
        buf_id = self._buf_man.schedBuffer()
        if buf_id == -1: # nothing to send
            #print 'TxEvt: executing, time: %f, nothing to send for node id: %d, buf_man id: %d' % (self._timestamp, self._buf_man._node._id, self._buf_man._id)
            evt = TxEvt(self._simu, self._timestamp + self._buf_man.schedInterval(), self._buf_man)
            self._simu.enqueue(evt)
            return

        # now, 'Transmit' for this buffer
        chunk = self._buf_man.dequeue(buf_id)
        assert chunk is not None
        chunk.updateTimestamp(self._timestamp)

        print 'TxEvt: executing, time: %f, node id: %d, buf_man id: %d' % (self._timestamp, self._buf_man._node._id, self._buf_man._id)
        chunk.show()
        
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

class TxStartEvt(Event): 
    ''' try schedBuf, if able to Tx, set Chunk status to 'during_Tx', enqueue it at receiver (RxStart), and enqueue a 
        TxEnd Evt; else, enqueue an TxStartEvt for next interval '''
    def __init__(self, simu, timestamp, buf_man):
        super(TxStartEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man

    def execute(self):
        buf_id = self._buf_man.schedBuffer()
        if buf_id == -1: # nothing to send
            #print 'TxStartEvt: executing, time: %f, nothing to send for node id: %d, buf_man id: %d' % (self._timestamp, self._buf_man._node._id, self._buf_man._id)
            evt = TxStartEvt(self._simu, self._timestamp + self._buf_man.schedInterval(), self._buf_man)
            self._simu.enqueue(evt)
            return
        
        print '\n=== begin TxStartEvt'
        chunk = self._buf_man.getBufById(buf_id).peek()
        chunk.updateTimestamp(self._timestamp)
        chunk.setStatus(Chunk.DURING_TX)

        print '=== TxStartEvt: executing, time: %f, node id: %d, buf_man id: %d' % \
                (self._timestamp, self._buf_man._node._id, self._buf_man._id)
        chunk.show()

        next_hop_id = self._buf_man.node().getNextHop(chunk.dst())
        next_hop = self._simu.getNodeById(next_hop_id)

        tx_time = self._timestamp + self._buf_man.schedInterval(chunk)

        rs_evt = RxStartEvt(self._simu, self._timestamp + self._buf_man.latency(), chunk, next_hop, tx_time)
        self._simu.enqueue(rs_evt)

        te_evt = TxEndEvt(self._simu, self._timestamp + tx_time, self._buf_man, buf_id)
        self._simu.enqueue(te_evt)
        print '=== end TxStartEvt\n'


class TxEndEvt(Event): # block_in state change at sender
    ''' dequeue the chunk from upstream, update counter, and then enqueue next TxStartEvt '''
    def __init__(self, simu, timestamp, buf_man, buf_id):
        super(TxEndEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man
        self._buf_id = buf_id

    def execute(self):
        print '\n=== begin TxEndEvt'
        chunk = self._buf_man.dequeue(self._buf_id)
        chunk.updateTimestamp(self._timestamp)
        print 'TxEndEvt: executing, time: %f, node id: %d, buf_man id: %d' % \
                (self._timestamp, self._buf_man._node._id, self._buf_man._id)

        evt = TxStartEvt(self._simu, self._timestamp, self._buf_man)
        self._simu.enqueue(evt)
        print '=== end TxEndEvt: executing, time: %f, node id: %d, buf_man id: %d\n' % \
                (self._timestamp, self._buf_man._node._id, self._buf_man._id)

class RxStartEvt(Event): # block_in state change at receiver
    ''' enqueue at receiver, update counter, generate block signal if needed, enqueue a RxEndEvt. '''
    def __init__(self, simu, timestamp, chunk, node, tx_time):
        super(RxStartEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node
        self._tx_time = tx_time

    def execute(self):
        print '\n=== begin RxStartEvt'
        self._chunk.updateTimestamp(self._timestamp)
        self._node.receive(self._chunk)
        print '=== RxStartEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
        self._chunk.show()

        evt = RxEndEvt(self._simu, self._timestamp + self._tx_time, self._chunk, self._node)
        self._simu.enqueue(evt)
        print '=== end RxStartEvt\n'

class RxEndEvt(Event):
    def __init__(self, simu, timestamp, chunk, node):
        super(RxEndEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node

    def execute(self):
        print '\n=== begin RxEndEvt'
        self._chunk.updateTimestamp(self._timestamp)
        self._chunk.setStatus(Chunk.BEFORE_TX)
        print '=== RxEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
        self._chunk.show()
        print '=== end RxEndEvt\n'

class RxEvt(Event):
    ''' Receive-Event. '''
    def __init__(self, simu, timestamp, chunk, node):
        super(RxEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node
        #self._buf_man = buf_man

    def execute(self):
        self._chunk.updateTimestamp(self._timestamp)
        self._node.receive(self._chunk)
        print '=== RxEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
        self._chunk.show()

