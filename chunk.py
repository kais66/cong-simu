class Chunk:
    BEFORE_TX = 1
    DURING_TX = 2
    AT_DST = 3

    # src and dst are just ids, rather than references to the actual nodes
    def __init__(self, src, dst, size, ts, chk_id):
        self._size = size
        self._src_id = src
        self._dst_id = dst
        self._cur_id = src
        self._start_ts = ts # timestamp when the ultimate source pushes this chunk out
        self._cur_ts = ts # anytime when this chunk is in the network

        self._ecn_delay = 0.0 # this is the delay caused by ECN

        self._chk_id = chk_id
        self._state = Chunk.BEFORE_TX

        self._start_offset = -1
        self._end_offset = -1
        self._file_size = -1
        self._file_id = -1

    def initFileRelatedField(self, start_offset, end_offset, file_size):
        self._start_offset = start_offset
        self._end_offset = end_offset
        self._file_size = file_size
        #print 'file size: {}'.format(file_size)

        self._file_id = self._chk_id - self._start_offset

    def id(self):   
        return self._chk_id

    def fileId(self):
        return self._file_id

    def size(self):
        return self._size

    def src(self):
        return self._src_id

    def dst(self):
        return self._dst_id

    def curNode(self, node_id):
        return self._cur_id

    def updateCurNode(self, node_id):
        self._cur_id = node_id

    def setStatus(self, s):
        self._state = s

    def status(self):
        return self._state

    def updateTimestamp(self, time):
        assert time >= self._cur_ts
        self._cur_ts = time

    def setCurTimestamp(self, time):
        self._cur_ts = time

    def timestamp(self):
        return self._cur_ts

    def startTimestamp(self):
        return self._start_ts

    def setExperiencedECNDelay(self, delay):
        self._ecn_delay = delay

    def experiencedECNDelay(self):
        return self._ecn_delay

    def show(self):
        print 'chunk: id: %d, src: %d, dst: %d, cur: %d, size: %d, start_time: %f, cur_time: %f' % \
                (self._chk_id, self._src_id, self._dst_id, self._cur_id,
                 self._size, self._start_ts, self._cur_ts)

class File(object):
    '''
    Constructed only at the traffic sink: used to keep track of
    '''
    def __init__(self, chk):
        self._num_chks = chk._start_offset + chk._end_offset + 1
        self._chk_dict = {}

    def insertChk(self, chk):
        assert chk._chk_id not in self._chk_dict
        self._chk_dict[chk._chk_id] = chk

    def isComplete(self):
        return True if len(self._chk_dict) == self._num_chks else False
