import serial
import io
import time
import sys
from timeit import timeit

# function wrapper to use for timeit, taken from https://www.pythoncentral.io/time-a-python-function/
def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)
    return wrapped

#forwards line from SIO to FH. writes additional line if it spots a line that starts with pointMarker
def forwardLine(fh,sio, pointMarker): 
    line = sio.readline()
    fh.write(line)
    if line.startswith(pointMarker):
        fh.write("RPI_rx_ts_nanosec:" + str(time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)) + "\r\n")

def main(filename,pointMarker="Reception"):
    fh = open(filename,'w+')
    print("filename opened!")
    try:
        with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            timeForwardLine = wrapper(forwardLine,fh,sio,pointMarker) # wrapper to time how long it takes to forwardLine
            while True:
                print("time:" + str(timeit(timeForwardLine)))
                #forwardLine(fh,sio,pointMarker)
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
pointMarker = str(sys.argv[2])
main(filename,pointMarker)

