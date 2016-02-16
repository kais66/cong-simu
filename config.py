import json
import sys
import argparse
DEBUG = True

valid_val = {
    'exp_type':{'PerIf', 'PerFlow'},
    'topo_str':{'Small9',
                'Abilene', 'Exodus', 'Att', 'Level3', 'Sprint' # rocketfuel
                },
    'traff_str':{'Equal', 'Skewed', 'Full'}
}

class Config(object):
    def __init__(self, json_path, cmd_line_argv):
        ''' 
            this class incoporates configuration specs from both the json file 
            and cmd line arguments. Cmd line specifies exp_type, rate, ecn...
        '''
        with open(json_path) as jfile:
            data = json.load(jfile)

        self.exp_type = None
        self.use_ECN = None
        self.topo_str = None
        self.traff_str = None
        self.rate_str = None
        self.topo_traff_str = None

        # logging periodicity for queue length
        # unit is milli-second
        self.queue_len_log_peri = None


        self.cmdline_parser = argparse.ArgumentParser()
        print cmd_line_argv

        # Command line arg have precedence over the Json file.
        # i.e., only read the settings from Json which have not been set.
        self.initCmdLinePara(cmd_line_argv)
        self.initJsonPara(data)

    def initCmdLinePara(self, argv):
        self.cmdline_parser.add_argument('exp_type')
        self.cmdline_parser.add_argument('use_ECN')

        self.cmdline_parser.add_argument('topo_str')
        self.cmdline_parser.add_argument('traff_str')
        self.cmdline_parser.add_argument('rate_str')

        # parse_args() takes the list of cmd line arg excluding the program name
        # as input argument
        parsed = self.cmdline_parser.parse_args(argv[1:])

        self.exp_type = parsed.exp_type

        use_ECN = parsed.use_ECN.lower()
        assert use_ECN == 'true' or use_ECN == 'false'
        self.use_ECN = True if use_ECN == 'true' else False

        self.topo_str = parsed.topo_str
        self.traff_str = parsed.traff_str
        self.rate_str = parsed.rate_str

        print 'exp_type: {}'.format(self.exp_type)
        print 'use_ECN: {}'.format(self.use_ECN)

        print 'topo_str: {}'.format(self.topo_str)
        print 'traff_str: {}'.format(self.traff_str)
        print 'rate_str: {}'.format(self.rate_str)

        assert self.exp_type in valid_val['exp_type']
        assert not (self.exp_type == 'PerFlow' and self.use_ECN)
        assert self.topo_str in valid_val['topo_str']

    def initJsonPara(self, json_data):
        global_dict = json_data['global']
        if self.queue_len_log_peri is None and 'queue_len_log_periodicity':
            self.queue_len_log_peri = int(global_dict['queue_len_log_periodicity'])
            print 'queue_len_log_periodicity: {}'.format(self.queue_len_log_peri)

        if self.exp_type is None and 'experiment_type' in global_dict:
            self.exp_type = global_dict['experiment_type']
            print 'exp_type: {}'.format(self.exp_type)

        if self.rate_str is None and 'rate_str' in global_dict:
            self.rate_str = global_dict['rate_str']
            print 'rate_str: {}'.format(self.rate_str)

        if self.use_ECN is None and 'use_ECN' in global_dict:
            self.use_ECN = global_dict['use_ECN']
            print 'use_ECN: {}'.format(self.use_ECN)

    # getter functions
    def getQueueLenLogPeri(self):
        return self.queue_len_log_peri

#c = Config('setting/base.json')
