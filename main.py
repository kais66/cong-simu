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

        self._logger, self._rate_logger = None, None
        # use a list to retain references to all loggers, in order to call
        # on each of these loggers
        self._logger_list = []
        self.initLoggers()

        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()

    def initLoggers(self):

        # response time logger
        if self._config.use_ECN:
            self._logger = OutputLogger('output/respTimes_{}WithECN_{}.csv'.format(self._cong_str, self._rate_str))
        else:
            self._logger = OutputLogger('output/respTimes_{}_{}.csv'.format(self._cong_str, self._rate_str))
        self._logger_list.append(self._logger)

        # rate logger, only for Token Bucket based AppBuf, in PerIf experiment
        if self._config.exp_type == 'PerIf' and self._config.use_ECN:
            self._rate_logger = OutputLogger('output/rate_{}.csv'.format(self._rate_str))
            self._logger_list.append(self._rate_logger)

    def rateLogger(self):
        return self._rate_logger

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

        traf_file = 'input_files/traff_poisson_{}.txt'.format(self._rate_str)
        if not os.path.exists(traf_file):
            raise IOError("traf_file doesn't exist: {}".format(traf_file))
        tf = TrafficGenerator(traf_file, self._config)
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

if __name__ == '__main__':
    json_path = 'setting/base.json'
    config = Config(json_path, sys.argv)

    sim = Simulator(config)
    sim.loadInput()
    sim.run()
    sim.logToFile()
    print 'succeeded'
