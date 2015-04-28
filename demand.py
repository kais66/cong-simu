import random
import sys

class Demand(object):
    start_t = 0.0
    def __init__(self):
        pass

    def generate(self, band_str):
        length = 100000.0

        #rate = 3000.0 # or 6750, 10000, 
        #self.band = 10000.0 # bytes per ms
        self.band = float(band_str)
        src = [1, 2]
        dst = [6, 7, 8, 9]

        size = 1048576
        demand = []
        for s in src:
            #demand.extend(self.genOneSrcPoisson(length, s, dst, size))
            demand.extend(self.genOneSrcPoissonSkewed(length, s, dst, size))
        demand.sort(key=lambda x: x[3])
        chk_id = 1
        for l in demand:
            l.append(chk_id)
            chk_id += 1
            
        self.write(demand)


    def genOneSrcDeterministic(self, length, src, dst, size): 
        demand = []
        t = Demand.start_t
        while t < length:
            dst_id = dst[random.randint(0, len(dst)-1)]
            demand.append([src, dst_id, size, t])
            t += float(size) / self.band
        Demand.start_t += 0.00001
        return demand 

    def genOneSrcPoisson(self, length, src, dst, size):
        demand = []
        t = 0
        while t < length:
            dst_id = dst[random.randint(0, len(dst)-1)]
            arrival_rate = float(self.band) / size
            t += random.expovariate(arrival_rate) # this function takes mean rate as arg, or reciprocal of inter-arr time
            demand.append([src, dst_id, size, t])
        return demand
    def genOneSrcPoissonSkewed(self, length, src, dst, size):
        demand = []
        t = 0
        cnt = 0
        while t < length:
            dst_id = (dst[-1] if cnt%2==0 else dst[random.randint(0, len(dst)-2)])
            arrival_rate = float(self.band) / size
            t += random.expovariate(arrival_rate) # this function takes mean rate as arg, or reciprocal of inter-arr time
            demand.append([src, dst_id, size, t])
            cnt += 1
        return demand
                 
    
    def write(self, demand):
        fname = 'input_files/traff_poisson_' + str(int(self.band)) + '.txt'
        with open(fname, 'w') as f:
            for line in demand:
                f.write(','.join([str(x) for x in line]) + '\n') 

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print "usage: python demand.py rate_str"
        sys.exit(-1)
    d = Demand()
    d.generate(sys.argv[1])
