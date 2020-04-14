import serial
import io
import time
import sys
from timeit import timeit

def main(filename, serial_port):
    fh = open(filename,'w+')
    print("filename opened!")
    try:
        with serial.Serial(serial_port, 115200, timeout=1) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            while True:
                receptionNum = "N/A"
                RPItimeNS = -1
                DECAtime = -1
                DECAtimeNS = -1
                anchorID = "N/A"
                tagID = "N/A"
                line = sio.readline()
                print(line)

                if line.startswith("TimeOut"): continue
                if "Error" in line: continue
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
                    fh.write("Reception #: {}\nAnchor ID: {}\nTag ID: {}\nRPI Time(NS): {}\nDECAWAVE Time(NS): {}\n".format(receptionNum, anchorID, tagID, RPItimeNS, DECAtimeNS))
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
serial_port = str(sys.argv[2])
main(filename,serial_port)

