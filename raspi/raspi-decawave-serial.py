import serial
import io
import time
import sys

def main(filename,pointMarker="Reception"):
    fh = open(filename,'w+')
    print("filename opened!")
    try:
        with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            while True:
                t1 = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                line = sio.readline()
                fh.write(line)
                if line.startswith(pointMarker):
                    fh.write("RPI_rx_ts_nanosec:" + str(time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)) + "\r\n")
                t2 = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                print("time: " + str(t2 - t1))
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
pointMarker = str(sys.argv[2])
main(filename,pointMarker)

