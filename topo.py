from node import *
from chunk import *
import sys

class BaseBufManBuilder(object):
    band = 131072 # unit: byte per ms, == 1Gbps
    lat = 10 # ms
    def __init__(self):
        pass

    def buildBufMan(self, simu, node, if_id): # interface id, because each interface has a buf man
        pass

class BufManBuilderPerFlow(BaseBufManBuilder):
    def buildBufMan(self, simu, node, if_id):
        buf_man = LinkBufferManagerPerFlow(simu, if_id, BaseBufManBuilder.band, BaseBufManBuilder.lat)
        buf_man.attachNode(node)
        node.attachBufMan(buf_man)
        node.addWeight(BaseBufManBuilder.lat) # by default, use latency as link weight

class BufManBuilderPerIf(BaseBufManBuilder):
    def buildBufMan(self, simu, node, if_id):
        buf_man = LinkBufferManagerPerIf(simu, if_id, BaseBufManBuilder.band, BaseBufManBuilder.lat)
        buf_man.attachNode(node)
        node.attachBufMan(buf_man)
        node.addWeight(BaseBufManBuilder.lat) # by default, use latency as link weight


class TrafficGenerator(object):
    ''' 
        Load the traffic profile from input file, generate corresponding events and insert them into sender's buffers.
    '''
    def __init__(self, traff_file):
        self.src, self.dst = {}, {} # node_id : Node
        self.traff_file = traff_file

    def parseTrafficFile(self, node_dic, simu):
        try:
            f = open(self.traff_file, 'r')
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            sys.exit()
        for line in f:
            if not line or line[0] == '#': continue
            words = line.split(',')
            if len(words) != 4: 
                print 'Error'
                continue

            node = None
            try:
                src_id, dst_id= int(words[0]), int(words[1])
                if src_id not in node_dic or dst_id not in node_dic:
                    print 'error'
                    sys.exit()

                chk = Chunk(int(words[0]), int(words[1]), int(words[2]))
                node = node_dic[src_id]
                if not node.src:
                    src = TrafficSrc(node, None)
                    buf_man = AppBufferManager(simu, 0)
                    buf_man.attachNode(node)
                    src.attachBufMan(buf_man)
                    node.attachSrc(src)
                node.src.pushAppBuffer(chk)

            except ValueError as e:
                print "Value error({0}): {1}".format(e.errno, e.strerror)
                sys.exit()
        f.close()

class TopoGenerator(object):
    def __init__(self, topo_file): 
        self.topo_file = topo_file
        self.node_dic = {}
         
    def parseTopoFile(self, simu, buf_man_builder):
        try:
            f = open(self.topo_file, 'r')
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            sys.exit()

        for line in f:
            if not line or line[0] == '#': continue
            words = line.split(',')
                
            try:
                node = None
                node_id = int(words[0])
                if node_id not in self.node_dic:
                    self.node_dic[node_id] = Node(node_id, None)

                    #buf_man = BaseBufferManager(simu)
                    #buf_man.attachNode(node)
                    #node.attachBufMan(buf_man)

                    #self.node_dic[node_id] = node
                node = self.node_dic[node_id]

                for i in range(2, len(words)):
                    try:
                        nbr_id = int(words[i])
                    except ValueError:
                        #print 'exception: words[i]: %s' % (words[i],)
                        continue

                    nbr = None
                    if nbr_id not in self.node_dic:
                        self.node_dic[nbr_id] = Node(nbr_id, None)
                        #nbr = Node(nbr_id, None)
                        #buf_man = BaseBufferManager(simu)
                        #buf_man.attachNode(nbr)
                        #nbr.attachBufMan(buf_man)
                        #self.node_dic[nbr_id] = nbr
                    nbr = self.node_dic[nbr_id] 
                    node.addNbr(nbr)
                    buf_man_builder.buildBufMan(simu, node, nbr.id)

            except ValueError as e:
                print "Value error({}): {1}"
                print 'words' 
                print words
                sys.exit(-1)
        f.close()
    def getNodeDic(self):
        return self.node_dic

    def genRouteTable(self, simu):
        pass

class LinkProfileInitializer(object):
    DEFAULT_BANDWIDTH = 131072000 # 125*1024*1024, 1Gbps == 125MBps
    LATENCY = 10 # ms
