class Chunk:
    def __init__(self, src, dst, size): # src and dst are just ids, rather than references to the actual nodes
        self.size = size
        self.src_id = src
        self.dst_id = dst
        self.cur_id = src

    def getSize(self):
        return self.size

    def src(self):
        return self.src_id
    def dst(self):
        return self.dst_id

    def curNode(self, node_id):
        self.cur_id = node_id
