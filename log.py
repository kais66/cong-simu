from chunk import Chunk

class OutputLogger(object):
    def __init__(self, file_str):
        self._file = file_str
        self._content = [] # list of lines to be written to file

        f = open(file_str, 'w')
        f.close()

    def log(self, chunk):
        line = "{}, {}, {}, {}, {}, {}\n".format(chunk.id(), chunk.startTimestamp(), \
                chunk.timestamp(), chunk.timestamp()-chunk.startTimestamp(),
                chunk.src(), chunk.dst())
        self._content.append(line)
        
    def write(self):
        with open(self._file, 'a') as f:
            for line in self._content:
                f.write(line)
