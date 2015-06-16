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

        evt = TxStartEvt(self._simu, chunk.startTimestamp(), self._node.getBufManByDst(chunk.dst()))
        self._simu.enqueue(evt)

    #def printEvt(self):
        print '=== end executing DownStackEvt\n'

class DownStackWithECNEvt(DownStackEvt):
    ''' with this event, before calling downstack, we check if it is indeed time to push down the chunk. '''
    def execute(self):
        print '\n=== begin DownStackWithECNEvt: executing, time: %f' % (self._timestamp)

        if not self._node.src:
            raise AttributeError('node.src is None')

        self.printEvt()
        
        # query the appBufMan to see if the chunk should be delayed due to previous
        # congestion notification
        appBufMan = self._node.src.app_buf_man
        chunk = appBufMan.peek(self._dst_id)
        if chunk:
            chunk.show()
        else:
            print 'DownStackWithECNEvt: no chunk to be pushed down'
        intendedDelay = appBufMan.getDstDelay(self._dst_id)
        if chunk.startTimestamp() + intendedDelay <= self._timestamp:
            print 'DownStackWithECNEvt: do downStack'
            chunk = self._node.src.downOneChunk(self._dst_id)

            evt = TxStartEvt(self._simu, chunk.startTimestamp(), self._node.getBufManByDst(chunk.dst()))
            self._simu.enqueue(evt)
        else:
            print 'DownStackWithECNEvt: not the time yet, need to reschedule to do downStack'
            # should try DownStack later
            evt = DownStackWithECNEvt(self._simu, chunk.startTimestamp() + intendedDelay, self._node, self._dst_id) 
            self._simu.enqueue(evt)

        print '=== end executing DownStackEvt\n'


###############################################################################
# TxStartEvt: execution of this event attmpts to schedule a chunk for transfer.
# When is this event generated?
# 1. At the src, in DownStackEvt; 
# 2. In TxEndEvt: when a chunk finishes Tx, the next chk is scheduled;
# 3. In RxStartEvt: when a new chunk arrives and it becomes the only chk in q;
# 4. In function CongController.notifyCong():
#       when backpressure is resolved, chks should be scheduled.
###############################################################################
class TxStartEvt(Event): 
    ''' 
        try schedBuf, if able to Tx, set Chunk status to 'during_Tx', enqueue it at receiver (RxStart), and enqueue a 
        TxEnd Evt; else, enqueue an TxStartEvt for next interval 
    '''
    def __init__(self, simu, timestamp, buf_man):
        super(TxStartEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man

    def execute(self):
        buf_id = self._buf_man.schedBuffer()
        if self._timestamp < self._buf_man._tx_until or buf_id == -1: # nothing to send
            print '=== TxStartEvt: executing, time: %f, nothing to send for node id: %d, buf_man id: %d ===' % (self._timestamp, self._buf_man._node._id, self._buf_man._id)
            #evt = TxStartEvt(self._simu, self._timestamp + self._buf_man.schedInterval(), self._buf_man)
            #self._simu.enqueue(evt)
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

        tx_time = self._buf_man.schedInterval(chunk)

        rs_evt = RxStartEvt(self._simu, self._timestamp + self._buf_man.latency(), chunk, next_hop, tx_time)
        self._simu.enqueue(rs_evt)

        self._buf_man._tx_until = self._timestamp + tx_time
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

        print '=== RxStartEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
        self._chunk.show()


        if self._chunk.dst() != self._node.id():
            self._node.receive(self._chunk)
            evt = RxEndEvt(self._simu, self._timestamp + self._tx_time, self._chunk, self._node)
            self._simu.enqueue(evt)

            buf_man = self._node.getBufManByDst(self._chunk.dst())
            # this along with enqueued TxStart at the end of TxEnd, should guarantee every chunk will get scheduled.
            # because: if there's currently no chunk in q, then this received chunk will be Tx immediately;
            # else, the remaining chunk in q will scheduled by the other TxStart evt.
            ts_evt = TxStartEvt(self._simu, self._timestamp + self._tx_time, buf_man)
            self._simu.enqueue(ts_evt)
        else:
            evt = FinDeliveryEvt(self._simu, self._timestamp + self._tx_time, self._chunk, self._node)
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

class FinDeliveryEvt(Event):
    def __init__(self, simu, timestamp, chunk, node):
        super(FinDeliveryEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node
    def execute(self):
        print '\n=== begin FinDeliveryEvt'
        self._chunk.updateTimestamp(self._timestamp)
        self._chunk.setStatus(Chunk.BEFORE_TX)
        self._node.finish(self._chunk)
        print '=== FinDeliveryEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
        self._chunk.show()
        print '=== end FinDeliveryEvt\n'

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

