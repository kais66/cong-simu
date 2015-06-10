###############################################################################
# queue_manager.py 
# installed at node/bufManm provides ECN feedback to src
###############################################################################
class QueueManager(object):
    def __init__(self, node):
        self._node = node

    def decideFlowDelay(self, chunk):
        ''' Given the current occupancy, determine how long the flow src should backoff '''
        pass

    def applyFlowDelay(self, src_id, dst_id, delay):
        ''' get the src node, add delay to (src, dst)'s current delay '''
        pass
