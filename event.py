class Event(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp
    
    def execute(self):
        pass

    def printEvt(self):
        pass
        
class DownStackEvt(Event):
    ''' Pushing a chunk from app buffer onto link layer buffer for sending '''
    def __init__(self, timestamp, node, dst_id):
        super(DownStackEvt, self).__init__(timestamp)
        self.node = node
        self.dst_id = dst_id

    def execute(self):
        # see if the app buffer is currently blocked, 
        if not self.node.src:
            raise AttributeError('node.src is None')
        
        self.printEvt()
        chunk = self.node.src.downOneChunk(self.dst_id)
        if chunk:
            chunk.show()
        else:
            print 'DownStackEvt: no chunk to be pushed down'

    def printEvt(self):
        print 'executing DownStackEvt'

class TxEvt(Event):
    def __init__(self, timestamp, node, dst_id):
        pass  
