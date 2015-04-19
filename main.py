# python lib
import Queue

# my own modules
from topo import *


class Simulator(object):
    def __init__(self):
        self._queue = Queue.PriorityQueue()
        self._node_dic = {}
        self._sim_time = 0.0
        self._length = 150

        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()

    def loadInput(self):
        print 'simulator:loadInput'
        #Simulator.queue = Queue.PriorityQueue()

        tp = TopoGenerator('/Users/SunnySky/workspace/cong-simu/input_files/topo_9nodes.txt')
        tp.parseTopoFile(self, BufManBuilderPerFlow())
        tp.genForwardTable(self)

        self._node_dic = tp.getNodeDic()
        tf = TrafficGenerator('input_files/traff.txt')
        tf.parseTrafficFile(self._node_dic, self)

        link_prof = LinkProfileInitializer()

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

if __name__ == '__main__':
    sim = Simulator()
    sim.loadInput()
    sim.run()
    print 'succeeded'
