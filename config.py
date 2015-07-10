import json
import sys
DEBUG = False

class Config(object):
    def __init__(self, json_path, cmd_line_argv):
        ''' 
            this class incoporates configuration specs from both the json file 
            and cmd line arguments. Cmd line specifies exp_type, rate, ecn...
        '''
        with open(json_path) as jfile:
            data = json.load(jfile)

        self.exp_type = None
        self.rate_str = None
        self.use_ECN = None

        self.initCmdLinePara(cmd_line_argv)
        #self.initJsonPara(data)

    def initCmdLinePara(self, argv):
        if len(argv) > 4 or len(argv) < 3:
            print 'Wrong number of cmd line parameters, exiting'
            print 'usage: main.py cong_str rate_str [true/false]'
            sys.exit(-1)

        self.exp_type = argv[1]
        self.rate_str = argv[2]

        if len(argv) == 3:
            self.use_ECN = False
        else:
            self.use_ECN = True if argv[3].lower() == 'true' else False

        print 'exp_type: {}'.format(self.exp_type)
        print 'rate_str: {}'.format(self.rate_str)
        print 'use_ECN: {}'.format(self.use_ECN)

        assert not (self.exp_type == 'PerFlow' and self.use_ECN)
            
    def initJsonPara(self, json_data):
        global_dict = self.json_data['global']
        if 'experiment_type' in global_dict:
            self.exp_type = global_dict['experiment_type']
            print 'exp_type: {}'.format(self.exp_type)

        if 'rate_str' in global_dict:
            self.rate_str = global_dict['rate_str']
            print 'rate_str: {}'.format(self.rate_str)

        if 'use_ECN' in global_dict:
            self.use_ECN = global_dict['use_ECN']
            print 'use_ECN: {}'.format(self.use_ECN)


#c = Config('setting/base.json')
