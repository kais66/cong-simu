import random

class Demand(object):
    start_t = 0.0
    def __init__(self):
        pass

    def generate(self):
        length = 1
        #rate = 3000.0 # or 6750, 10000, 
        rate = 10000
        src = [1, 2]
        dst = [6, 7, 8, 9]
        total_bytes = 30 * 1000 * rate

        size = 1048576
        demand = []
        for s in src:
            demand.extend(self.genOneSrc(float(length*1000), s, dst, size, rate))
        demand.sort(key=lambda x: x[3])
        chk_id = 1
        for l in demand:
            l.append(chk_id)
            chk_id += 1
            
        self.write(demand)


    def genOneSrc(self, length, src, dst, size, rate): 
        demand = []
        t = Demand.start_t
        while t < length:
            dst_id = dst[random.randint(0, len(dst)-1)]
            demand.append([src, dst_id, size, t])
            t += size / rate
        Demand.start_t += 0.00001
        return demand 
                 
    
    def write(self, demand):
        fname = 'input_files/traff10000.txt'
        with open(fname, 'w') as f:
            for line in demand:
                f.write(','.join([str(x) for x in line]) + '\n') 

d = Demand()
d.generate()
