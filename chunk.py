class Chunk:
    BEFORE_TX = 1
    DURING_TX = 2
    AT_DST = 3
    def __init__(self, src, dst, size, ts, chk_id): # src and dst are just ids, rather than references to the actual nodes
        self._size = size
        self._src_id = src
        self._dst_id = dst
        self._cur_id = src
        self._start_ts = ts # timestamp when the ultimate source pushes this chunk out
        self._cur_ts = ts # anytime when this chunk is in the network

        self._chk_id = chk_id
        self._state = Chunk.BEFORE_TX

    def id(self):   
        return self._chk_id

    def size(self):
        return self._size

    def src(self):
        return self._src_id

    def dst(self):
        return self._dst_id

    def curNode(self, node_id):
        self.cur_id = node_id

    def setStatus(self, s):
        self._state = s

    def status(self):
        return self._state

    def updateTimestamp(self, time):
        assert time >= self._cur_ts
        self._cur_ts = time

    def timestamp(self):
        return self._cur_ts

    def startTimestamp(self):
        return self._start_ts

    def show(self):
        print 'chunk: id: %d, src: %d, dst: %d, cur: %d, size: %d, start_time: %f, cur_time: %f' % \
                (self._chk_id, self._src_id, self._dst_id, self._cur_id, self._size, self._start_ts, self._cur_ts)
