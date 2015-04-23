from chunk import Chunk

class OutputLogger(object):
    def __init__(self):
        self._file = 'output/respTimes.txt'
        self._content = [] # list of lines to be written to file

    def log(self, chunk):
        self._content.append(str(chunk.timestamp()-chunk.startTimestamp()) + '\n')
        
    def write(self):
        with open(self._file, 'a') as f:
            for line in self._content:
                f.write(line)
