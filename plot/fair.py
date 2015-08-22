import cong_plot
import numpy as np
import process_trace
import matplotlib.pyplot as plt
from scipy.stats import norm
import sys
from cong_plot import ThroughputByFlowData
from .. import queue_manager

rate_list = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "1.7", "2.0"]

class FairnessPlot(object):
    def __init__(self, topo_str, traff_str):
        self.traff_str = traff_str
        self.topo_str = topo_str
        self.topo_traff_str = self.topo_str + self.traff_str
        self.rates = cong_plot.rates_dic[self.topo_traff_str]
        self.rate_values = [float(entry) for entry in self.rates]

        #self.rates = cong_plot.rates_dic[topo_traff_str]
        self.exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        #self.exp_list = ['PerIf']

    def plotJain(self):
        # plot jain's fairness index, across different rates
        # http://people.duke.edu/~ccc14/pcfb/numpympl/MatplotlibBarPlots.html

        fig = plt.figure()
        ax = fig.add_subplot(111)

        # get the hop count first
        hop_file = '{}{}.hop'.format(cong_plot.trace_topo_path, self.topo_str)
        hop_count = {}
        with open(hop_file, 'r') as f:
            for row in f:
                words = row.split(',')
                flow = queue_manager.Flow(words[0], words[1])
                hop_count[flow.hashKey()] = int(words[2])

        num_rates = len(self.rates)
        xpos = np.arange(num_rates)
        width = 0.25

        fair_ind = {} # { exp : [] }
        for exp_pos in xrange(len(self.exp_list)):
            exp = self.exp_list[exp_pos]
            jain_list = []
            for rate_pos in xrange(num_rates):
                rate = self.rates[rate_pos]
                file_path = '{}respTimes_{}_{}.csv'.format(cong_plot.trace_base_path,
                                                               exp, rate)
                thru_data = ThroughputByFlowData(file_path)
                flow_thru = thru_data.hopWeightedAvgThru(hop_count)
                #flow_thru = thru_data.avgFlowThruData()

                jain_list.append(self.computeJainIndex(flow_thru))
            #fair_ind[exp] = jain_list
            ax.bar(xpos+exp_pos*width, jain_list, width, color=cong_plot.color_iter.next(), label=exp)

        cong_plot.labelPlot('Offered load for each (src, dst) pair', 'Jain\'s index', '', 'lower left')
        x_tick_marks = self.rates
        ax.set_xticks(xpos + width)
        ax.set_xticklabels(x_tick_marks)
        #plt.axis([0, 20, 0, 1])
        plt.show()

    def computeJainIndex(self, flow_thru_list):
        dividend = sum(flow_thru_list) ** 2
        divisor = len(flow_thru_list) * sum([thru ** 2 for thru in flow_thru_list])
        return (dividend / divisor)

if __name__ == "__main__":
    topo_str = 'Abilene'
    traff_str = 'Equal'

    #topo_str = 'Small9'
    p = FairnessPlot(topo_str, traff_str)
    p.plotJain()