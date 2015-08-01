###############################################################################
# BufferManager classes
# Each buffer manager (except AppBufMan) corresponds to one egress interface.
# It manages buffers for that interface.
###############################################################################
from node import *
from queue_manager import *

class BaseBufferManager(object):
    MB_1 = 1048576
    def __init__(self, simu, id):
        self._node = None
        self._id = id
        self._buffers = {}  # id : buffer, id means differently in different context: next hop, or dst id
        self._simulator = simu
        
        self._cur_byte = 0
        self._MAX_BYTE = BaseBufferManager.MB_1 * 10

    def id(self):
        return self._id

    def addBuffer(self, buf_id):
        self._buffers[buf_id] = BaseBuffer(self._node, buf_id)

    def getBufById(self, buf_id):
        return self._buffers[buf_id]

    def attachNode(self, node):
        #print 'attach node %d for buf_man %d' % (self.id(), node.id())
        self._node = node

    def node(self):
        return self._node 

    def enqueue(self, chunk):
        pass

    def dequeue(self, buf_id):
        pass

    def canDequeue(self, buf_id): 
        ''' given an index to a buffer, determine if we can dequeue a chunk (i.e. not blocked) from it. Returns a boolean '''
        pass

    def curTotalByte(self):
        return self._cur_byte

    def occupancyPercent(self):
        return float(self._cur_byte) / self._MAX_BYTE



###############################################################################
# AppBufferManager class
###############################################################################
class AppBufferManager(BaseBufferManager):
    def addBuffer(self, buf_id):
        self._buffers[buf_id] = AppBuffer(self._node, buf_id)

    def enqueue(self, chunk):
        dst_id = chunk.dst() 
        if dst_id not in self._buffers:
            self.addBuffer(dst_id)

        evt = DownStackEvt(self._simulator, chunk.startTimestamp(), self._node, dst_id)
        self._simulator.enqueue(evt)

        self._buffers[dst_id].enqueue(chunk)

    def dequeue(self, buf_id):
        if buf_id not in self._buffers:
            raise KeyError('AppBufMan: buf_id: %d not found' % (buf_id,))
        buf = self._buffers[buf_id]
        chunk = None
        if not buf.empty():
            chunk = buf.dequeue(-1.0)
            assert chunk is not None
        else:
            print 'AppBufferManager.dequeue(): buffer {} is empty from node: {}, buf_man: {}'.\
                    format(buf_id, self.id(), self.node().id())

        return chunk

class AppBufferManagerTB(AppBufferManager):
    '''
    With Token Bucket controlled buffers.
    '''
    def addBuffer(self, buf_id):
        self._buffers[buf_id] = AppBufferTB(self._node, buf_id, self._simulator)

    def enqueue(self, chunk):
        dst_id = chunk.dst()
        if dst_id not in self._buffers:
            self.addBuffer(dst_id)

            buf = self._buffers[dst_id]
            time_enough_token = 0.0 + float(chunk.size()) / buf.rate

            # this logic is the same as appbuf.estimateTimeOfNextDeq()
            init_time = max(time_enough_token, chunk.startTimestamp())

            evt = DownStackTBEvt(self._simulator, init_time, self._node, dst_id)
            self._simulator.enqueue(evt)

        # with TB, downStack evt is enqueued only for buffer is initialized
        # i.e. not for every enqueued chunk.
        self._buffers[dst_id].enqueue(chunk)


class AppBufferManagerWithECN(AppBufferManager):
    def __init__(self, simu, id):
        super(AppBufferManagerWithECN, self).__init__(simu, id)
        self._dst_to_delay = {}

    def enqueue(self, chunk):
        dst_id = chunk.dst() 
        if dst_id not in self._buffers:
            self.addBuffer(dst_id)

        evt = DownStackWithECNEvt(self._simulator, chunk.startTimestamp(), self._node, dst_id)
        self._simulator.enqueue(evt)

        self._buffers[dst_id].enqueue(chunk)

    def peek(self, dst_id):
        ''' peek at the buffer with dst_id as id '''
        return self._buffers[dst_id].peek()

    def addDelay(self, dst_id, delayToAdd):
        if dst_id not in self._dst_to_delay:
            self._dst_to_delay[dst_id] = delayToAdd
        else:
            self._dst_to_delay[dst_id] += delayToAdd
        print 'AppBufferManagerWithECN.addDelay: curr delay: {}'.format(self._dst_to_delay[dst_id])

    def getDstDelay(self, dst_id):
        if dst_id not in self._dst_to_delay:
            return 0.0
        else:
            return self._dst_to_delay[dst_id] 


class LinkBufferManager(BaseBufferManager):
    def __init__(self, simu, id, band, lat):
        super(LinkBufferManager, self).__init__(simu, id)
        self._band = band # bandwidth, unit: byte per ms
        self._lat = lat # latency: between self._node and the next hop which this buffer is for
        self._intv = 1.0 # length of scheduling interval in ms, later can change this to 1,000,000/band
        self._tx_until = 0.0

        self._logger = self._simulator.queueLenLogger()
        self.initLoggerEvt()

    def initLoggerEvt(self):
        periodicity = 200 # in milliseconds

        timestamp = 0.0
        evt = LogEvent(self._simulator, timestamp, self, periodicity)
        self._simulator.enqueue(evt)

    def log(self):
        node_id, buf_man_id = self.node().id(), self.id()

        # this is the format
        stat_list = [node_id, buf_man_id, self.simu.time(), self.curTotalByte()]
        self.rate_logger.log(stat_list)

    def latency(self):
        return self._lat

    def bandwidth(self):
        return self._band

    def schedInterval(self, chunk):
        #assert chunk is None:
            #return self._intv

        return chunk.size()/self._band
         
    def schedBuffer(self): 
        ''' 
            return a buf_id of which we will send a chunk from.
            This buffer is: 
            1. not being blocked due to backpressure; 
            2. non-empty, i.e. has chunks; 
        '''
        pass

    def schedNextTx(self):
        pass

    def canDequeue(self, buf_id):
        buf = self._buffers[buf_id]
        if not buf.empty():
            chunk = buf.peek()
            if chunk.timestamp() <= self._simulator.time() and chunk.status() == Chunk.BEFORE_TX:
                # see if the chunk will go to a block_in buffer
                next_hop_id = self._node.getNextHop(chunk.dst())

                # for now, assume application is fast, and have infinite buffer
                if next_hop_id == chunk.dst():
                    print 'canDq: next_hop_id == chunk.dst()'
                    return True

                next_hop = self._simulator.getNodeById(next_hop_id)
                next_hop_bufman = next_hop.getBufManByDst(chunk.dst())
                next_hop_buf = next_hop_bufman.getBufById(next_hop_bufman.id())

                if not buf.congCtrl().isBlockedOut(next_hop_buf.congCtrl(), self._simulator.time()):
                    print 'canDq: not blocked'
                    return True
        #    else:
        #        print 'queue element too early to push'           
        #else:
        #    print 'queue empty()'

        #print 'canDq: NO, for node: %d, buf_man: %d, buf: %d' % \
        #        (self._node.id(), self.id(), buf_id)
        return False


    def dequeue(self, buf_id):
        if buf_id not in self._buffers:
            raise KeyError('buf_id: %d' % (buf_id,))

        chunk = None
        #if self.canDequeue(buf_id):

        buf = self._buffers[buf_id] 
        #dq_time = self._simulator.time() + self.schedInterval(buf.peek())
        chunk = buf.dequeue(self._simulator.time())

        # bookkeeping
        self._cur_byte -= chunk.size()

        return chunk

    

class LinkBufferManagerPerFlow(LinkBufferManager):
    def __init__(self, simu, id, band, lat):
        super(LinkBufferManagerPerFlow, self).__init__(simu, id, band, lat)
        self._buf_ids = []
        self._last_buf_ind = 0

    def getBufById(self, buf_id):
        if buf_id not in self._buffers:
            self.addBuffer(buf_id)
        return self._buffers[buf_id]

    def addBuffer(self, buf_id):
        cong_ctrl = CongControllerPerFlow(self._simulator)
        self._buffers[buf_id] = LinkBufferPerFlow(self._node, buf_id, cong_ctrl)
        cong_ctrl.attachBuf(self._buffers[buf_id])
        #print 'added buf: node: %d, buf_man: %d, buf: %d' \
                #% (self._node.id(), self._id, buf_id)

    def enqueue(self, chunk):
        #print 'linkBufManPerFlow: enqueue'
        dst_id = chunk.dst() 
        if dst_id not in self._buffers:
            raise KeyError("buf for dst: %d should've been created on node: %d, buf: %d" \
                % (dst_id, self._node.id(), self._id))
            #self.addBuffer(dst_id)
        
        buf = self._buffers[dst_id]
        self._buffers[dst_id].enqueue(chunk)
        
        # bookkeeping related to capacity
        self._cur_byte += chunk.size()

        # if last hop is not in cong_ctrl's observers, attach it
        #print 'linkBufManPerFlow: enqueue a chunk at node %d buf_man %d buf %d' \
                #% (self._node._id, self._id, dst_id)

    def schedBuffer(self):
        ''' Round Robin scheduling. If there's an available buffer with data in it, schedule it; else if no such buffer exist,
            return -1. '''
        self._buf_ids = self._buffers.keys()
        if not self._buf_ids: return -1
        temp_ind = self._last_buf_ind + 1
        while True: 
            cur_id = self._buf_ids[temp_ind % len(self._buf_ids)]
            #print 'schedBuf: cur_id: %d' % (cur_id)
            if self.canDequeue(cur_id):
                self._last_buf_ind = temp_ind % len(self._buf_ids)
                return cur_id

            #buf = self._buffers[cur_id]
            #if not buf.empty(): 
            #    chunk = buf.peek()
            #    if chunk.startTimestamp() <= self._simulator.time() and \
            #        not buf.congCtrl().isBlockedOut(self._simulator.time()):
            #        self._last_buf_ind = temp_ind % len(self._buf_ids)
            #        return cur_id

            if cur_id == self._buf_ids[self._last_buf_ind]:  # we've checked all buffers
                return -1
            temp_ind += 1

    def canDequeue(self, buf_id):
        buf = self._buffers[buf_id]
        if not buf.empty():
            chunk = buf.peek()
            if chunk.timestamp() <= self._simulator.time() and chunk.status() == Chunk.BEFORE_TX:
                # see if the chunk will go to a block_in buffer
                next_hop_id = self._node.getNextHop(chunk.dst())

                # for now, assume application is fast, and have infinite buffer
                if next_hop_id == chunk.dst():
                    print 'canDq: next_hop_id == chunk.dst()'
                    return True

                next_hop = self._simulator.getNodeById(next_hop_id)
                next_hop_bufman = next_hop.getBufManByDst(chunk.dst())
                next_hop_buf = next_hop_bufman.getBufById(chunk.dst())

                if not buf.congCtrl().isBlockedOut(next_hop_buf.congCtrl(), self._simulator.time()):
                    print 'canDq: not blocked'
                    return True
        #    else:
        #        print 'queue element too early to push'           
        #else:
        #    print 'queue empty()'
        #print 'canDq: NO, for node: %d, buf_man: %d, buf: %d' % \
        #        (self._node.id(), self.id(), buf_id)
        return False



class LinkBufferManagerPerIf(LinkBufferManager):
    ''' per interface queuing '''
    def __init__(self, simu, id, band, lat):
        super(LinkBufferManagerPerIf, self).__init__(simu, id, band, lat)
        #self.addBuffer(self._id)
        self._queue_man = None

        # to get the current number of flows (later can use a bloom filter)
        self._flow_counter = DictFlowCounter()

    def attachQueueMan(self, queue_man):
        self._queue_man = queue_man        
    
    def addBuffer(self, buf_id):
        cong_ctrl = CongControllerPerIf(self._simulator)
        #assert self._node is not None
        self._buffers[buf_id] = LinkBufferPerIf(self._node, buf_id, cong_ctrl)
        cong_ctrl.attachBuf(self._buffers[buf_id])

        self._buffer = self._buffers[self._id]

    def enqueue(self, chunk):
        ''' enqueue based on next hop, instead of dst '''
        print 'LinkBufferManagerPerIf: enqueue'
        self._buffer.enqueue(chunk)

        # bookkeeping related to capacity
        self._cur_byte += chunk.size()

        # bookkeeping ragarding flow counter
        self._flow_counter.flowSeen(Flow(chunk.src(), chunk.dst()))

        node_id = self._node.id()
        #if self._queue_man and chunk.dst() != node_id and chunk.src() != node_id:
        if self._queue_man and chunk.dst() != node_id:
            if self._queue_man.needECN():
                # use the following statement if don't consider propogation delay for ctrl msg
                # self._queue_man.doECN(chunk)

                # considering link delays, need to enqueue a ECN msg event
                latency = self._simulator.calcLatency(node_id, chunk.src())
                evt = ECNMsgEvt(self._simulator, self._simulator.time() + latency,
                                self, chunk)
                self._simulator.enqueue(evt)

    def schedBuffer(self):
        return self._id if self.canDequeue(self._id) else -1

    def canDequeue(self, buf_id):
        buf = self._buffers[buf_id]
        if not buf.empty():
            chunk = buf.peek()
            if chunk.timestamp() <= self._simulator.time() and chunk.status() == Chunk.BEFORE_TX:
                # see if the chunk will go to a block_in buffer
                next_hop_id = self._node.getNextHop(chunk.dst())

                # for now, assume application is fast, and have infinite buffer
                if next_hop_id == chunk.dst():
                    print 'canDq: next_hop_id == chunk.dst()'
                    return True

                next_hop = self._simulator.getNodeById(next_hop_id)
                next_hop_bufman = next_hop.getBufManByDst(chunk.dst())
                next_hop_buf = next_hop_bufman.getBufById(next_hop_bufman.id())

                if not buf.congCtrl().isBlockedOut(next_hop_buf.congCtrl(), self._simulator.time()):
                    print 'canDq: not blocked'
                    return True
        #    else:
        #        print 'queue element too early to push'           
        #else:
        #    print 'queue empty()'
        #print 'canDq: NO, for node: %d, buf_man: %d, buf: %d' % \
        #        (self._node.id(), self.id(), buf_id)
        return False

    # def doECN(self, chunk):
    #     print 'LinkBufferManagerPerIf: doECN'
    #     delay = self._queue_man.decideFlowDelay(chunk)
    #     if delay > 0.0:
    #         self._queue_man.applyFlowDelay(chunk.src(), chunk.dst(), delay)
