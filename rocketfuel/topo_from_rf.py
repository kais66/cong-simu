#!/usr/bin/python
###############################################################################
# Given Intra.txt, Rocketfuel intra AS topologies, and an AS number, output
# the nodes, and the links (topology)
###############################################################################

class ASTopoParser(object):
    INPUT_PATH = 'input/RFfull_Intra.txt'
    def __init__(self, as_num):
        self.as_num = as_num

        self.node_line = []
        self.link_line = []

        self.locate()

        self.node_dic = {} # node string : id
        self.topo = {} # node_id : set(nbr1_id, nbr2_id, ...)

        self.parseNode()
        self.parseLink()

    def locate(self):
        as_found = False
        with open(ASTopoParser.INPUT_PATH, 'r') as f:
            for line in f:
                words = line.split('$')
                assert len(words) >= 1
                sub_words = words[0].split(',')

                if not as_found:
                    if len(sub_words) != 2: continue

                    as_num = int(sub_words[1])
                    if self.as_num == as_num:
                        self.node_line = words
                        as_found = True
                else:
                    assert len(sub_words) != 2 # link line
                    self.link_line = words
                    break
        print self.node_line
        print self.link_line

    def parseNode(self):
        node_str_list = self.node_line[1].split(';')
        node_id = 1
        for node_str in node_str_list:
            if node_str == '\n': continue
            if node_str not in self.node_dic:
                self.node_dic[node_str] = node_id
                node_id += 1
        print 'num nodes: {}'.format(len(self.node_dic))

        node_list = self.node_dic.keys()
        node_list.sort()

        for node in node_list:
            print node

    def parseLink(self):
        for link_str in self.link_line:
            if link_str == '\n': continue
            two_node = link_str.split(';')
            id_list = [self.node_dic[two_node[0]], self.node_dic[two_node[1]]]
            for index in xrange(2):
                this_id, other_id = id_list[index], id_list[1-index]
                if this_id not in self.topo:
                    self.topo[this_id] = set()
                nbr_set = self.topo[this_id]
                if other_id not in nbr_set:
                    nbr_set.add(other_id)

        # for id in self.topo:
        #     print 'nbrs of node: {}'.format(id)
        #     print self.topo[id]

    def outputTopoRaw(self, as_name):
        '''
        generate the topology file, for raw sprint topo, i.e. without access
        trees.
        :return:
        '''
        output_path = '../topo_files/{}.topo'.format(as_name)

        with open(output_path, 'w') as f:
            for node, nbr_set in self.topo.iteritems():
                #print node
                #print nbr_set
                assert len(nbr_set) > 0
                line_words = [node, len(nbr_set)]
                for nbr in nbr_set:
                    line_words.append(nbr)
                line_words = [str(entry) for entry in line_words]
                line_words.append('\n')
                f.write(','.join(line_words))

# from rocketfuel paper
as_dic = {'Abilene':11537, 'Exodus':3967, 'Att':7018, 'Level3':3356,
          'Sprint':1239}
if __name__ == '__main__':
    as_name = 'Sprint'
    as_number = as_dic[as_name]
    ps = ASTopoParser(as_number)
    ps.outputTopoRaw(as_name)
    #ps = ASTopoParser(701)
