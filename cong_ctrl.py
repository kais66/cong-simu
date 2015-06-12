from node import *

class BaseCongController(object):
    ''' Implementing the subject class: which owns a group of observers. When notify() is called 
        for that observer, its status should be set to 'blocked'. '''
    def __init__(self, simu):
        self._obs = [] # list of observers
        self._buf = None
        self._simu = simu

        # whether traffic into this buffer is currently blocked
        self._block_in = False

    def attachBuf(self, buf):
        self._buf = buf

    def attachObserver(self, obs):
        if obs is not self and self._buf.id() != obs._buf.node().id():
            self._obs.append(obs)

    def bufMan(self):
        return self._buf.node().getBufManByDst(self._buf.id())        

    def detachObserver(self, obs):
        pass

    def updateBlockInState(self, future_time=None): pass 

    def notifyCong(self, sub, future_time): pass

    def notifyNoCong(self, sub): 
        pass

    def isBlockedOut(self, sub, cur_time):
        pass

# as of now, Apr 13th, it's implemented as per-dst queuing, but this can be extended.
class CongControllerPerFlow(BaseCongController):
    ''' Each observer is an upstream buffer. CongCtrl algo is to limit num outstanding chunks to be H, 
        this is done on a buffer to buffer basis (downstream buffer, i.e. subject, notify 
        upstream buffer, i.e. observer). '''
    def __init__(self, simu):
        super(CongControllerPerFlow, self).__init__(simu)
        #self._ostd_chk_limit = 1
        self._ostd_chk_limit = 100

        # till when is outgoing traffic blocked: -1 means not blocked, 0 means blocked indefinitely, otherwise
        # blocked until the nominal time.
        self._block_out_till = -1.0 

    def updateBlockInState(self, future_time=None):
        ''' return if block In state is changed '''
        if not self._block_in and self._buf.numChunks() >= self._ostd_chk_limit:
            self._block_in = True
            print 'BlockInState: --> blocked'
            self.notifyCong(self, 0)
            return True

        if self._block_in and self._buf.numChunks() < self._ostd_chk_limit:
            assert future_time is not None
            self._block_in = False
            print 'BlockInState: --> unblocked'
            self.notifyCong(self, future_time)
            return True
        return False

    def notifyCong(self, sub, future_time): 
        ''' isCong: bool. Identifying whether this is to activate or deactivate back pressure '''
        for ob in self._obs:
            ob._block_out_till = future_time

            evt = None
            if future_time > 0: # remote interface won't be blocked starting this future_time
                evt = TxStartEvt(ob._simu, future_time, ob.bufMan()) 
            elif future_time < 0: # not blocked as of right now
                evt = TxStartEvt(ob._simu, ob._simu.time(), ob.bufMan()) 
            if evt:
                self._simu.enqueue(evt)

    def notifyNoCong(self, sub):
        for ob in self._obs:
            ob._block_out_till = -1.0

            evt = TxStartEvt(ob._simu, ob._simu.time(), ob.bufMan()) 
            self._simu.enqueue(evt)

    def isBlockedOut(self, sub, cur_time):
        ''' cur_time is a float ''' 

        ret = None
        if self._block_out_till < 0:
            ret = False
        elif self._block_out_till == 0:
            ret = True
        else:
            ret = (cur_time < self._block_out_till)

        if ret:
            print '!!! CongController: blocked. '
        return ret


# A problem with per-if queuing is: if multiple upstream outgoing buffer
class CongControllerPerIf(BaseCongController):
    ''' 
        Per interface queuing. 1. Subject is an interface, i.e. perIfBuf (note not buf_man). A buf has limit on buffering, if this
        limit is reached, it's not accepting additional data. For each upstream node, essentially blocking all 
        flows that will travel through the congested interface. 2. The congested interface can also notify the 
        source of the traffic, i.e. app_buf_man of a source node. 
        Note: another way of per-interface queuing is: a shared buffer space for all outgoing interfaces. This implementation is 
        for the first way. 
    ''' 

    def __init__(self, simu):
        super(CongControllerPerIf, self).__init__(simu)
        self._block_out_till = {} # cong_ctrl_subject : future_time

    def updateBlockInState(self, future_time=None):
        if not self._block_in and self._buf.numBytes() >= self._buf.capacity():
            self._block_in = True
            print 'BlockInState: --> blocked, node: %d, buf: %d' % \
                (self._buf.node().id(), self._buf.id())
            self.notifyCong(self, 0)
            return True

        if self._block_in and self._buf.numBytes() < self._buf.capacity():
            assert future_time is not None
            self._block_in = False
            print 'BlockInState: --> unblocked'
            self.notifyCong(self, future_time)
            return True
        return False

    def notifyNoCong(self, sub):
        for ob in self._obs:
            ob._block_out_till[sub] = -1.0

            evt = TxStartEvt(ob._simu, ob._simu.time(), ob.bufMan()) 
            self._simu.enqueue(evt)

    def notifyCong(self, sub, future_time):
        for ob in self._obs:
            #if sub._buf.id() == ob._buf.node().id(): # e.g. node 1's buf 3 blocked in, don't notify node 3's buf 1
            #    continue
            ob._block_out_till[sub] = future_time
            print 'notifyCong: future_time: %f, block_out: node: %d, buf: %d, block_in: node: %d, buf: %d' % \
                (future_time, ob._buf.node().id(), ob._buf.id(), sub._buf.node().id(), sub._buf.id())
            #print ob
            #print sub
            evt = None
            if future_time > 0: # remote interface won't be blocked starting this future_time
                evt = TxStartEvt(ob._simu, future_time, ob.bufMan()) 
            elif future_time < 0: # not blocked as of right now
                evt = TxStartEvt(ob._simu, ob._simu.time(), ob.bufMan()) 
            if evt:
                self._simu.enqueue(evt)
            

    def isBlockedOut(self, sub, cur_time):
        ret = None
        #print 'isBlockedOut'
        #print sub
        if sub not in self._block_out_till: # meaning sub is not a subject for this observer
            print '!!! congestion subject not found '
            ret = False
        else:
            future_time = self._block_out_till[sub]
            if future_time < 0: 
                ret = False
            elif future_time == 0:
                ret = True
            else:
                ret = (cur_time < future_time)

        if ret:
            print '!!! CongController: blocked till %f' % (future_time)
        return ret
