from node import *

class BaseCongController(object):
    ''' Implementing the subject class: which owns a group of observers. When notify() is called 
        for that observer, its status should be set to 'blocked'. '''
    def __init__(self):
        self._obs = [] # list of observers
        self._buf = None

        # whether traffic into this buffer is currently blocked
        self._block_in = False

    def attachBuf(self, buf):
        self._buf = buf

    def attachObserver(self, obs):
        if obs is not self:
            self._obs.append(obs)

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
    def __init__(self):
        super(CongControllerPerFlow, self).__init__()
        self._ostd_chk_limit = 1

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

    def notifyNoCong(self, sub):
        for ob in self._obs:
            ob._block_out_till = -1.0

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
    ''' Per interface queuing. 1. Subject is an interface, i.e. perIfBuf (note not buf_man). A buf has limit on buffering, if this
        limit is reached, it's not accepting additional data. For each upstream node, essentially blocking all 
        flows that will travel through the congested interface. 2. The congested interface can also notify the 
        source of the traffic, i.e. app_buf_man of a source node. 
        Note: another way of per-interface queuing is: a shared buffer space for all outgoing interfaces. This implementation is 
        for the first way. ''' 
    def __init__(self):
        super(CongControllerPerIf, self).__init__()
        self._block_out_till = {} # cong_ctrl_subject : future_time

    def updateBlockInState(self, future_time=None):
        if not self._block_in and self._buf.numBytes() >= self._buf.capacity():
            self._block_in = True
            print 'BlockInState: --> blocked, node: %d, buf: %d' % \
                (self._buf.node().id(), self._buf.id())
            self.notifyCong(self, 0)
            return True
        return False

    def notifyNoCong(self, sub):
        for ob in self._obs:
            ob._block_out_till[sub] = -1.0

    def notifyCong(self, sub, future_time):
        for ob in self._obs:
            ob._block_out_till[sub] = future_time
            print 'notifyCong: block_out: node: %d, buf: %d, block_in: node: %d, buf: %d' % \
                (ob._buf.node().id(), ob._buf.id(), sub._buf.node().id(), sub._buf.id())
            print ob
            print sub
            

    def isBlockedOut(self, sub, cur_time):
        ret = None
        print 'isBlockedOut'
        print sub
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
            print '!!! CongController: blocked. '
        return ret
