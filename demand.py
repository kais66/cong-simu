###############################################################################
# This file generate chunk arrival trace file for the simulator.
# row format for the generated input file:
# src, dst, chk_size, arrival_time, start_offset, end_offset, file_size, chk_id
###############################################################################

import random
import sys
import math
import numpy as np
from scipy.stats import pareto
import unit_conv

class ArrivalTrace(object):
    start_t = 0.0

    def __init__(self, topo_str, traff_str, rate_mbyteps_str):
        '''
        rate: per (src, dst) base rate in MB/s
        '''
        self.rate_str = rate_mbyteps_str
        self.traff_str = traff_str

        self.rate_mbyteps = float(rate_mbyteps_str)
        self.rate_bytepms = unit_conv.convertMbytepsecToBytepmsec(self.rate_mbyteps)

        self.start_msec = 0.0
        self.end_msec = 100000.0

        # 50KB, value taken from "FlowCompletionTime" paper
        # make sure the mean file size is a multiple of 1000B
        self.mean_file_size = 50000

        # if a file of size greater than the chunk size, it will be segmented
        #self.max_chk_size_bytes = 1048576

        self.max_chk_size_bytes = 50000 # 50KB chunk

        # change to a different Demand object to use another traffic demand profile
        demand_initializer = None

        self.topo_str = topo_str
        demand_init_str = topo_str + traff_str
        if demand_init_str == 'Small9Equal':
            demand_initializer = DemandSmallEqual(self.rate_bytepms)
            #self.topo_str = 'Small9Equal'
        elif demand_init_str == 'Small9Skewed':
            demand_initializer = DemandSmallSkewed(self.rate_bytepms)
            #self.topo_str = 'Small9Skewed'
        elif demand_init_str == 'Small9AllPairEqual':
            demand_initializer = DemandEqual(self.topo_str, self.rate_bytepms)
        elif demand_init_str == 'AbileneEqual':
            demand_initializer = DemandEqual(self.topo_str, self.rate_bytepms)
            #self.topo_str = 'AbileneEqual'
        else:
            print 'error in argument'
            sys.exit()

        self.demand_init_str = demand_init_str
        self.demand_list = demand_initializer.demandList()

        # list of file arrivals
        self.arrival_list = []
        # final output is this list, its row format is
        # src, dst, chk_size_bytes, arrival_time, chk_id, start_offset,
        # end_offset, file_id
        self.chk_arrival_list = []


    def generate(self):
        random.seed()

        for line in self.demand_list:
            inter_arrival_time_func = NextExponentialInterArrival
            #file_size_func = NextParetoSize
            #inter_arrival_time_func = NextDeterministicInterArrival
            file_size_func = NextDeterministicSize

            this_arr_list = self.genOneSrcDst(line, inter_arrival_time_func, file_size_func)
            self.arrival_list.extend(this_arr_list)

        self.arrival_list.sort(key=lambda x: x[2])

        chk_id = 1

        for row in self.arrival_list:
            src, dst, arrival_time, file_size = row[0], row[1], row[2], row[3]
            remain_file_size = file_size

            start_chk_id = chk_id
            # this chunk's offset with the first and last chunk of this file
            # invariant: start_offset + end_offset + 1 = num_chks_in_file
            #start_offset = 0

            # calculate num_chks
            num_chks = remain_file_size // self.max_chk_size_bytes
            if remain_file_size % self.max_chk_size_bytes != 0:
                num_chks += 1
            end_chk_id = start_chk_id + num_chks - 1

            while remain_file_size > 0:
                # insert a new entry for a chunk
                chk_size = min(remain_file_size, self.max_chk_size_bytes)

                start_offset = chk_id - start_chk_id
                end_offset = end_chk_id - chk_id
                assert start_offset >= 0 and end_offset >= 0
                chk_arrival_row = [src, dst, chk_size, arrival_time,
                    start_offset, end_offset, file_size, chk_id]

                self.chk_arrival_list.append(chk_arrival_row)

                chk_id += 1
                remain_file_size -= chk_size
            
        self.write()

    def genOneSrcDst(self, demand_row, inter_arrival_func, file_size_func):
        '''
        given a demand_row, i.e. src, dst, demanded_rate, and functions for
        getting file size and inter arrival times, generate a list of rows,
        where each row is corresponding to one file arrival.
        '''
        print demand_row
        src, dst, demanded_bytepmsec = demand_row[0], demand_row[1], demand_row[2]
        mean_arrival_rate = float(demanded_bytepmsec) / self.mean_file_size

        arrival_list = []
        cur_time = self.start_msec

        random.seed()
        np.random.seed()

        while cur_time < self.end_msec:
            file_size = file_size_func(self.mean_file_size)
            arrival_list.append([src, dst, cur_time, file_size])

            cur_time += inter_arrival_func(mean_arrival_rate)

        return arrival_list

    def write(self):
        #fname = 'input_files/traff_poisson_' + str(self.rate_mbyteps) + '.txt'
        fname = 'input_files/{}/{}_{}.traff'.format(self.topo_str,
                self.traff_str, self.rate_str)
        with open(fname, 'w') as f:
            for line in self.chk_arrival_list:
                f.write(','.join([str(x) for x in line]) + '\n')

###############################################################################
# Demand classes: provide per (src, dst) traffic demand list, in terms of rate.
###############################################################################
class BaseDemand(object):
    def __init__(self, rate_str=None):
        self.demand_list = []

    def demandList(self):
        return self.demand_list

    def offeredLoad(self):
        '''
        return the overrall offered load
        '''
        pass

class DemandSmallEqual(BaseDemand):
    '''
    This new implementation assumes rate is the rate for every (src, dst) pair.
    '''
    def __init__(self, rate=None):
        '''
        :param rate: rate in bytes/ms
        :return:
        '''
        self.demand_list = []
        self.src_list = [1, 2]
        self.dst_list = [6, 7, 8, 9]

        if rate is not None:
            self.writeDemandList(rate)

        #self.rate = rate

    def writeDemandList(self, rate):
        assert rate is not None
        for src in self.src_list:
            for dst in self.dst_list:
                self.demand_list.append([src, dst, rate])

    def offeredLoad(self, rate):
        return float(len(self.src_list)) * len(self.dst_list) * rate


class DemandSmallSkewed(BaseDemand):
    def __init__(self, rate=None):
        self.demand_list = []
        self.src_list = [1, 2]
        self.dst_list = [6, 7, 8, 9]

        if rate is not None:
            self.writeDemandList(rate)

        #self.rate = rate

    def writeDemandList(self, rate):
        assert rate is not None
        for src in self.src_list:
            for dst in self.dst_list:
                actual_rate = rate * 3 if dst == 9 else rate
                self.demand_list.append([src, dst, actual_rate])

    def offeredLoad(self, rate):
        nSrc, nDst = len(self.src_list), len(self.dst_list)
        return float(nSrc) * (nDst-1) * rate + float(nSrc) * 1 * 3 * rate


class DemandEqual(BaseDemand):
    def __init__(self, topo_str, rate=None):
        '''
        generate per (src, dst) rate demand. For any raw Rocketfuel AS topo.
        Traffic demands are equal. Assume each node Tx to all the other nodes.
        '''
        self.demand_list = []
        self.src_list = []
        self.dst_list = []
        self.topo_str = topo_str

        self.initSrcDst()

        if rate is not None:
            self.writeDemandList(rate)

    def initSrcDst(self):
        topo_file_path = 'topo_files/{}.topo'.format(self.topo_str)
        with open(topo_file_path, 'r') as f:
            for line in f:
                words = line.split(',')
                self.src_list.append(int(words[0]))

        print self.src_list

        self.dst_list = self.src_list[:]

        #sys.exit()

    def writeDemandList(self, rate):
        assert rate is not None
        for src in self.src_list:
            for dst in self.dst_list:
                if src != dst:
                    self.demand_list.append([src, dst, rate])

    def offeredLoad(self, rate):
        return float(len(self.src_list)) * len(self.dst_list) * rate


###############################################################################
# A few functions to return a value according to certain distribution
###############################################################################
def NextExponentialInterArrival(mean_arr_rate):
    '''
    :param mean_arr_rate: number of arrivals per milli sec
    :return: inter-arrival time in milli seconds.
    '''
    return float(random.expovariate(mean_arr_rate))

def NextDeterministicInterArrival(mean_arr_rate):
    return 1/float(mean_arr_rate)

def NextParetoSize(mean):
    # https://docs.scipy.org/doc/scipy-0.7.x/reference/generated/scipy.stats.pareto.html
    alpha = 1.20
    sigma = (alpha - 1) * mean / alpha
    size = int(math.ceil(pareto.rvs(alpha, loc=0, scale=sigma)))
    if size == 0:
        return 1
    return size

def NextDeterministicSize(mean):
    return mean


