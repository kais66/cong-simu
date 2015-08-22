import cong_plot
import numpy as np
import process_trace
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from scipy.stats import norm
import sys
from cong_plot import ThroughputByFlowData
from .. import queue_manager


class ResponseTimeByFlowPlot(object):
    def __init__(self, rate_str, topo_str):
        self.rate_str = rate_str
        self.topo_str = topo_str
        #self.rates = cong_plot.rates_dic[topo_traff_str]
        #self.exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        self.exp_list = ['PerFlow', 'PerIfWithECN']

    def plotHist(self):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        for exp in self.exp_list:
            file_path = '{}respTimes_{}_{}.csv'.format(cong_plot.trace_base_path,
                                                           exp, self.rate_str)
            thru_data = ThroughputByFlowData(file_path)
            flow_resp = thru_data.avgFlowRespTime()
            num_flow = len(flow_resp)

            # to normalize
            #ax.hist(flow_resp, bins=100, histtype='stepfilled', normed=True, alpha=0.5, label=exp)
            ax.hist(flow_resp, bins=100, histtype='stepfilled', alpha=0.5, label=exp)

            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: round(x/(num_flow * 1.0), 4)))

        cong_plot.labelPlot('Response time (ms)', 'Probability', '', 'upper right')
        plt.show()

    def plotCDF(self):
        for exp in self.exp_list:
            file_path = '{}respTimes_{}_{}.csv'.format(cong_plot.trace_base_path,
                                                           exp, self.rate_str)
            thru_data = ThroughputByFlowData(file_path)
            flow_thru = thru_data.avgFlowRespTime()
            print flow_thru

            cumu_prob = np.arange(len(flow_thru)) / float(len(flow_thru))
            plt.plot(flow_thru, cumu_prob, marker=cong_plot.
                     marker_iter.next(), linewidth=2, label=exp)
        cong_plot.labelPlot('Response time (ms)', 'Cumulative Probability', '', 'lower right')
        #plt.axis([0, 20, 0, 1])
        plt.show()

if __name__ == "__main__":
    rate_str = sys.argv[1]
    topo_str = 'Abilene'
    #topo_str = 'Small9'
    p = ResponseTimeByFlowPlot(rate_str, topo_str)
    #p.plotHist()
    p.plotCDF()