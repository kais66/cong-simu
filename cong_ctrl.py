from node import *

class BaseCongController(object):
    ''' Implementing the subject class: which owns a group of observers. When notify() is called 
        for that observer, its status should be set to 'blocked'. '''
    def __init__(self):
        self._obs = [] # list of observers
        self._buf = None

        # whether traffic into this buffer is currently blocked
        self._block_in = False

        # till when is outgoing traffic blocked: -1 means not blocked, 0 means blocked indefinitely, otherwise
        # blocked until the nominal time.
        self._block_out_till = -1.0 

    def attachObserver(self, obs):
        self.obs.append(obs)

    def detachObserver(self, obs):
        pass

    def updateState(self):
        pass

    def notifyCong(self, future_time): 
        ''' isCong: bool. Identifying whether this is to activate or deactivate back pressure '''
        for ob in self.obs:
            ob._block_out_till = future_time


    def notifyNoCong(self):
        pass

    def notifyOne(self, obs): 
        ''' signal a specific node about the congestion, it could ask a particular node to resend after some time. '''
        pass

    def isBlockedOut(self, cur_time):
        ''' cur_time is a float ''' 
        if self._blocked_out_till < 0:
            return False
        elif self._blocked_out_till == 0:
            return True
        else:
            return cur_time < self._blocked_out_till

# as of now, Apr 13th, it's implemented as per-dst queuing, but this can be extended.
class CongControllerPerFlow(BaseCongController):
    ''' Each observer is an upstream buffer. CongCtrl algo is to limit num outstanding chunks to be H, 
        this is done on a buffer to buffer basis (downstream buffer, i.e. subject, notify 
        upstream buffer, i.e. observer). '''
    def updateState(self):
        if not self._block_in and self._buf.numChunks() >= 1:
            self._block_in = True
            self.notifyCong(0)

# A problem with per-if queuing is: if multiple upstream outgoing buffer
class CongControllerPerIf(BaseCongController):
    ''' Per interface queuing. 1. Subject is an interface, i.e. perIfBuf (note not buf_man). A buf has limit on buffering, if this
        limit is reached, it's not accepting additional data. For each upstream node, essentially blocking all 
        flows that will travel through the congested interface. 2. The congested interface can also notify the 
        source of the traffic, i.e. app_buf_man of a source node. ''' 
    pass
