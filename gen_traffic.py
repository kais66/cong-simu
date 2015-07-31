from demand import *
import config
import argparse

if __name__ == "__main__":
    '''
    cmd line argument to this script:
    rate_str: usually the per (src, dst) base rate (skewed traffic would be
                multiple of this rate.
    demand_init_str: identifies which Demand subclass to use (see demand.py)
    SmallEqual, SmallSkewed, AbileneEqual
    '''

    cmdline_parser = argparse.ArgumentParser()
    cmdline_parser.add_argument('topo_str')
    cmdline_parser.add_argument('traff_str')
    cmdline_parser.add_argument('rate_str')

    parsed = cmdline_parser.parse_args(sys.argv[1:])

    topo_str = parsed.topo_str
    traff_str = parsed.traff_str
    rate_str = parsed.rate_str

    t = ArrivalTrace(topo_str, traff_str, rate_str)
    t.generate()
