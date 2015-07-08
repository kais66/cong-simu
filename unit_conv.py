def convertMbytepsecToBytepmsec(rate_mbyteps):
    new_rate = float(rate_mbyteps) * 1048
    return new_rate

def convertBytepmsecToMbytepsec(rate_bytepmsec):
    new_rate = float(rate_bytepmsec) / 1048
    return new_rate