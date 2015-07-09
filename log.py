from chunk import Chunk

class OutputLogger(object):
    def __init__(self, file_str):
        self._file = file_str
        self._content = [] # list of lines to be written to file

        # just so we are not appending to the output file from last run.
        f = open(file_str, 'w')
        f.close()

    # def log(self, chunk):
    #     line = "{}, {}, {}, {}, {}, {}\n".format(chunk.id(), chunk.startTimestamp(), \
    #             chunk.timestamp(), chunk.timestamp()-chunk.startTimestamp(),
    #             chunk.src(), chunk.dst())
    #     self._content.append(line)

    def log(self, stat_list):
        stat_str = [str(x) for x in stat_list]
        stat_str[-1] += '\n'
        #stat_str.append('\n')
        self._content.append(','.join(stat_str))
        
    def write(self):
        with open(self._file, 'a') as f:
            for line in self._content:
                f.write(line)

