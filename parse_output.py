f = open('output/respTimes_PerIfWithECN_8000.csv', 'r')
data = []
for line in f:
    words = line.split(',')
    data.append(words)
data.sort(key=lambda x: int(x[0]))
outf = open('output/sorted_respTimes_PerIfWithECN_10000.csv', 'w')
for words in data:
    outf.write(','.join(words))
