import numpy as np
import matplotlib.pyplot as plt
import process_trace
from .. import demand

# this rate list should be kept in sync with the one in the shell scripts
#rates = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "2.0", "3.0"]

# rates for small skewed traffic
rates = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "1.7"]

trace_base_path = '/Users/SunnySky/workspace/cong-simu/output/'

class ThroughputPlot(object):
    def __init__(self):

        self.rate_values = [float(entry) for entry in rates]

        #exp_list = ['PerFlow', 'PerIf']
        exp_list = ['PerFlow', 'PerIfWithECN' ]

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
            for rate_pos in xrange(len(rates)):
                rate = rates[rate_pos]

                file_path = '{}respTimes_{}_{}.csv'.format(trace_base_path, exp, rate)
                print file_path
                thru_data = ThroughputData(file_path)
                thru[exp_pos][rate_pos] = thru_data.overallThroughput()
                print 'value at pos ({}, {}) is: {}'.format(exp_pos, rate_pos,
                                                        thru[exp_pos][rate_pos])

        # now plot
        for exp_pos in xrange(len(experiment_list)):
            plt.plot(offered, thru[exp_pos], '-D', linewidth=4, label=experiment_list[exp_pos])
        #plt.plot(offered, thru[0], '-1', linewidth=4)
        labelPlot('Offered load (MB/s)', 'Throughput (MB/s)', '')
        #plt.axis([0, 16, 0, 14])
        plt.show()
        plt.savefig('offered.png')

class DstThroughputPlot(object):
    def __init__(self, rate_str, dst_list):
        self.rate_str = rate_str
        self.dst_list = dst_list
        self.exp_list = ['PerFlow', 'PerIfWithECN' ]
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
        bar_width = 0.35

        opacity = 0.4
        error_config = {'ecolor': '0.3'}

        rects1 = plt.bar(index, thru[0], bar_width,
                         alpha=opacity,
                         color='b',
                         error_kw=error_config,
                         label='PerFlow')

        rects2 = plt.bar(index + bar_width, thru[1], bar_width,
                         alpha=opacity,
                         color='r',
                         error_kw=error_config,
                         label='PerIfWithECN')



        legend_str = ['dst: '+ str(dst) for dst in self.dst_list]
        plt.xticks(index + bar_width, legend_str)
        labelPlot('', 'Throughput (MB/s)', 'Per dst. throughput')
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
                plt.plot(data[:, 0], data[:, 1], linewidth=4, label=str(src)+'-'+str(dst))
        labelPlot('time (ms)', 'rate', '')
        plt.show()


###############################################################################
# Class for actually getting the data
###############################################################################

class ThroughputData(object):
    SIMU_LENG = 100000.0 # 100s

    # based on the positions of entries defined when writing the throughput trace
    FILEID_POS = 0
    STARTTS_POS = 1
    ENDTS_POS = 2
    DELAY_POS = 3
    SRC_POS = 4
    DST_POS = 5
    FILESIZE_POS = 6
    CHKSIZE_POS = 7

    def __init__(self, file_path):
        # numpy 2-d array
        all_data_array = np.array(process_trace.readCSVToFloatMatrix(file_path))
        # only retain the flows finished before simu length
        self.array = all_data_array[all_data_array[:, ThroughputData.ENDTS_POS]
                        <= ThroughputData.SIMU_LENG]

    def overallThroughput(self, np_array=None):
        if np_array is None:
            np_array = self.array
        total_bytes = np.sum(np_array, axis=0)[ThroughputData.CHKSIZE_POS]
        #total_bytes = np.sum(np_array, axis=0)[ThroughputData.FILESIZE_POS]
        thru_mbyteps = float(total_bytes) / 1048576 / (ThroughputData.SIMU_LENG / 1000)
        return thru_mbyteps

    def dstThroughput(self, dst):
        valid_entries = self.array[self.array[:, ThroughputData.DST_POS] == dst]
        return self.overallThroughput(valid_entries)

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
        #ret = np.hstack((valid_entries[:, PerIfRateData.SRC_POS],
        #                valid_entries[:, PerIfRateData.DST_POS]))
        #ret = ret.transpose()
        print ret
        return ret

###############################################################################
# Some utility functions for plotting
###############################################################################
def labelPlot(x, y, title):
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(title)
    legend = plt.legend(loc='lower right', shadow=True, fontsize='x-large')
    #legend = plt.legend(shadow=True, fontsize='x-large')

#if __name__ == "__main__":
#    plt = ThroughputPlot()
