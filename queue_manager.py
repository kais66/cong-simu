###############################################################################
# queue_manager.py 
# installed at bufManm provides ECN feedback to src
# This class implements ECN operation at routers.
###############################################################################
import random
from node import Node, TrafficSrc
from buffer_manager import *

class BaseQueueManager(object):
    EXP_BACKOFF_MEAN = 10 # in milliseconds
    def __init__(self, buf_man, simu):
        self._buf_man = buf_man 
        self._simu = simu

    def decideFlowDelay(self, chunk):
        ''' 
            Based on the current occupancy, determine how long the flow src should backoff. 
            This basic version applies a exponential delay, multiplied by occupancy.
        '''
        occupancy_percent = self._buf_man.occupancyPercent()
        print 'BaseQueueManager.decideFlowDelay(): occupancy_percent: {}'.format(occupancy_percent)
        if occupancy_percent <= 0.2:
            return 0.0

        #if chunk.dst() != 9:
        #    return 0.0

        mean = BaseQueueManager.EXP_BACKOFF_MEAN        
        delay = random.expovariate(1.0 / mean)
        return delay
        

    def applyFlowDelay(self, src_id, dst_id, delay):
        ''' get the src node, add delay to (src, dst)'s current delay '''
        print 'BaseQueueManager.applyFlowDelay: src: {}, dst: {}, delay: {}' \
                .format(src_id, dst_id, delay)
        srcNode = self._simu.getNodeById(src_id)
        srcNode.src.app_buf_man.addDelay(dst_id, delay)

class CongSrcQueueManager(BaseQueueManager):
    def decideFlowDelay(self, chunk):
        # if this is a blocked interface (buffer), don't do ECN base on it.
        # Becuase this is not the source of congestion
        cong_ctrl = self._buf_man._buffer.congCtrl()
        
        if cong_ctrl.numBlockOut() > 0:
            return 0.0

        occupancy_percent = self._buf_man.occupancyPercent()
        if occupancy_percent <= 0.5:
            return 0.0

        # use a quadratic function to do backoff
        #gain = (occupancy_percent * 10) ** 3
        gain = (occupancy_percent * 10) ** 2 

        delay = BaseQueueManager.EXP_BACKOFF_MEAN * gain
        print 'CongSrcQueueManager.decideFlowDelay(): occupancy_percent: {}, delay: {}' \
            .format(occupancy_percent, delay)
        return delay
        