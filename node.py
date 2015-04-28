#import Queue
import collections
from event import *
from main import Simulator
from cong_ctrl import *
from log import OutputLogger
from chunk import Chunk

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

    def id(self):
        return self._id

    def nextHopDic(self):
        return self.next_hop

    def attachBufMan(self, buf_man):
        self.buf_man[buf_man.id()] = buf_man
        #self.buf_man.attachNode(self)

    def getBufManByDst(self, dst_id):
        #print 'Node:getBufManByDst: node_id: %d, dst_id: %d' % (self._id, dst_id)
        if dst_id not in self.next_hop or self.next_hop[dst_id] not in self.buf_man:
            raise ValueError('Node:getBufMan: buf man not found')
        return self.buf_man[self.next_hop[dst_id]]

    def getBufManByNextHop(self, next_hop_id):
        if next_hop_id not in self.buf_man:
            raise KeyError('Node:getBufMan: next hop not found')
        return self.buf_man[next_hop_id]

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

    def pushAppBuffer(self, chunk):
        self.app_buf_man.enqueue(chunk)

    def downOneChunk(self, dst_id):
        chunk = self.app_buf_man.dequeue(dst_id)
        if not chunk:
            print 'TrafficSrc: no available chunk for dst_id: %d' % (dst_id,)
        else:
            self._node.receive(chunk)

        return chunk
            

class TrafficSink:
    def __init__(self, node, logger):
        self._node = node
        self._logger = logger

    def finish(self, chunk):
        print '*** TrafficSink:finish, node %d' % (self._node.id())
        chunk.show()
        self._logger.log(chunk)

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

    def dequeue(self, dq_time): 
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
    
    def dequeue(self, dq_time):
        return self.queue.popleft()
        
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
        #assert node is not None
        super(LinkBufferPerIf, self).__init__(node, buf_id, cong_ctrl)

class BaseBufferManager(object):
    def __init__(self, simu, id):
        self._node = None
        self._id = id
        self._buffers = {}  # id : buffer, id means differently in different context: next hop, or dst id
        self._simulator = simu
        

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

    def receive(self, chunk):
        ''' receive some data: increment buffer occupancy counter '''
        pass

    def send(self):
        pass

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
        return chunk

class LinkBufferManager(BaseBufferManager):
    def __init__(self, simu, id, band, lat):
        super(LinkBufferManager, self).__init__(simu, id)
        self._band = band # bandwidth, unit: byte per ms
        self._lat = lat # latency: between self._node and the next hop which this buffer is for
        self._intv = 1.0 # length of scheduling interval in ms, later can change this to 1,000,000/band

    def latency(self):
        return self._lat

    def bandwidth(self):
        return self._band

    def schedInterval(self, chunk=None):
        if chunk is None:
            return self._intv
        else:
            return chunk.size()/self._band 
         
    def schedBuffer(self): 
        ''' return a buf_id of which we will send a chunk from '''
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

        # if last hop is not in cong_ctrl's observers, attach it
        #print 'linkBufManPerFlow: enqueue a chunk at node %d buf_man %d buf %d' \
                % (self._node._id, self._id, dst_id)

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


