# python lib
import Queue

# my own modules
from topo import *


class Simulator(object):
    shared_state = {}
    queue = Queue.PriorityQueue()
    node_dic = {}
    sim_time = 0.0
    #def __new__(cls, *args, **kwargs):
    #    if not cls._singleton:
    #        cls._singleton = super(Simulator, cls).__new__(cls, *args, **kwargs)
            #cls._singleton.queue = None
    #    return cls._singleton

    def __init__(self):
        #self.__dict___ = Simulator.shared_state
        #self.queue = Queue.PriorityQueue()
        pass

    def loadInput(self):
        print 'simulator:loadInput'
        #Simulator.queue = Queue.PriorityQueue()

        tp = TopoGenerator('/Users/SunnySky/workspace/cong-simu/input_files/topo_9nodes.txt')
        tp.parseTopoFile()

        Simulator.node_dic = tp.getNodeDic()
        tf = TrafficGenerator('input_files/traff.txt')
        tf.parseTrafficFile(self.node_dic)


    def enqueue(self, event):
        print 'simu:enqueue'
        Simulator.queue.put((event.timestamp, event,))

    def run(self):
        print 'simu:run'
        # initialize network

        # run
        while not Simulator.queue.empty():
            ev = self.queue.get()[0] # get() returns a tuple
            ev.execute()
            Simulator.sim_time = ev.timestamp

    def time():
        return Simulator.time

    def advanceTimeTo(self, newtime):
        if newtime <= self.time:
            print 'error'
        self.time = newtime

if __name__ == '__main__':
    sim = Simulator()
    sim.loadInput()
    sim.run()
    print 'succeeded'
