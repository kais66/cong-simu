# python lib
import Queue
import sys
import os

# my own modules
from topo import *

class Simulator(object):
    def __init__(self, cong_str, rate_str):
        self._queue = Queue.PriorityQueue()
        self._node_dic = {}
        self._sim_time = 0.0
        self._length = 200000.0

        self._cong_str = cong_str
        self._rate_str = rate_str 
        self._logger = OutputLogger('output/respTimes_{}_{}.csv'.format(self._cong_str, self._rate_str))
        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()

    def loadInput(self):
        ''' cong_str: 'PerFlow' or 'PerIf'; rate_str: integer between 3000 and 10000. '''
        print 'simulator:loadInput'
        tp = TopoGenerator('input_files/topo_9nodes.txt')

        fac = BuilderFactory(self._cong_str)
        builder = fac.getBuilder()

        tp.parseTopoFile(self, builder)
        tp.genForwardTable(self)
        self._node_dic = tp.getNodeDic()
        builder.genObservers(self, tp)

        traf_file = 'input_files/traff_poisson_{}.txt'.format(self._rate_str)
        if not os.path.exists(traf_file):
            raise IOError("traf_file doesn't exist: {}".format(traf_file))
        tf = TrafficGenerator(traf_file)
        tf.parseTrafficFile(self._node_dic, self)

    def enqueue(self, event):
        #print 'simu:enqueue, evt with timestamp: %f' % (event.timestamp(),)
        #print 'evt q len: %d' % (self._queue.qsize())
        self._queue.put((event.timestamp(), event,))

    def run(self):
        print 'simu:run'
        # initialize network

        # run
        print 'evt q len: %d' % (self._queue.qsize())
        while self._sim_time < self._length and not self._queue.empty():
            ev = self._queue.get()[1] # get() returns a tuple
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
    if len(sys.argv) != 3: 
        print 'usage: main.py cong_str rate_str'
        sys.exit(-1)
    
    sim = Simulator(sys.argv[1], sys.argv[2])
    sim.loadInput()
    sim.run()
    sim.logToFile()
    print 'succeeded'
