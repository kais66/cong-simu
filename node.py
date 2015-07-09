import collections
from event import *
from housekeep_event import LogEvent
from main import Simulator
from cong_ctrl import *
from log import OutputLogger
from chunk import Chunk, File
import math

class Node(object):
    ''' Provides the 'node' abstraction. Because we need to simulate two types of 
    cong ctrl/scheduling policies, the layout of node class is aimed at separating out 
    the policy related logic (i.e. bufferMan and congCtrl, which tends to change) '''
    def __init__(self, node_id, cong_ctrl): # these two argument are base class references
        self._id = node_id
        self.src = None
        self.sink = None

        self.nbrs = []
        self.weights = [] # corresponding to each link where self is one of the vertices
        self.buf_man = {} # next hop node id : buf_man. next_hop_id is in the meantime buf_man.id

        self.next_hop = {} # dst_id : next_hop_id

        self.storage_man = None

    def id(self):
        return self._id

    def nextHopDic(self):
        return self.next_hop

    def attachBufMan(self, buf_man):
        self.buf_man[buf_man.id()] = buf_man
        #self.buf_man.attachNode(self)

    #def attachQueueMan(self, queue_man):
    #    self.queue_man = queue_man

    def attachStorageMan(self, storage_man):
        self.storage_man = storage_man

    def getBufManByDst(self, dst_id):
        #print 'Node:getBufManByDst: node_id: %d, dst_id: %d' % (self._id, dst_id)
        if dst_id not in self.next_hop or self.next_hop[dst_id] not in self.buf_man:
            raise ValueError('Node:getBufMan: buf man not found')
        return self.buf_man[self.next_hop[dst_id]]

    def getBufManByNextHop(self, next_hop_id):
        if next_hop_id not in self.buf_man:
            raise KeyError('Node:getBufMan: node id: {0}, next hop {1} not found'
                            .format(self._id, next_hop_id))
        return self.buf_man[next_hop_id]

    def getBufManById(self, buf_man_id):
        # buf_man_id is essentially next hop id
        return self.getBufManByNextHop(buf_man_id)

    def getNextHop(self, dst_id):
        assert dst_id in self.next_hop
        return self.next_hop[dst_id]

    def attachSrc(self, src):
        self.src = src

    def attachSink(self, sink):
        self.sink = sink

    def schedule(self):
        ''' if the planned sending is granted by next hop, send it; otherwise, congestion control is in effect '''
        pass 

    def send(self):
        pass

    def receive(self, chunk):
        ''' a chunk will be enqueued at one of the buffers, by the link layer buffer manager. The chunk may come 
            from a higher layer buffer (app buffer), or from another node. '''
        print '=== Node:receive: node: %d, chunk: ' % (self._id)
        chunk.show()

        # if cur node is dst, send it to sink, else enqueue at link buffer manager
        if chunk.dst() == self._id:
            raise ValueError("chunk shouldn't be here")
            # sink should handle it
            # self.sink.finish(chunk)
        else:
            # find out the next hop for this chunk (i.e. corresponding buf_man)
            next_hop = self.next_hop[chunk.dst()]

            # then call corresponding buf_man's enqueue
            self.buf_man[next_hop].enqueue(chunk)

    def finish(self, chunk):
        self.sink.finish(chunk)
    
    def addNbr(self, nbr):
        self.nbrs.append(nbr)
    def addWeight(self, weight):
        self.weights.append(weight)

    def getNbrList(self):
        return self.nbrs

class TrafficSrc(object):
    def __init__(self, node, cong_ctrl):
        self._node = node
        self.app_buf_man = None
        #Buffer() # in addition to the bufferMan which manages multiple link layer buffers, src node has app
                                    # buffer which has traffic generated by application
    def attachBufMan(self, buf_man):
        self.app_buf_man = buf_man

    def appBufMan(self):
        return self.app_buf_man

    def pushAppBuffer(self, chunk):
        self.app_buf_man.enqueue(chunk)

    def downOneChunk(self, dst_id):
        chunk = self.app_buf_man.dequeue(dst_id)
        if not chunk:
            print 'TrafficSrc: no available chunk for dst_id: %d' % (dst_id,)
        else:
            self._node.receive(chunk)

        return chunk

    def canDownOneChunk(self, dst_id):
        pass
            

class TrafficSink:
    def __init__(self, node, logger):
        self._node = node
        self._logger = logger

        # file_id (first chk's id) : File
        self._file_dict = {}

    def finish(self, chunk):
        #print '*** TrafficSink:finish, node %d' % (self._node.id())
        #chunk.show()

        # see if a file object is present in dict
        file_id = chunk.fileId()
        if file_id not in self._file_dict:
            self._file_dict[file_id] = File(chunk)

        file = self._file_dict[file_id]
        file.insertChk(chunk)
        if file.isComplete():
            stat_list = [chunk.fileId(), chunk.startTimestamp(),
                    chunk.timestamp(), chunk.timestamp()-chunk.startTimestamp(),
                    chunk.src(), chunk.dst()]
            self._logger.log(stat_list)

    def logToFile(self):
        self._logger.write()
    

class BaseBuffer(object): # buffer could be for a single interface, or for a single flow
    def __init__(self, node, buf_id):
        self.buf_id = buf_id
        self.max_bytes = 1048576*10 # max capacity in bytes, 10MB to begin with

        self.cur_bytes = 0
        self.queue = collections.deque()
        #assert node is not None
        self.cur_node = node

        # buffer scheduling cycle, blocking time
        self.next_sched = 0.0 # in millisecond
        #self.sched_intv = 0.1 # 1MB chunk per 0.1ms, i.e. default is 10GB/s 

    def startBlocking(self): # this should be an observe() function in a observer: once a corresponding congestion
                            # signal is active, the current buffer is blocked.
        pass
       
    def enqueue(self, chunk):
        self.queue.append(chunk)
        self.increCurBytes(chunk.size())
        #self.curNode(cur_node)
        #print 'BaseBuffer:enqueue the chunk'

    def dequeue(self, dq_time=-1.0):
        chunk = self.queue.popleft()
        self.decreCurBytes(chunk.size())
        return chunk

    def empty(self):
        return False if self.queue else True

    def peek(self):
        return self.queue[0]

    def numBytes(self):
        return self.cur_bytes

    def capacity(self):
        return self.max_bytes

    def numChunks(self):
        return len(self.queue)

    def increCurBytes(self, inc):
        self.cur_bytes += inc

    def decreCurBytes(self, dec):
        self.cur_bytes -= dec
        assert self.cur_bytes >= 0
    
    def insertEvent(self):
        pass

    def node(self):
        assert self.cur_node is not None
        return self.cur_node

    def id(self):
        return self.buf_id

class AppBuffer(BaseBuffer):
    def insertEvent(self):
        #evt = DownStackEvt(self._node, self.buf_id)
        #Simulator().enqueue(evt)
        pass

    def enqueue(self, chunk):
        self.queue.append(chunk)
        self.increCurBytes(chunk.size())
        #self.curNode(cur_node)
        #print 'AppBuffer:enqueue the chunk'


class AppBufferTB(BaseBuffer):
    '''
        Implements the token bucket algorithm for rate control of the buffer.
    '''
    INITIAL_RATE = 2000.0
    MAX_RATE = 3000.0
    MIN_RATE = 100.0 # 100 KB/s, or 100B/ms
    # rate increase granularity: increase rate every rate_inc_gran chks
    RATE_INC_GRAN = 1
    # rate increase factor: 0.2 meaning new_rate=prev_rate + INIT_rate*0.2
    RATE_INC_FACTOR = 0.2

    def __init__(self, node, buf_id, simu):
        super(AppBufferTB, self).__init__(node, buf_id)

        self.rate = AppBufferTB.INITIAL_RATE # unit: byte per millisecond


        # timestamp (in ms) of last event of dequeue a chunk from appBuf
        self.last_time = 0.0
        # num of token remaining after last event of dequeue
        self.last_token = 0 # in bytes

        self.simu = simu
        self.config = self.simu._config

        # incremented by 1 for every chk sent; reset to 0 if multiple of rate_inc_gran
        self.sent_count = 0

        # init logger for inst. sending rates
        self.rate_logger = self.simu.rateLogger()
        self.initLoggerEvt()

    def initLoggerEvt(self):
        periodicity = 200 # in milliseconds

        timestamp = 0.0
        evt = LogEvent(self.simu, timestamp, self, periodicity)
        self.simu.enqueue(evt)

    def log(self):
        src_id, dst_id = self.node().id(), self.buf_id

        # this is the format
        stat_list = [src_id, dst_id, self.simu.time(), self.rate]
        self.rate_logger.log(stat_list)

    def dequeue(self, dq_time=-1.0):
        assert self.sufficientToken()
        chunk = super(AppBufferTB, self).dequeue()

        time_passed = self.simu.time() - self.last_time
        #assert self.last_token + time_passed * self.rate >= chunk.size()


        self.sent_count += 1
        self.last_time = self.simu.time()
        self.last_token += (time_passed * self.rate - chunk.size())

        if self.sent_count % AppBufferTB.RATE_INC_GRAN == 0:
            self.sent_count = 0
            self.__additiveIncRate()
        return chunk


    def setRate(self, new_rate):
        old_rate = self.rate
        #assert old_rate >= AppBufferTB.MIN_RATE

        self.rate = new_rate
        print 'AppBuf.setRate: rate changed from {} to {}'.format(old_rate, new_rate)

        # rate reduced
        if new_rate < old_rate:


            time_passed = self.simu.time() - self.last_time
            token_accrued = old_rate * time_passed

            # don't let the accrued token (with old, higher rate) go waste
            self.last_token += token_accrued
            self.last_time = self.simu.time()

            # reduction in rate renders previously enqueued downStackEvt invalid
            # need to re-enqueue one
            # this has to happen after last two lines (after states updated)
            if not self.empty():
                next_sched_time = self.estimateTimeOfNextDeq()
                evt = DownStackTBEvt(self.simu, next_sched_time, self.node(), self.buf_id)
                self.simu.enqueue(evt)

                print 'appBuf.setRate: enq a downStackEvt, next_sched_time: {}, sd: {}, {}'.\
                    format(next_sched_time, self.node().id(), self.buf_id)

    def __additiveIncRate(self):
        new_rate = self.rate + AppBufferTB.INITIAL_RATE * AppBufferTB.RATE_INC_FACTOR
        if new_rate <= AppBufferTB.MAX_RATE:
            print 'appBuf.additiveInc: rate inc from {} to {}'.format(self.rate, new_rate)
            self.setRate(new_rate)

    def sufficientToken(self):
        time_passed = self.simu.time() - self.last_time
        chunk = self.peek()
        if not chunk:
            print 'AppBufferTB.sufficientToken(): no chunk available'
            return False
        total_token = time_passed * self.rate + self.last_token

        if total_token - chunk.size() < -1: # total_token is a float
            print 'appBuf.sufficientToken: last token: {}, total_token: {}, chk size: {}'.\
                    format(self.last_token, total_token, chunk.size())
            print '     time passed: {}, rate: {}'.format(time_passed, self.rate)
            print 'scheduled too early....'
            return False
        else:
            return True

    def estimateTimeOfNextDeq(self):
        '''
            Estimate the time of next dequeue event, when sufficient number of
            have accumulated. This estimate might not be accurate, because
            rate can be changed after DownStack event is enqueued.
            This is called only when a chunk is just pushed down to link buf,
            or when buf_man is initializing this buffer.
            :return: timestamp in ms
        '''

        cur_time = self.simu.time()


        # see if there's an arrival of chunk before the cur_time
        # (buffer is guaranteed to be not empty by caller)
        chunk = self.peek()
        size = chunk.size()

        # calculate how long does take to accumulate enough tokens
        time_till_token = max(math.ceil(float(size - self.last_token) / self.rate), 0.0)

        # if next chunk is scheduled to arrive after the enough-token
        # time, need to schedule later
        estimate = max(chunk.startTimestamp(), cur_time + time_till_token)

        print 'AppBufferTB.estimate: chk size: {}, last_token: {}, rate: {}, estimate: {}'.\
                format(size, self.last_token, self.rate, estimate)
        print '     cur_time: {}, time_till_token: {}, chunk start ts: {}'.\
                format(cur_time, time_till_token, chunk.startTimestamp())
        return estimate




class LinkBuffer(BaseBuffer):
    def __init__(self, node, buf_id, cong_ctrl):
        super(LinkBuffer, self).__init__(node, buf_id)
        self._cong_ctrl = cong_ctrl

    def insertEvent(self):
        pass

    def enqueue(self, chunk):
        super(LinkBuffer, self).enqueue(chunk)
        self._cong_ctrl.updateBlockInState()

    def dequeue(self, dq_time):
        ''' dequeue time should be the receiving time, i.e. Tx timestamp plus time it takes to Tx the whole chunk '''
        chunk = super(LinkBuffer, self).dequeue(dq_time)
        # need to check, if removing this chunk may cause any change in block_in states
        self._cong_ctrl.updateBlockInState(dq_time)
        return chunk

    # cong control related operations
    def congCtrl(self):
        return self._cong_ctrl

    def attachCongObserver(self, obs_buf):
        self._cong_ctrl.attachObserver(obs_buf)
        #obs_buf.attachBuf(self)

class LinkBufferPerFlow(LinkBuffer): 
    def __init__(self, node, buf_id, cong_ctrl):
        super(LinkBufferPerFlow, self).__init__(node, buf_id, cong_ctrl)

class LinkBufferPerIf(LinkBuffer): 
    def __init__(self, node, buf_id, cong_ctrl):
        # assert node is not None
        super(LinkBufferPerIf, self).__init__(node, buf_id, cong_ctrl)

        # because per-if buf_man has single buffer, whose id is the same as buf_man_id
        buf_man_id = self.id()
        self._buf_man = self.cur_node.getBufManById(buf_man_id)

    def enqueue(self, chunk):
        '''
            has ECN capability
        '''
        super(LinkBufferPerIf, self).enqueue(chunk)
        # self._buf_man.doECN(chunk)
