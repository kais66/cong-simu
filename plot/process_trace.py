import csv
def readCSVToFloatMatrix(filepath):
    '''
    Given a csv file, read its content into a matrix of floats.
    :param filepath:
    :return:
    '''
    matrix = []
    with open(filepath, 'rb') as f:
        reader = csv.reader(f, delimiter=',', quotechar='|')
        for row in reader:
            try:
                matrix.append([float(entry) for entry in row if entry != '\n'])
            except ValueError as e:
                print 'valueError: {} and {}'.format(row, row[-1])
    return matrix

#mtx = readCSVToFloatMatrix('../input_files/traff_poisson_10000.txt')
#print mtx