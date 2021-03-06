from chunk import Chunk
import config

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

        if config.DEBUG:
            print '\n=== begin DownStackEvt: executing, time: %f' % (self._timestamp)

        # see if the app buffer is currently blocked, 
        if self._node.src is None:
            raise AttributeError('node.src is None')



        chunk = self._node.src.downOneChunk(self._dst_id)
        if config.DEBUG:
            if chunk:
                chunk.show()
            else:
                print 'DownStackEvt: no chunk to be pushed down'

        evt = TxStartEvt(self._simu, chunk.startTimestamp(), self._node.getBufManByDst(chunk.dst()))
        self._simu.enqueue(evt)

        if config.DEBUG:
            print '=== end executing DownStackEvt\n'


class DownStackTBEvt(DownStackEvt):
    '''
        with this event, app buffer uses Token Bucket algorithm to manage its
        sending rate.
    '''
    def execute(self):
        if config.DEBUG:
            print '\n=== begin DownStackTBEvt: executing, time: {}, node: {}, dst_id: {}'.\
                format(self._timestamp, self._node.id(), self._dst_id)

        appBuf = self._node.src.app_buf_man.getBufById(self._dst_id)
        if appBuf.empty():
            if config.DEBUG:
                print '=== end executing DownStackTBEvt: no chunk in queue \n'
            return

        # try schedule the head-of-queue chunk
        if not appBuf.sufficientToken():
            if config.DEBUG:
                print '=== end executing DownStackTBEvt: no sufficient token \n'
            return

        # buf is guaranteed to be not empty
        chunk = appBuf.peek()

        # if chunk arrives after cur time
        if chunk.startTimestamp() > self.timestamp():
            if config.DEBUG:
                print '=== end executing DownStackTBEvt: not yet chk start time: {}\n'. \
                    format(chunk.startTimestamp())
            return

        if config.DEBUG: print 'DownStackTBEvt: do downStack'

        # because there're enough tokens, now first push a chunk down, then
        # schedule another DownStack evt.
        chunk = self._node.src.downOneChunk(self._dst_id)
        if not chunk:
            if config.DEBUG:
                print 'DownStackTBEvt: no chunk to be pushed down, exiting'
            return

        chunk.updateTimestamp(self.timestamp())

        if config.DEBUG:
            chunk.show()

        evt = TxStartEvt(self._simu, self._simu.time(), self._node.getBufManByDst(chunk.dst()))
        self._simu.enqueue(evt)

        if not appBuf.empty():
            next_sched_time = appBuf.estimateTimeOfNextDeq()
            evt = DownStackTBEvt(self._simu, next_sched_time, self._node, self._dst_id)
            self._simu.enqueue(evt)
            if config.DEBUG:
                print 'DownStackTBEvt: next sched downStack time: {}'.format(next_sched_time)

        if config.DEBUG: print '=== end executing DownStackTBEvt\n'


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
            print 'DownStackWithECNEvt: no chunk to be pushed down, exiting'
            return

        # get the linkBufMan for this chunk
        linkBufMan = self._node.getBufManByDst(self._dst_id)

        evt = None
        intendedDelay = appBufMan.getDstDelay(self._dst_id)

        # if buf_man is currently Tx-ing
        if linkBufMan._tx_until > self._timestamp:
            evt = DownStackWithECNEvt(self._simu, linkBufMan._tx_until, self._node, self._dst_id) 
            print 'DownStackWithECNEvt: buf_man currently Tx-ing till {}, \
                nee to reschedule.'.format(linkBufMan._tx_until)
        # elif src has to backoff
        elif chunk.experiencedECNDelay() < intendedDelay: 
            print 'DownStackWithECNEvt: not the time yet, need to reschedule to do downStack'
            # should try DownStack later
            evt = DownStackWithECNEvt(self._simu, self._timestamp +  \
                    (intendedDelay-chunk.experiencedECNDelay()), \
                    self._node, self._dst_id) 
            chunk.setExperiencedECNDelay(intendedDelay)

        # safe to push down
        else:
            print 'DownStackWithECNEvt: do downStack'
            chunk = self._node.src.downOneChunk(self._dst_id)

            evt = TxStartEvt(self._simu, chunk.startTimestamp(), self._node.getBufManByDst(chunk.dst()))

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
        self._logger = self._simu.utilLogger()

    def execute(self):
        buf_id = self._buf_man.schedBuffer()
        if self._timestamp < self._buf_man._tx_until or buf_id == -1: # nothing to send
            if config.DEBUG:
                print '=== TxStartEvt: executing, time: %f, nothing to send for node id: %d, buf_man id: %d ===' % \
                    (self._timestamp, self._buf_man._node._id, self._buf_man._id)

            return

        if config.DEBUG:
            print '\n=== begin TxStartEvt'
        chunk = self._buf_man.getBufById(buf_id).peek()
        chunk.updateTimestamp(self._timestamp)
        chunk.setStatus(Chunk.DURING_TX)

        if chunk.src() == self._buf_man.node().id():
            # trans_ts is the time when the chunk enters the link layer buffer
            chunk.setTransTimestamp(self.timestamp())

        if config.DEBUG:
            print '=== TxStartEvt: start Tx, time: %f, node id: %d, buf_man id: %d' % \
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

        # because we're sure that the chunk has been transmitted, the link has to be occupied
        # during that peirod of time. So log that utilized period.
        # [node_id, buf_man_id, tx_start_time, tx_end_time, length]
        stat_list = [self._buf_man._node.id(), self._buf_man.id(), \
                     self.timestamp(), self._timestamp + tx_time, tx_time]
        self._logger.log(stat_list)

        if config.DEBUG:
            print '=== TxStartEvt: scheduled RxStart at {} and TxEnd at {}'.format(
                    self._timestamp + self._buf_man.latency(), self._timestamp + tx_time)
            print '=== end TxStartEvt\n'


class TxEndEvt(Event): # block_in state change at sender
    ''' dequeue the chunk from upstream, update counter, and then enqueue next TxStartEvt '''
    def __init__(self, simu, timestamp, buf_man, buf_id):
        super(TxEndEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man
        self._buf_id = buf_id

    def execute(self):
        if config.DEBUG:
            print '\n=== begin TxEndEvt'
        chunk = self._buf_man.dequeue(self._buf_id)
        chunk.updateTimestamp(self._timestamp)
        if config.DEBUG:
            print 'TxEndEvt: executing, time: %f, node id: %d, buf_man id: %d' % \
                (self._timestamp, self._buf_man._node._id, self._buf_man._id)

        evt = TxStartEvt(self._simu, self._timestamp, self._buf_man)
        self._simu.enqueue(evt)

        if config.DEBUG:
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
        if config.DEBUG:
            print '\n=== begin RxStartEvt'
        self._chunk.updateTimestamp(self._timestamp)

        if config.DEBUG:
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

        if config.DEBUG:
            print '=== end RxStartEvt\n'


class RxEndEvt(Event):
    def __init__(self, simu, timestamp, chunk, node):
        super(RxEndEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node

    def execute(self):
        if config.DEBUG:
            print '\n=== begin RxEndEvt'
        self._chunk.updateTimestamp(self._timestamp)
        self._chunk.updateCurNode(self._node.id())
        self._chunk.setStatus(Chunk.BEFORE_TX)

        if config.DEBUG:
            print '=== RxEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
            self._chunk.show()
            print '=== end RxEndEvt\n'

class FinDeliveryEvt(Event):
    def __init__(self, simu, timestamp, chunk, node):
        super(FinDeliveryEvt, self).__init__(simu, timestamp)
        self._chunk = chunk
        self._node = node
    def execute(self):
        if config.DEBUG: print '\n=== begin FinDeliveryEvt'
        self._chunk.updateTimestamp(self._timestamp)
        self._chunk.setStatus(Chunk.BEFORE_TX)
        self._node.finish(self._chunk)

        if config.DEBUG:
            print '=== FinDeliveryEvt: executing, time: %f, node id: %d, chunk: ' % (self._timestamp, self._node.id())
            self._chunk.show()
            print '=== end FinDeliveryEvt\n'


class ECNMsgEvt(Event):
    def __init__(self, simu, timestamp, buf_man, chunk):
        super(ECNMsgEvt, self).__init__(simu, timestamp)
        self._buf_man = buf_man
        self._chunk = chunk

    def execute(self):
        if config.DEBUG: print '\n=== begin ECNMsgEvt'
        # actually perform rate adaptation
        self._buf_man._queue_man.doECN(self._chunk)

        # this is for logging
        router_node_id, buf_man_id, src_id = self._buf_man.node().id(), \
                self._buf_man._id, self._chunk.src()
        statList = [router_node_id, buf_man_id, src_id, self.timestamp()]
        ecnLogger = self._simu.ecnLogger()
        ecnLogger.log(statList)
        if config.DEBUG: print '\n=== end ECNMsgEvt'

