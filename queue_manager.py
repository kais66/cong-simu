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
    SET_POINT_RATIO = 0.5
    def __init__(self, buf_man, simu):
        self._buf_man = buf_man 
        self._simu = simu


    def doECN(self, chunk):
        delay = self.decideFlowDelay(chunk)
        if delay > 0.0:
            self.applyFlowDelay(chunk.src(), chunk.dst(), delay)

    def needECN(self):
        cong_ctrl = self._buf_man._buffer.congCtrl()

        # if cur node is blocked out, this is not a source of congestion
        if cong_ctrl.numBlockOut() > 0:
            return False

        occupancy_percent = self._buf_man.occupancyPercent()
        print 'queueMan.needECN: occupancy percentage: {}'.format(occupancy_percent)
        if occupancy_percent <= BaseQueueManager.SET_POINT_RATIO:
            return False

        return True

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
        if occupancy_percent <= BaseQueueManager.SET_POINT_RATIO:
            return 0.0

        # use a quadratic function to do backoff
        #gain = (occupancy_percent * 10) ** 3
        gain = (occupancy_percent * 10) ** 2 

        delay = BaseQueueManager.EXP_BACKOFF_MEAN * gain
        print 'CongSrcQueueManager.decideFlowDelay(): occupancy_percent: {}, delay: {}' \
            .format(occupancy_percent, delay)
        return delay
        
class QueueManagerTB(BaseQueueManager):
    def __init__(self, buf_man, simu):
        super(QueueManagerTB, self).__init__(buf_man, simu)

        #self._rate_adaptor = BaseRateAdaptor()
        #self._rate_adaptor = QuadraticRateAdaptor()
        self._rate_adaptor = FairRateAdaptor()

    def doECN(self, chunk):
        '''
        based on queue occupancy, adjust (or maintain) the src's rate.
        :param chunk:
        :return:
        '''


        self.__adjustSrcRate(chunk)


    def __adjustSrcRate(self, chunk):
        '''
        assuming need to do ECN, determine and apply the new rate for traffic src
        :param chunk: a Chunk object
        :return: return a float
        '''
        print 'queueMan: adjustSrcRate:'
        src_id = chunk.src()
        dst_id = chunk.dst()

        src_node = self._simu.getNodeById(src_id)
        src_buf = src_node.src.app_buf_man.getBufById(dst_id)

        occupancy_percent = self._buf_man.occupancyPercent()

        #new_rate = self._rate_adaptor.newRate(src_buf.rate, occupancy_percent)
        new_rate = self._rate_adaptor.newRate(src_buf.last_inc_rate,
                                              occupancy_percent, self._buf_man.bandwidth())
        if new_rate < src_buf.rate:
            src_buf.setRate(new_rate)

class BaseRateAdaptor(object):
    def newRate(self, old_rate, occupancy_percent):
        return float(old_rate) / 2

class QuadraticRateAdaptor(BaseRateAdaptor):
    def newRate(self, old_rate, occupancy_percent):
        occupancy_percent = min(occupancy_percent, 1.0)
        gain = ((occupancy_percent - BaseQueueManager.SET_POINT_RATIO) * 10) ** 2
        reduction = float(old_rate) / 100 * gain
        new_rate = old_rate - reduction
        return new_rate

class FairRateAdaptor(BaseRateAdaptor):
    def newRate(self, old_rate, occupancy_percent, link_capacity):
        num_flow = 40
        fair_share = link_capacity / num_flow
        return fair_share

