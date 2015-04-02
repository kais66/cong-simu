class Event(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp
    
    def execute(self):
        pass

    def printEvt(self):
        pass
        
class DownStackEvt(Event):
    def __init__(self, timestamp, node, dst_id):
        super(DownStackEvt, self).__init__(timestamp)
        self.node = node
        self.dst_id = dst_id

    def execute(self):
        # see if the app buffer is currently blocked, 
        if not node.src:
            raise AttributeError('node.src is None')
        
        chunk = node.src.downOneChunk(dst_id)
        self.printEvt()

    def printEvt(self):
        print 'executing DownStackEvt'

        
    
