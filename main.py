# python lib
import Queue

# my own modules
from topo import *


class Simulator(object):
    #def __new__(cls, *args, **kwargs):
    #    if not cls._singleton:
    #        cls._singleton = super(Simulator, cls).__new__(cls, *args, **kwargs)
            #cls._singleton.queue = None
    #    return cls._singleton

    def __init__(self):
        self._queue = Queue.PriorityQueue()
        self._node_dic = {}
        self._sim_time = 0.0

        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()

    def loadInput(self):
        print 'simulator:loadInput'
        #Simulator.queue = Queue.PriorityQueue()

        tp = TopoGenerator('/Users/SunnySky/workspace/cong-simu/input_files/topo_9nodes.txt')
        tp.parseTopoFile(self)

        self._node_dic = tp.getNodeDic()
        tf = TrafficGenerator('input_files/traff.txt')
        tf.parseTrafficFile(self._node_dic, self)


    def enqueue(self, event):
        print 'simu:enqueue'
        self._queue.put((event.timestamp, event,))

    def run(self):
        print 'simu:run'
        # initialize network

        # run
        print 'evt q len: %d' % (self._queue.qsize())
        while not self._queue.empty():
            
            ev = self._queue.get()[1] # get() returns a tuple
            ev.execute()
            self._sim_time = ev.timestamp

    def time():
        return self.time

    def advanceTimeTo(self, newtime):
        if newtime <= self._sim_time:
            print 'error'
        self._sim_time = newtime

if __name__ == '__main__':
    sim = Simulator()
    sim.loadInput()
    sim.run()
    print 'succeeded'
