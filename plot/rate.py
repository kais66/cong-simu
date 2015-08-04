import sys
from cong_plot import *

#rate_list = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "1.7", "2.0"]
class AllDstList(object):
    def __init__(self):
        self.src_list = [3]
        self.dst_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]

class AllSrcList(object):
    def __init__(self):
        self.src_list = [1, 2, 3, 5, 8, 9]
        self.dst_list = [6]

class Small9List(object):
    def __init__(self):
        self.src_list = [1, 2]
        self.dst_list = [6, 7, 8, 9]
if __name__ == "__main__":
    sd_list = AllDstList()
    src_list = sd_list.src_list
    dst_list = sd_list.dst_list

    #rate_set = set(rate_list)
    num_arg = len(sys.argv)
    rate_str = sys.argv[1]
    #if num_arg != 2 or rate_str not in rate_set:
    #    print 'error in arguments'

    plt = PerIfRatePlot(rate_str, src_list, dst_list)
