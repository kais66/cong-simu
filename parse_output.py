#base_name = 'respTimes_PerIf_'
base_name = 'respTimes_PerFlow_'
rate_str = '0.7'
f = open('output/{}{}.csv'.format(base_name, rate_str), 'r')
data = []
for line in f:
    words = line.split(',')
    data.append(words)
data.sort(key=lambda x: int(x[0]))
outf = open('output/sorted_{}{}.csv'.format(base_name, rate_str), 'w')
for words in data:
    outf.write(','.join(words))
