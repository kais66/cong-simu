from demand import *

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "usage: python demand.py rate_str"
        sys.exit(-1)
    t = ArrivalTrace(sys.argv[1])
    t.generate()