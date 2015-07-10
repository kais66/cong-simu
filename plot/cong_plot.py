import numpy as np
import matplotlib.pyplot as plt
import process_trace
from .. import demand

# this rate list should be kept in sync with the one in the shell scripts
#rates = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "2.0", "3.0"]
rates = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "2.0"]
#rates = ['1.0']
trace_base_path = '/Users/SunnySky/workspace/cong-simu/output/'

class ThroughputPlot(object):
    def __init__(self):

        self.rate_values = [float(entry) for entry in rates]

        exp_list = ['PerFlow', 'PerIf']
        traff_demand = demand.DemandSmallEqual()
        self.thruVsOffered(exp_list, traff_demand)

    def thruVsOffered(self, experiment_list, traffic_demand):
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
        plt.show()
        plt.savefig('offered.png')



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

    def __init__(self, file_path):
        # numpy 2-d array
        all_data_array = np.array(process_trace.readCSVToFloatMatrix(file_path))
        # only retain the flows finished before simu length
        self.array = all_data_array[all_data_array[:, ThroughputData.ENDTS_POS]
                        <= ThroughputData.SIMU_LENG]

    def overallThroughput(self, np_array=None):
        if np_array is None:
            np_array = self.array
        total_bytes = np.sum(np_array, axis=0)[ThroughputData.FILESIZE_POS]
        thru_mbyteps = float(total_bytes) / 1048576 / (ThroughputData.SIMU_LENG / 1000)
        return thru_mbyteps

    def dstThroughput(self, dst):
        valid_entries = self.array[self.array[:, ThroughputData.DST_POS] == dst]
        return self.overallThroughput(valid_entries)

###############################################################################
# Some utility functions for plotting
###############################################################################
def labelPlot(x, y, title):
    plt.xlabel(x)
    plt.ylabel(y)
    plt.title(title)
    legend = plt.legend(loc='lower right', shadow=True, fontsize='x-large')
    #legend = plt.legend(shadow=True, fontsize='x-large')

if __name__ == "__main__":
    plt = ThroughputPlot()
