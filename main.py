# python lib
import Queue

# my own modules
import node

class Simulator:
    def __init__(self):
        self.queue = Queue.PriorityQueue()
        pass
    def run(self):
        pass

if __name__ == '__main__':
    sim = Simulator()
    n = node.Node()
    print 'succeeded'
