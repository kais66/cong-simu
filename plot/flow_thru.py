import cong_plot
import numpy as np
import process_trace
import matplotlib.pyplot as plt
from scipy.stats import norm
import sys
from cong_plot import ThroughputByFlowData

rate_list = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "1.7", "2.0"]

class FlowThruPlot(object):
    def __init__(self, rate_str, topo_str):
        self.rate_str = rate_str
        self.topo_str = topo_str
        #self.rates = cong_plot.rates_dic[topo_traff_str]
        #self.exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        self.exp_list = ['PerFlow', 'PerIfWithECN']

    def plotCDF(self):
        for exp in self.exp_list:
            file_path = '{}respTimes_{}_{}.csv'.format(cong_plot.trace_base_path,
                                                           exp, self.rate_str)
            thru_data = ThroughputByFlowData(file_path)
            flow_thru = thru_data.avgFlowThruData()
            print flow_thru

            cumu_prob = np.arange(len(flow_thru)) / float(len(flow_thru))
            plt.plot(flow_thru, cumu_prob, marker=cong_plot.
                     marker_iter.next(), linewidth=2, label=exp)
        cong_plot.labelPlot('Throughput (MB/s)', 'Cumulative Probability', '', 'lower right')
        #plt.axis([0, 20, 0, 1])
        plt.show()

    def plotHist(self):
        for exp in self.exp_list:
            file_path = '{}respTimes_{}_{}.csv'.format(cong_plot.trace_base_path,
                                                           exp, self.rate_str)
            thru_data = ThroughputByFlowData(file_path)
            flow_thru = thru_data.avgFlowThruData()
            plt.hist(flow_thru, bins=100, histtype='stepfilled', normed=True, alpha=0.5, label=exp)
        cong_plot.labelPlot('Throughput (MB/s)', 'Probability', '', 'upper right')
        plt.show()



        # #plt.show()
        # file_format = 'png'
        # save_path = 'cong-simu/plot/byHopRespTime.{}'.format(
        #     file_format)
        # plt.savefig(save_path)

if __name__ == "__main__":
    rate_str = sys.argv[1]
    topo_str = 'Abilene'
    #topo_str = 'Small9'
    p = FlowThruPlot(rate_str, topo_str)
    p.plotCDF()
    #p.plotHist()

