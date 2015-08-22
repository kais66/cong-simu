from graph_tool.all import *
import sys

base_path = '../topo_files/'
class TopoPlot(object):
    def __init__(self, topo_str):
        self.file_path = '{}{}.topo'.format(base_path, topo_str)
        self.topo_str = topo_str

    def plot(self):
        g = Graph()
        g.set_directed(False)
        ver_dic = {} # int(id) : vertex
        with open(self.file_path, 'r') as f:
            for line in f:
                if line[0] == '#': continue
                words = line.split(',')
                cur_node = int(words[0])
                num_nbr = int(words[1])
                ver_dic[cur_node] = g.add_vertex()

        with open(self.file_path, 'r') as f:
            for line in f:
                if line[0] == '#': continue
                words = line.split(',')
                cur_node = int(words[0])
                num_nbr = int(words[1])
                for pos in xrange(2, 2+num_nbr):
                    nbr = int(words[pos])
                    if cur_node < nbr:
                        g.add_edge(ver_dic[cur_node], ver_dic[nbr])

        graph_draw(g, vertex_text=g.vertex_index, vertex_font_size=15,
            output_size=(800, 800), output='{}.png'.format(self.topo_str))

if __name__ == '__main__':
    topo_str = sys.argv[1]
    tp = TopoPlot(topo_str)
    tp.plot()
