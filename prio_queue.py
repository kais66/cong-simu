import sys

class HeapElement(object):
    def __init__(self, key, app_object):
        self._key = key
        self._app_object = app_object
        self._heap_pos = -1

    def setKey(self, key):
        self._key = key

    def key(self):
        return self._key

    def appObject(self):
        return self._app_object

    def setHeapPos(self, pos):
        self._heap_pos = pos

    def heapPos(self):
        return self._heap_pos

    def appObject(self):
        return self._app_object

###############################################################################
# Heap functions 
###############################################################################

def parent(childPos):
    return (childPos-1)//2

def left(parentPos):
    ''' return position of left child of position i '''
    return parentPos*2 + 1

def right (parentPos):
    return parentPos*2 + 2

def siftdown(h, start, end):
    ''' h is essentially a python list, which tries to maintain the heap property:
        min heap: h[parent[i]] <= h[i]. 
        This considers the heap to be min-heap. '''
    ind = start 
    while left(ind) <= end:
        minind = left(ind) # tentative
        # need to replace the parent with child with min value
        if minind+1 <= end and h[minind] > h[minind+1]: minind += 1
        if h[ind].key() > h[minind].key():
            h[ind], h[minind] = h[minind], h[ind]
            h[ind].setHeapPos(ind)
            h[minind].setHeapPos(minind)
            ind = minind
        else:
            return 

def siftup(h, ind):
    ''' move an element up, if it's parent violates heap property with it. Unlike siftdown, no need to worry about
        the sibling, as it's guaranteed to be no less than the original parent. ''' 
    while parent(ind) >= 0:
        prind = parent(ind)
        if h[ind].key() < h[prind].key():
            h[ind], h[prind] = h[prind], h[ind]
            h[ind].setHeapPos(ind)
            h[prind].setHeapPos(prind)
            ind = prind 
        else:
            return
        
def heapify(h):
    for i in reversed(xrange(len(h)//2)):
        siftdown(h, i, len(h)-1)

def heapsort(h):
    heapify(h)
    for i in reversed(xrange(len(h)-1)):
        h[0], h[i+1] = h[i+1], h[0]
        siftdown(h, 0, i)
    # min-heap will produce reversed sorted order
    h.reverse()

def heappush(h, heapElement):
    h.append(heapElement)
    heapElement.setHeapPos(len(h)-1)
    siftup(h, len(h)-1) 

def heappop(h):
    endPos = len(h)-1
    h[0], h[endPos] = h[endPos], h[0]
    h[0].setHeapPos(0)
    h[endPos].setHeapPos(endPos)
    siftdown(h, 0, len(h)-2) 
    return h.pop()

def changeKey(h, heapElement, newKey):
    # locate the heapElement in heap
    oldPos = heapElement.heapPos()
    endPos = len(h)-1
    h[oldPos], h[endPos] = h[endPos], h[oldPos]
    h[oldPos].setHeapPos(oldPos)
    h[endPos].setHeapPos(endPos)

    # now similar to heappop(), pretending endPos element has gone, do siftdown()
    siftdown(h, oldPos, endPos-1)

    # now heap[0..endPos-1] satisfies heap property; similar to heappush(), need
    # to siftup the element whose key changed.
    h[endPos].setKey(newKey)
    siftup(h, endPos)


###############################################################################
# Priority Queue class, which is built on the heap functions above 
###############################################################################
class PrioQueue(object):
    ''' min-heap based proirity queue '''
    def __init__(self):
        self.heap = []

    def put(self, element):
        ''' element is a HeapElement object. '''
        heappush(self.heap, element)

    def get(self):
        return heappop(self.heap)

    def peek(self):
        return self.heap[0]

    def changeKey(self, oldElement, newKey):
        ''' increase or decrease the key of a priority queue element '''
        changeKey(self.heap, oldElement, newKey)

    def printQueue(self):
        keyArray = [heapElement.key() for heapElement in self.heap]
        print 'Heap looks like: '
        print keyArray

        #print 'sorted array looks like: '
        #print heapsort(keyArray)

def test():
    h = [13, 14, 94, 33, 82, 25, 59, 65, 23, 45, 27, 73] 
    queue = PrioQueue()
    elementArray = [HeapElement(i, None) for i in h]
    for i in xrange(len(h)): 
        ele = elementArray[i]
        queue.put(ele)

    queue.printQueue()
    queue.changeKey(elementArray[0], 15)
    queue.printQueue()

