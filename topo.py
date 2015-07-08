from node import *
from buffer_manager import *
from chunk import *
import sys
import Queue

class BuilderFactory(object):
    def __init__(self, config):
        self.config = config

    def getBuilder(self):
        ret = None
        exp_type = self.config.exp_type
        if exp_type == 'PerFlow':
            ret = BufManBuilderPerFlow(self.config)
        elif exp_type == 'PerIf':
            ret = BufManBuilderPerIf(self.config)
        else:
            raise AttributeError('wrong string')
        return ret

class BaseBufManBuilder(object):
    #band = 131072.0 # unit: byte per ms, == 1Gbps
    band = 6750.0 # byte per ms, == 54 Mbps
    lat = 5.0 # ms

    def __init__(self, config):
        self.config = config

    # interface id, because each interface has a buf man
    def buildBufMan(self, simu, node, if_id):
        pass

    def genObservers(self, simu, topo):
        pass

class BufManBuilderPerFlow(BaseBufManBuilder):
    def buildBufMan(self, simu, node, if_id):
        buf_man = LinkBufferManagerPerFlow(simu, if_id, BaseBufManBuilder.band,
                                           BaseBufManBuilder.lat)
        buf_man.attachNode(node)
        node.attachBufMan(buf_man)
        node.addWeight(BaseBufManBuilder.lat) # by default, use latency as link weight
        #evt = TxStartEvt(simu, 0.0, buf_man)
        #simu.enqueue(evt)

    def genObservers(self, simu, topo):
        ''' output: dic = {node_id : {flow_id(dst_id) : upstream_id}} '''
        nd_obs_dic = {} # {node_id : {flow_id(dst_id) : [upstream_ids]}}
        for nd in simu.nodes():
            for dst_id in nd.nextHopDic():
                next_hop = nd.nextHopDic()[dst_id]

                #if next_hop not in nd_obs_dic:
                #    nd_obs_dic[next_hop] = {}
                #cur_obs_dic = nd_obs_dic[next_hop]
                #if dst_id not in cur_obs_dic:
                #    cur_obs_dic[dst_id] = []

                self.attachObserver(simu.nodesDic()[next_hop], dst_id, nd)

    def attachObserver(self, cur_nd, dst_id, pred_nd):
        if cur_nd.id() == dst_id:
            return 
        print 'Builder:attachObs: cur_nd: %d, dst: %d, pred: %d' \
                % (cur_nd.id(), dst_id, pred_nd.id())
        cur_buf = cur_nd.getBufManByDst(dst_id).getBufById(dst_id)
        pred_buf = pred_nd.getBufManByDst(dst_id).getBufById(dst_id)
        cur_buf.attachCongObserver(pred_buf.congCtrl())


class BufManBuilderPerIf(BaseBufManBuilder):
    def buildBufMan(self, simu, node, if_id):
        buf_man = LinkBufferManagerPerIf(simu, if_id, BaseBufManBuilder.band, BaseBufManBuilder.lat)
        buf_man.attachNode(node)

        assert node is not None
        self.buf_man = buf_man
        node.attachBufMan(buf_man)
        node.addWeight(BaseBufManBuilder.lat) # by default, use latency as link weight

        # here, addBuffer() has to come after buf_man is attached to the node
        buf_man.addBuffer(buf_man.id())

        # if ECN,
        if self.config.use_ECN:
            #queue_man = BaseQueueManager(buf_man, simu)
            queue_man = QueueManagerTB(buf_man, simu)
            buf_man.attachQueueMan(queue_man)

        #evt = TxStartEvt(simu, 0.0, buf_man)
        #simu.enqueue(evt)

    def genObservers(self, simu, topo):
        for nd in simu.nodes():
            for man in nd.buf_man.values():
                for nbr in nd.nbrs:
                    self.attachObserver(man, nbr)

    def attachObserver(self, cur_buf_man, pred_nd):
        print 'Builder:attachObs: cur_nd: %d, cur_buf_man: %d, pred: %d' \
                % (cur_buf_man._node.id(), cur_buf_man.id(), pred_nd.id(),)
        cur_buf = cur_buf_man.getBufById(cur_buf_man.id())
        pred_buf_man = pred_nd.getBufManByNextHop(cur_buf_man.node().id())
        cur_buf.attachCongObserver(pred_buf_man.getBufById(pred_buf_man.id()).congCtrl())

class BufManBuilderPerIfWithECN(BaseBufManBuilder):
    def buildBufMan(self, simu, node, if_id):
        pass

class TrafficGenerator(object):
    ''' 
        Load the traffic profile from input file, generate corresponding events
        and insert them into sender's buffers.
    '''
    def __init__(self, traff_file, config):
        self.src, self.dst = set(), {} # node_id : Node
        self.traff_file = traff_file
        self.config = config

    def parseTrafficFile(self, node_dic, simu):
        try:
            f = open(self.traff_file, 'r')
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            sys.exit()
        for line in f:
            if not line or line[0] == '#': continue
            words = line.split(',')
            if len(words) != 8:
                print 'Error'
                continue

            node = None
            try:
                src_id, dst_id= int(words[0]), int(words[1])
                if src_id not in node_dic or dst_id not in node_dic:
                    print 'error'
                    sys.exit()

                chk_size, arrival_time = int(words[2]), float(words[3])
                chk_id = int(words[-1])
                chk = Chunk(src_id, dst_id, chk_size, arrival_time, chk_id)

                # file related, in addition to chunk related, fields
                start_offset, end_offset, file_size = int(words[4]), \
                                            int(words[5]),int(words[6])
                chk.initFileRelatedField(start_offset, end_offset, file_size)

                node = node_dic[src_id]
                if not node.src:

                    src = TrafficSrc(node, None)

                    # if ECN
                    buf_man = None
                    if self.config.use_ECN:
                        # buf_man = AppBufferManagerWithECN(simu, 0)
                        buf_man = AppBufferManagerTB(simu, 0)
                    else:
                        buf_man = AppBufferManager(simu, 0)
                    buf_man.attachNode(node)
                    src.attachBufMan(buf_man)
                    node.attachSrc(src)
                node.src.pushAppBuffer(chk)

                dst_node = node_dic[dst_id]
                if not dst_node.sink:
                    sink = TrafficSink(dst_node, simu._logger)
                    dst_node.attachSink(sink)

            except ValueError as e:
                print "Value error({0}): {1}".format(e.errno, e.strerror)
                sys.exit()
        f.close()

class TopoGenerator(object):
    def __init__(self, topo_file): 
        self.topo_file = topo_file
        self.node_dic = {}
        self.src_pred_dic = {} # { dst : {node_id : pred_id}}

        # parameters identifying if ECN/storage is enabled
        self.is_ECN = False
        self.is_storage = False

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
                    print "added node %d's nbr: %d" % (node._id, nbr._id)
                    buf_man_builder.buildBufMan(simu, node, nbr._id)

            except ValueError as e:
                print "Value error({}): {1}"
                print 'words' 
                print words
                sys.exit(-1)
        f.close()

    def getNodeDic(self):
        return self.node_dic

    def genForwardTable(self, simu):
        ''' forward table is the next_hop dictionary in each node object '''
        for node in self.node_dic.values():
            self.dijkstra(node)
        #self.dijkstra(self.node_dic[3])

    def dijkstra(self, node):
        ''' 
            '''
        # init
        q = Queue.PriorityQueue()
        q.put((0, node,))

        dist, pred = {}, {} # distance and predecessor
        visited = set()
        for nd in self.node_dic.values():
            dist[nd.id()] = sys.maxint
        dist[node.id()] = 0
        next_hop = {}

        # the second condition, along with visited node checking,
        # guarantees we only visit each node once. Thus without
        # using decrease-key, we still achieve running time of O((V+E)*lgV)
        while not q.empty() and len(visited) < len(self.node_dic):
            nd = q.get()[1]
            if nd.id() in visited: continue
            
            #print 'dijk: visiting node: %d' % (nd.id())
            visited.add(nd.id())

            # next hop bookkeeping 
            if nd.id() != node.id():
                if pred[nd.id()] == node.id(): # immediate 
                    next_hop[nd.id()] = nd.id()
                elif pred[nd.id()] in next_hop:
                    next_hop[nd.id()] = next_hop[pred[nd.id()]]
                else:
                    raise ValueError('dijkstra: next hop not found')
                    sys.exit(-1)

            # Dijkstra relaxation 
            for i in xrange(len(nd.nbrs)):
                nbr, weight = nd.nbrs[i], nd.weights[i]
                if dist[nbr.id()] > dist[nd.id()] + weight:
                    #print 'dijk: visiting nbr: %d' % (nbr.id())
                    dist[nbr.id()] = dist[nd.id()] + weight
                    pred[nbr.id()] = nd.id()
                    q.put((dist[nbr.id()], nbr))

        node.next_hop = next_hop
        #print next_hop

        self.src_pred_dic[node.id()] = pred


