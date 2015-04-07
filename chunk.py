class Chunk:
    def __init__(self, src, dst, size, ts): # src and dst are just ids, rather than references to the actual nodes
        self._size = size
        self._src_id = src
        self._dst_id = dst
        self._cur_id = src
        self._start_ts = ts # timestamp when the ultimate source pushes this chunk out
        self._cur_ts = 0.0 # anytime when this chunk is in the network

    def size(self):
        return self._size

    def src(self):
        return self._src_id

    def dst(self):
        return self._dst_id

    def curNode(self, node_id):
        self.cur_id = node_id

    def timestamp(self, time):
        self._cur_ts = time

    def timestamp(self):
        return self._cur_ts

    def startTimestamp(self):
        return self._start_ts

    def show(self):
        print 'chunk: src: %d, dst: %d, cur: %d, size: %d, time: %f' % \
                (self._src_id, self._dst_id, self._cur_id, self._size, self._cur_ts)
