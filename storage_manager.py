class StorageManager(object):
    ''' 
        How storage is used: 
    '''
    def __init__(self, node):
        self._node = node
        self._interface_queue = {} # next_hop : FIFO queue of stored chunks
        self.initStorageQueues()

        self._MAX_BYTE = 0 # should be some large number
        self._cur_byte = 0

    def initStorageQueues(self):
        for nbr in self._node.nbrs:
            self._interface_queue[nbr] = collections.deque()

    def __spaceAvailable(self, chunk):
        return True if self._cur_byte + chunk.size() <= self._MAX_BYTE else False
        
    def putChunk(self, chunk):
        ''' Push chunk to storage. if put() is successful, returns True '''
        if not self.__spaceAvailable(chunk):
            return False
        
        next_hop = self._node.getNextHop(chunk.dst()) 
        self._interface_queue[next_hop].append(chunk)
        return True

    def getChunkByBufMan(self, buf_man_id):
        queue = self._interface_queue[buf_man_id]
        if not queue:
            return None
        return queue.popleft()
