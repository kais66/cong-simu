# python lib
#import Queue
import sys
import os

# my own modules
from topo import *
from prio_queue import HeapElement, PrioQueue
from config import Config

class Simulator(object):
    def __init__(self, config):
        ''' config is a Config object '''
        self._queue = Queue.PriorityQueue()
        #self._queue = PrioQueue()
        self._node_dic = {}
        self._sim_time = 0.0

        # debug running time
        #self._length = 50000.0

        # regular running time
        self._length = 100000.0 # 100s
        self._config = config

        self._cong_str = config.exp_type
        self._rate_str = config.rate_str

        self._logger, self._rate_logger, self._queue_len_logger = None, None, None
        self._ecn_logger = None

        # use a list to retain references to all loggers, in order to call
        # on each of these loggers
        self._logger_list = []
        self.initLoggers()

        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()

    def initLoggers(self):

        # response time logger
        ECN_str = 'WithECN' if self._config.use_ECN else ''
        self._logger = OutputLogger('output/respTimes_{}{}_{}.csv'.format(
            self._cong_str, ECN_str, self._rate_str))
        self._queue_len_logger = OutputLogger('output/queueLen_{}{}_{}.csv'.
            format(self._cong_str, ECN_str, self._rate_str))

        self._logger_list.append(self._logger)
        self._logger_list.append(self._queue_len_logger)

        # rate logger, only for Token Bucket based AppBuf, in PerIf experiment
        if self._config.exp_type == 'PerIf' and self._config.use_ECN:
            self._rate_logger = OutputLogger('output/rate_{}.csv'.format(
                self._rate_str))
            self._logger_list.append(self._rate_logger)

            self._ecn_logger = OutputLogger('output/ecn_{}.csv'.format(
                self._rate_str))
            self._logger_list.append(self._ecn_logger)




    def rateLogger(self):
        return self._rate_logger

    def queueLenLogger(self):
        return self._queue_len_logger

    def ecnLogger(self):
        return self._ecn_logger

    def loadInput(self):
        ''' cong_str: 'PerFlow' or 'PerIf'; rate_str: integer between 3000 and 10000. '''
        topo_file = 'topo_files/{}.topo'.format(self._config.topo_str)
        print 'simulator:loadInput, using topology: {}'.format(topo_file)
        tp = TopoGenerator(topo_file)

        fac = BuilderFactory(self._config)
        builder = fac.getBuilder()

        tp.parseTopoFile(self, builder)
        tp.genForwardTable(self)
        self._node_dic = tp.getNodeDic()
        builder.genObservers(self, tp)

        #traf_file = 'input_files/traff_poisson_{}.txt'.format(self._rate_str)

        traff_file = 'input_files/{}/{}_{}.traff'.format(self._config.topo_str,
                self._config.traff_str, self._config.rate_str)
        if not os.path.exists(traff_file):
            raise IOError("traf_file doesn't exist: {}".format(traff_file))
        tf = TrafficGenerator(traff_file, self._config)
        tf.parseTrafficFile(self._node_dic, self)

    def enqueue(self, event):
        #print 'simu:enqueue, evt with timestamp: %f' % (event.timestamp(),)
        #print 'evt q len: %d' % (self._queue.qsize())

        self._queue.put((event.timestamp(), event,))

        ## if using the customized priority queue
        #heapElement = HeapElement(event.timestamp(), event)
        #self._queue.put(heapElement)
        #return heapElement

    def run(self):
        print 'simu:run'
        # initialize network

        # run
        print 'evt q len: %d' % (self._queue.qsize())
        while self._sim_time < self._length and not self._queue.empty():
            ev = self._queue.get()[1] # get() returns a tuple
            #ev = self._queue.get().appObject() 
            self._sim_time = ev.timestamp()
            ev.execute()


    def time(self):
        return self._sim_time

    def advanceTimeTo(self, newtime):
        if newtime < self._sim_time:
            print 'error'
        self._sim_time = newtime

    def getNodeById(self, nid):
        if nid not in self._node_dic:
            raise KeyError('nid: %d not in dic' % (nid,))
        else:
            return self._node_dic[nid]

    def nodes(self):
        return self._node_dic.values()

    def nodesDic(self):
        return self._node_dic

    def registerLogger(self, logger):
        self._logger_list.append(logger)

    def logToFile(self):
        for logger in self._logger_list:
            logger.write()

    def calcLatency(self, src_id, dst_id):
        '''
        public interface. Calculate raw aggregated link latencies between a src and a dst
        :param src_id:
        :param dst_id:
        :return:
        '''
        cur_id = src_id
        latency = 0.0
        while cur_id != dst_id:
            cur_node = self._node_dic[cur_id]
            buf_man = cur_node.getBufManByDst(dst_id)
            latency += buf_man.latency()
            print 'simu.calcLatency: latency between {} and {} is: {}'.format(
                cur_id, buf_man.id(), buf_man.latency())
            cur_id = buf_man.id()
        print 'simu.calcLatency: overall latency between {} and {} is: {}'.format(
                src_id, dst_id, latency)
        return latency

    def writeHopCountFile(self):
        # this function is not supposed to run along with the simulator.
        file_path = 'topo_files/{}.hop'.format(self._config.topo_str)
        with open(file_path, 'w') as f:
            node_id_list = self.nodesDic().keys()
            num_node = len(node_id_list)
            for node_pos in xrange(num_node):
                node_id = node_id_list[node_pos]
                for nbr_pos in xrange(num_node):
                    nbr_id = node_id_list[nbr_pos]
                    if node_id >= nbr_id: continue
                    line = '{},{},{}\n'.format(node_id, nbr_id,
                            self.calcHopCount(node_id, nbr_id))
                    f.write(line)


    def calcHopCount(self, src_id, dst_id):
        '''
        public interface. Calculate raw aggregated link latencies between a src and a dst
        :param src_id:
        :param dst_id:
        :return:
        '''
        cur_id = src_id
        count = 0
        while cur_id != dst_id:
            cur_node = self._node_dic[cur_id]
            buf_man = cur_node.getBufManByDst(dst_id)
            count += 1
            cur_id = buf_man.id()
        return count


if __name__ == '__main__':
    json_path = 'setting/base.json'
    config = Config(json_path, sys.argv)

    sim = Simulator(config)
    sim.loadInput()

    #sim.writeHopCountFile()
    #sys.exit()

    sim.run()
    sim.logToFile()
    print 'succeeded'
