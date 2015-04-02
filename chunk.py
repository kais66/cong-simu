class Chunk:
    def __init__(self, src, dst, size): # src and dst are just ids, rather than references to the actual nodes
        self._size = size
        self._src_id = src
        self._dst_id = dst
        self._cur_id = src
        self._ts = 0.0

    def size(self):
        return self._size

    def src(self):
        return self._src_id

    def dst(self):
        return self._dst_id

    def curNode(self, node_id):
        self.cur_id = node_id

    def timestamp(self, time):
        self._ts = time

    def timestamp(self):
        return self._ts

    def show(self):
        print 'chunk: src: %d, dst: %d, cur: %d, size: %d, time: %f' % \
                (self._src_id, self._dst_id, self._cur_id, self._size, self._ts)
