from demand import *

if __name__ == "__main__":
    '''
    cmd line argument to this script:
    rate_str: usually the per (src, dst) base rate (skewed traffic would be
                multiple of this rate.
    demand_init_str: identifies which Demand subclass to use (see demand.py)
    SmallEqual, SmallSkewed, AbileneEqual
    '''
    if len(sys.argv) != 3:
        print "usage: python demand.py rate_str demand_init_str"
        sys.exit(-1)

    # the rate str passed in is in the unit of
    rate_str = sys.argv[1]
    demand_init_str = sys.argv[2]

    t = ArrivalTrace(rate_str, demand_init_str)
    t.generate()
