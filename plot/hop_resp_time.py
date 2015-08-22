import cong_plot
import numpy as np
import process_trace
import matplotlib.pyplot as plt
import sys

rate_list = ["0.5", "0.7", "0.9", "1.1", "1.3", "1.5", "1.7", "2.0"]

class ResponseTimeByHopCountPlot(object):
    def __init__(self, rate_str, topo_str):
        self.rate_str = rate_str
        self.topo_str = topo_str
        #self.rates = cong_plot.rates_dic[topo_traff_str]
        self.exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        self.plot()

    def plot(self):
        # plotting with two y-axis
        # http://matplotlib.org/examples/api/two_scales.html

        #ax = plt.axes()
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        plt.hold(True)

        num_exp = len(self.exp_list)

        all_data = {} # exp_str : [[resp_times]]
        max_hop_count = 0
        for exp in self.exp_list:
            file_path = '{}respTimes_{}_{}.csv'.format(cong_plot.trace_base_path,
                                                           exp, self.rate_str)
            thru_data = cong_plot.ThroughputData(file_path)
            resp_times = thru_data.respTimeByHopCount(self.topo_str)
            max_hop_count = max(max_hop_count, len(resp_times))
            all_data[exp] = resp_times

        for hop_count_pos in xrange(max_hop_count):

            time_data = []
            num_flow = []
            for exp_pos in xrange(num_exp):
                exp = self.exp_list[exp_pos]

                # this should be the way to build a numpy array row by row
                # because each concatenation in numpy is a copy
                # not like what's in python list.
                this_time_data = all_data[exp][hop_count_pos]

                print 'exp: {}, length of data: {}'.format(
                    exp, this_time_data.shape[0])
                time_data.append(this_time_data)
                num_flow.append(len(this_time_data))

            #plt.boxplot(time_data, positions=[2+ hop_count_pos*4+i for i in xrange(num_exp)])
            bp = ax1.boxplot(time_data, positions=[2+ hop_count_pos*4+i for i in
                                                   xrange(num_exp)],
                             patch_artist=True)
            cong_plot.setBoxColor(bp, num_exp)
            ax2.plot([2+ hop_count_pos*4+i for i in xrange(num_exp)], num_flow, 'g*', markersize=10)

        ax1.set_xticklabels([str(entry+1) for entry in xrange(max_hop_count)])
        ax1.set_xticks([3 + i*4 for i in xrange(max_hop_count)])
        ax1.set_ylabel('Resp. time (ms)', color='b')
        ax2.set_ylabel('# completed flows', color='g')
        ax1.set_xlabel('Hop count')

        lines = []
        for exp_pos in xrange(len(self.exp_list)):
            lines.append(plt.plot([0,0], '-', linewidth=2, color=
            cong_plot.color_list[exp_pos])[0])
        plt.legend(tuple(lines), tuple(self.exp_list))
        # 1 unit white space on the left and right edge
        # and 1 unit white space in-between two rates
        plt.xlim(0, 4*max_hop_count +2 )
        #cong_plot.labelPlot('Hop count', 'Response time (ms)','')

        #plt.show()
        file_format = 'png'
        save_path = 'cong-simu/plot/byHopRespTime.{}'.format(
            file_format)
        plt.savefig(save_path)

if __name__ == "__main__":
    rate_str = sys.argv[1]
    topo_str = 'Abilene'
    #topo_str = 'Small9'
    plt = ResponseTimeByHopCountPlot(rate_str, topo_str)

