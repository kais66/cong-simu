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
        self._length = 200000.0
        self._config = config

        self._cong_str = config.exp_type
        self._rate_str = config.rate_str 
        self._logger = None
        if self._config.use_ECN:
            self._logger = OutputLogger('output/respTimes_{}WithECN_{}.csv'.format(self._cong_str, self._rate_str))
        else:
            self._logger = OutputLogger('output/respTimes_{}_{}.csv'.format(self._cong_str, self._rate_str))

        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()

    def loadInput(self):
        ''' cong_str: 'PerFlow' or 'PerIf'; rate_str: integer between 3000 and 10000. '''
        print 'simulator:loadInput'
        tp = TopoGenerator('input_files/topo_9nodes.txt')

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

    def logToFile(self):
        self._logger.write()

if __name__ == '__main__':
    json_path = 'setting/base.json'
    config = Config(json_path, sys.argv)

    sim = Simulator(config)
    sim.loadInput()
    sim.run()
    sim.logToFile()
    print 'succeeded'
