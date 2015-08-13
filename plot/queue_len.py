import cong_plot
import numpy as np
import process_trace
import matplotlib.pyplot as plt
import sys

class QueueIdentifier(object):
    def __init__(self, node_id, buf_man_id):
        # input is the node id given by the topology plot (so index starts from 0)
        self.node_id, self.buf_man_id = node_id+1, buf_man_id+1

class QueueLenPlot(object):
    '''
    Plot len of queue of (node_id, buf_man_id), for a subset of experiments.
    '''
    def __init__(self, rate_str, node_id, buf_man_id):
        self.rate_str = rate_str
        self.node_id, self.buf_man_id = node_id, buf_man_id

        #exp_list = ['PerFlow', 'PerIf', 'PerIfWithECN']
        exp_list = ['PerIf', 'PerIfWithECN']
        self.plot(exp_list)

    def plot(self, exp_list):
        for exp_pos in xrange(len(exp_list)):
            exp = exp_list[exp_pos]
            file_path = '{}queueLen_{}_{}.csv'.format(
                cong_plot.trace_base_path, exp, self.rate_str)
            qlen_data = QueueLenData(file_path)
            data_column = qlen_data.getData(self.node_id, self.buf_man_id)
            plt.plot(data_column[:, 0], data_column[:, 1], marker=
                        cong_plot.marker_iter.next(), markersize=10,
                         linewidth=2, label='{}, {}-{}'.
                        format(exp, str(self.node_id), str(self.buf_man_id)))
        cong_plot.labelPlot('time (ms)', 'Queue length (bytes)', '', 'upper left')
        #plt.axis([0, 100000, 0, 15000000])
        plt.show()


class QueueLenPlotMultiple(object):
    def __init__(self, rate_str, qid_list):
        self.rate_str = rate_str
        self.queue_id_list = qid_list
        exp_list = ['PerIfWithECN']
        self.plot(exp_list)

    def plot(self, exp_list):
        for exp_pos in xrange(len(exp_list)):
            exp = exp_list[exp_pos]
            file_path = '{}queueLen_{}_{}.csv'.format(
                cong_plot.trace_base_path, exp, self.rate_str)
            qlen_data = QueueLenData(file_path)

            for queue_id in self.queue_id_list:
                node_id = queue_id.node_id
                buf_man_id = queue_id.buf_man_id
                data_column = qlen_data.getData(node_id, buf_man_id)
                plt.plot(data_column[:, 0]/1000, data_column[:, 1]/1000, marker=
                            cong_plot.marker_iter.next(), markersize=1,
                             linewidth=2, label='{}, {}-{}'.
                            format(exp, str(node_id-1), str(buf_man_id-1)))
        cong_plot.labelPlot('time (s)', 'Queue length (KB)', '', 'upper left')
        #plt.axis([0, 100000, 0, 15000000])
        plt.show()

class QueueLenData(object):
    SIMU_LENG = 100000.0 # 100s

    NODE_ID_POS = 0
    BUFMAN_ID_POS = 1
    TIME_POS = 2
    QUEUE_LEN_POS = 3

    def __init__(self, file_path):
        all_data_array = np.array(process_trace.readCSVToFloatMatrix(file_path))
        # only retain the flows finished before simu length
        self.array = all_data_array[all_data_array[:, QueueLenData.TIME_POS]
                        <= QueueLenData.SIMU_LENG]

    def getData(self, node_id, buf_man_id):
        valid_entries = self.array[
            self.array[:, QueueLenData.NODE_ID_POS] == node_id]
        valid_entries = valid_entries[
            valid_entries[:, QueueLenData.BUFMAN_ID_POS] == buf_man_id]
        #print valid_entries

        # stacking two column vectors
        ret = np.c_[valid_entries[:, QueueLenData.TIME_POS],
                        valid_entries[:, QueueLenData.QUEUE_LEN_POS]]
        #print ret
        return ret

if __name__ == '__main__':
    rate_str = sys.argv[1]
    if len(sys.argv) == 2:
        qid_list = [QueueIdentifier(x, y) for x,y in
                    [(3,15), (3,0), (3,6)]]
        p = QueueLenPlotMultiple(rate_str, qid_list)



    # assert len(sys.argv) == 4
    # rate_str = sys.argv[1]
    # node_id = int(sys.argv[2])
    # buf_man_id = int(sys.argv[3])
    # p = QueueLenPlot(rate_str, node_id, buf_man_id)