import serial
import io
import time
import sys
from timeit import timeit

#forwards line from SIO to FH. if it spots a line that starts with pointMarker, then writes additional line 
def forwardLine(fh,sio, pointMarker): 
    line = sio.readline()
    if line.startswith(pointMarker):
        fh.write(line)
        systime = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
        fh.write("RPI_rx_ts_nanosec:" + str(systime))
    else:
        fh.write(line)

def main(filename,pointMarker="R"):
    fh = open(filename,'w+')
    print("filename opened!")
    try:
        with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
            sio = io.TextIOWrapper(io.BufferedReader(ser))
            while True:
                forwardLine(fh,sio,pointMarker)
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
pointMarker = str(sys.argv[2])
main(filename,pointMarker)

