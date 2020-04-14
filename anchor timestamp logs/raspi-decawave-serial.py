import serial
import io
import time
import sys
from timeit import timeit

def main(filename):
    fh = open(filename,'w+')
    print("filename opened!")
    try:
        with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            while True:
                receptionNum = "\n"
                RPItimeNS = 0
                DECAtime = 0
                DECAtimeNS = 0
                anchorID = "\n"
                tagID = "\n"
                line = sio.readline()
                if line.startswith("Reception"): # Retrieve the frame number as an INT & get the RPI current time
                    receptionNum = int(line.split(":")[1])
                    RPItimeNS = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                if line.startswith("resp_rx_ts"): # Retrieve the decawave time (automatically converting from a HEX string to INT)
                    DECAtime = int(line.split(":")[1],16)
                    DECAtimeNS = DECAtime * 1.0 * (10**3) / (499.2 * 128)
                if line.startswith("anchor"): # Retrieve the anchor ID as a STRING
                    anchorID = line.split(":")[1]
                if line.startswith("tag"):  # Retrieve the tag ID as a STRING
                    tagID = line.split(":")[1]
                if line.startswith("\n"):
                    fh.write("Reception #: {} Anchor ID: {} \n Tag ID: {} \n RPI Time(NS): {} \n DECAWAVE Time(NS): {} \n",
                    receptionNum, anchorID, tagID, RPItimeNS, DECAtimeNS)
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
main(filename)

