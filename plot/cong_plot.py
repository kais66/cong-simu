import numpy as np
import matplotlib.pyplot as plt
import process_trace
from .. import demand
from matplotlib.lines import Line2D
# to generate an iterator for line markers
import itertools

# this rate list should be kept in sync with the one in the shell scripts
#rates = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "2.0", "3.0"]

# rates for small skewed traffic
rates_dic = {
    #'small_skewed':["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "1.7", "2.0"],
    'Small9Skewed':["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "2.0"],
    'Small9Equal':["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "2.0"],
    'Small9AllPairEqual':["0.5", "0.7", "0.9", "1.1", "1.3", "1.5"],
    'AbileneEqual':["0.05", "0.35", "0.45", "0.55", "0.65"]
}


#
traff_demand = demand.DemandSmallSkewed()
#offered = {rate : str(traff_demand.offeredLoad(float(rate))) for rate in rates}

trace_base_path = '/Users/SunnySky/workspace/cong-simu/output/'

class ThroughputPlot(object):
    def __init__(self, topo_traff_str):
        self.rates = rates_dic[topo_traff_str]
        self.rate_values = [float(entry) for entry in self.rates]

        exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        #exp_list = ['PerFlow', 'PerIfWithECN' ]

        #traff_demand = demand.DemandSmallEqual()

        traff_demand = demand.DemandSmallSkewed()
        self.plot(exp_list, traff_demand)

    def plot(self, experiment_list, traffic_demand):
        '''
        :param experiment_list: a list of experiment strings, such as PerIf,
        PerFlow, PerIfWithECN
        :param traffic_demand: an object of demand.BaseDemand class,
        used to get offered load
        :return:
        '''
        offered = np.array([traffic_demand.offeredLoad(rate) for rate in self.rate_values])

        # each row is the throughput list for a single experiment, where each
        # entry is for a particular rate
        thru = np.zeros((len(experiment_list), len(self.rate_values)))
        for exp_pos in xrange(len(experiment_list)):
            exp = experiment_list[exp_pos]
            for rate_pos in xrange(len(self.rates)):
                rate = self.rates[rate_pos]

                file_path = '{}respTimes_{}_{}.csv'.format(trace_base_path, exp, rate)
                print file_path
                thru_data = ThroughputData(file_path)
                thru[exp_pos][rate_pos] = thru_data.overallThroughput()
                print 'value at pos ({}, {}) is: {}'.format(exp_pos, rate_pos,
                                                        thru[exp_pos][rate_pos])

        # now plot
        for exp_pos in xrange(len(experiment_list)):
            plt.plot(offered, thru[exp_pos], '-D', linewidth=4, label=experiment_list[exp_pos])

        labelPlot('Offered load (MB/s)', 'Throughput (MB/s)', '', 'upper left')
        #plt.axis([0, 16, 0, 14])
        #plt.show()
        plt.savefig('cong-simu/plot/offered')

class DstThroughputPlot(object):
    def __init__(self, rate_str, dst_list):
        self.rate_str = rate_str
        self.dst_list = dst_list
        #self.exp_list = ['PerFlow', 'PerIfWithECN' ]
        self.exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        self.plot()

    def plot(self):
        thru = np.zeros((len(self.exp_list), len(self.dst_list)))
        for exp_pos in xrange(len(self.exp_list)):
            exp = self.exp_list[exp_pos]
            file_path = '{}respTimes_{}_{}.csv'.format(trace_base_path,
                                                       exp, self.rate_str)
            thru_data = ThroughputData(file_path)
            for dst_pos in xrange(len(self.dst_list)):
                dst = self.dst_list[dst_pos]
                dst_thru = thru_data.dstThroughput(dst)
                thru[exp_pos][dst_pos] = dst_thru
                print 'value at pos ({}, {}) is: {}'.format(exp_pos, dst_pos,
                                                        thru[exp_pos][dst_pos])

        # http://matplotlib.org/examples/pylab_examples/barchart_demo.html
        n_groups = len(self.dst_list)
        fig, ax = plt.subplots()

        index = np.arange(n_groups)
        bar_width = 0.26

        opacity = 0.4
        error_config = {'ecolor': '0.3'}

        for exp_pos in xrange(len(self.exp_list)):
            num_shift = exp_pos
            plt.bar(index + num_shift*bar_width, thru[exp_pos], bar_width,
                         alpha=opacity,
                         color=color_iter.next(),
                         edgecolor='k',
                         linewidth=3,
                         error_kw=error_config,
                         label=self.exp_list[exp_pos])

        # rects2 = plt.bar(index + bar_width, thru[1], bar_width,
        #                  alpha=opacity,
        #                  color='r',
        #                  error_kw=error_config,
        #                  label='PerIfWithECN')



        legend_str = ['dst: '+ str(dst) for dst in self.dst_list]
        plt.xticks(index + bar_width, legend_str)
        offered_load = offered[self.rate_str]

        labelPlot('', 'Throughput (MB/s)', 'Offered load ' + offered_load)
        #plt.tight_layout()
        #plt.show()


        file_format = 'png'
        save_path = 'cong-simu/plot/figure/perDstThru_{}.{}'.format(
            offered_load, file_format)
        plt.savefig(save_path)

class TraffInputPlot(object):
    '''
    used to visualize the actual offered load generated,
    from the traff input files.
    '''
    def __init__(self, rate_str, dst_list):
        self.rate_str = rate_str
        self.dst_list = dst_list
        self.plot()

    def plot(self):

        file_path = '{}{}.txt'.format(
                '/Users/SunnySky/workspace/cong-simu/input_files/traff_poisson_',
                self.rate_str)


        index = { 'ENDTS_POS':3, 'DST_POS':1, 'CHKSIZE_POS':2}
        thru_data = ThroughputData(file_path, index)
        thru = np.zeros((1, len(self.dst_list)))
        for dst_pos in xrange(len(self.dst_list)):
            dst = self.dst_list[dst_pos]
            dst_thru = thru_data.dstThroughput(dst)
            thru[0][dst_pos] = dst_thru
            print 'value at pos ({}) is: {}'.format(dst_pos,
                                                    thru[0][dst_pos])

        n_groups = len(self.dst_list)
        fig, ax = plt.subplots()

        index = np.arange(n_groups)
        bar_width = 0.35

        opacity = 0.4
        error_config = {'ecolor': '0.3'}
        rects1 = plt.bar(index, thru[0], bar_width,
                 alpha=opacity,
                 color='b',
                 error_kw=error_config,
                 label='PerFlow')
        legend_str = ['dst: '+ str(dst) for dst in self.dst_list]
        plt.xticks(index + bar_width, legend_str)
        labelPlot('', 'Throughput (MB/s)', 'Per dst. offered load')
        #plt.tight_layout()
        plt.show()

class PerIfRatePlot(object):
    def __init__(self, rate_str, src_list, dst_list):
        self.rate_str = rate_str
        self.src_list, self.dst_list = src_list, dst_list
        self.plot()

    def plot(self):
        file_path = '{}rate_{}.csv'.format(trace_base_path, self.rate_str)

        rate_data = PerIfRateData(file_path)
        for src in self.src_list:
            for dst in self.dst_list:
                data = rate_data.srcDstRate(src, dst)
                plt.plot(data[:, 0], data[:, 1], marker=marker_iter.next(),
                         markersize=10,
                         linewidth=2, label=str(src)+'-'+str(dst))
        labelPlot('time (ms)', 'rate', '', 'lower left')
        plt.show()
        #plt.savefig('cong-simu/plot/rate_fig', ext="png", close=True, verbose=True)

class ResponseTimePlot(object):
    '''
    for a single rate, plot boxplot of resp times for each experiment
    '''
    def __init__(self, topo_traff_str):
        self.rates = rates_dic[topo_traff_str]

        self.exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']

        traff_demand = demand.DemandSmallSkewed()
        self.rate_values = [float(entry) for entry in self.rates]
        self.offered = np.array([traff_demand.offeredLoad(rate) for rate in self.rate_values])

        self.plot()

    #http://stackoverflow.com/questions/16592222/matplotlib-group-boxplots
    def plot(self):
        ax = plt.axes()
        #fig = plt.figure()
        plt.hold(True)
        whisker = [5, 95] # let whiskers show 5th and 95th percentile

        num_rates, num_exp = len(self.rates), len(self.exp_list)

        for rate_pos in xrange(num_rates):
            rate = self.rates[rate_pos]
            time_data = []
            for exp_pos in xrange(num_exp):
                exp = self.exp_list[exp_pos]
                file_path = '{}respTimes_{}_{}.csv'.format(trace_base_path,
                                                           exp, rate)
                thru_data = ThroughputData(file_path)

                # this should be the way to build a numpy array row by row
                # because each concatenation in numpy is a copy
                # not like what's in python list.
                this_time_data = thru_data.allCompletionTime()#.tolist()
                print 'exp: {}, length of data: {}'.format(
                    exp, this_time_data.shape[0])
                time_data.append(this_time_data)


            plt.boxplot(time_data, positions=[2+ rate_pos*4+i for i in xrange(num_exp)])
                        #widths=0.6)

            #plt.boxplot(time_data, labels=(exp,))
        #np_data = np.array(time_data)
        #print np.shape(np_data)


        #plt.boxplot(time_data, whis=whisker, labels=self.exp_list)
        #plt.boxplot(time_data, sym=None, labels=self.exp_list)

        ax.set_xticklabels([str(entry) for entry in self.offered])
        ax.set_xticks([3 + i*4 for i in xrange(len(self.rates))])

        # 1 unit white space on the left and right edge
        # and 1 unit white space in-between two rates
        plt.xlim(0, 4*len(self.rates) +2 )
        labelPlot('offered load (MB/s)', 'Response time (ms)','')

        #plt.show()
        file_format = 'png'
        save_path = 'cong-simu/plot/respTime.{}'.format(
            file_format)
        plt.savefig(save_path)

###############################################################################
# Class for actually getting the data
###############################################################################

class ThroughputData(object):
    '''
    This class provides a handle to all the data columns from respTime.csv
    '''
    SIMU_LENG = 100000.0 # 100s

    def __init__(self, file_path, index=None):
        # based on the positions of entries defined when writing the throughput trace
        self.CHUNKID_POS = 0
        self.STARTTS_POS = 1
        self.ENDTS_POS = 2
        self.DELAY_POS = 3
        self.SRC_POS = 4
        self.DST_POS = 5
        self.FILESIZE_POS = 6
        self.CHKSIZE_POS = 7
        self.FILEID_POS = 8

        if index is not None:
            self.ENDTS_POS = index['ENDTS_POS']
            self.DST_POS = index['DST_POS']
            self.CHKSIZE_POS = index['CHKSIZE_POS']

        self.raw_csv_data = process_trace.readCSVToFloatMatrix(file_path)
        # numpy 2-d array
        all_data_array = np.array(self.raw_csv_data)
        # only retain the flows finished before simu length
        self.array = all_data_array[all_data_array[:, self.ENDTS_POS]
                        <= ThroughputData.SIMU_LENG]

    def overallThroughput(self, np_array=None):
        if np_array is None:
            np_array = self.array
        total_bytes = np.sum(np_array, axis=0)[self.CHKSIZE_POS]
        #total_bytes = np.sum(np_array, axis=0)[ThroughputData.FILESIZE_POS]
        thru_mbyteps = float(total_bytes) / 1048576 / (ThroughputData.SIMU_LENG / 1000)
        return thru_mbyteps

    def dstThroughput(self, dst):
        valid_entries = self.array[self.array[:, self.DST_POS] == dst]
        #if dst==6: print valid_entries.tolist()
        return self.overallThroughput(valid_entries)

    def allCompletionTime(self, np_array=None):
        if np_array is None:
            np_array = self.array

        # because completion time is per file, not per chunk; we need to filter
        # the array so that each file is considered only once
        valid_entries = self.__retainOneChkPerFile(np_array)
        return valid_entries[:, self.DELAY_POS]
        #total_time = np.sum(valid_entries, axis=0)[self.DELAY_POS]

    def __retainOneChkPerFile(self, np_array):
        valid_entries = np_array[np_array[:, self.FILEID_POS] == np_array[:, self.CHUNKID_POS]]
        return valid_entries

    #def respTimeByHopCount(self, raw_csv_data):


class PerIfRateData(object):
    '''
    Src rates over time according to ECN adjustments
    '''
    SIMU_LENG = 100000.0 # 100s

    SRC_POS = 0
    DST_POS = 1
    TIME_POS = 2
    RATE_POS = 3
    def __init__(self, file_path):
        all_data_array = np.array(process_trace.readCSVToFloatMatrix(file_path))
        # only retain the flows finished before simu length
        self.array = all_data_array[all_data_array[:, PerIfRateData.TIME_POS]
                        <= PerIfRateData.SIMU_LENG]

    def srcDstRate(self, src, dst):
        '''
        return a numpy array of two rows: times, rates
        :param src:
        :param dst:
        :return:
        '''

        valid_entries = self.array[
            self.array[:, PerIfRateData.SRC_POS] == src]
        valid_entries = valid_entries[
            valid_entries[:, PerIfRateData.DST_POS] == dst]
        #print valid_entries

        # stacking two column vectors
        ret = np.c_[valid_entries[:, PerIfRateData.TIME_POS],
                        valid_entries[:, PerIfRateData.RATE_POS]]
        #print ret
        return ret

###############################################################################
# Some utility functions for plotting
###############################################################################
def labelPlot(x, y, title, legend_loc=None):
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(title)
    if legend_loc is None: legend_loc = 'lower right'
    legend = plt.legend(loc=legend_loc, shadow=True, fontsize='x-large')
    #legend = plt.legend(shadow=True, fontsize='x-large')

#marker_list = itertools.cycle((',', '+', '.', 'o', '*'))
marker_list = [marker for marker in Line2D.markers if marker != ' ']
marker_iter = itertools.cycle(marker_list)

# http://matplotlib.org/examples/color/named_colors.html
color_list = ['deepskyblue', 'royalblue', 'lawngreen', 'lightcoral', 'orange']
color_iter = iter(color_list)



#if __name__ == "__main__":
#    plt = ThroughputPlot()
