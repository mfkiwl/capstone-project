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

                if line.startswith("TimeOut"): continue
                if "Error" in line: continue
                if line.startswith("Reception"): # Retrieve the frame number as an INT & get the RPI current time
                    receptionNum = int(line.split(":")[1].strip())
                    RPItimeNS = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                    print("receptionNum:" + str(receptionNum))
                    print("RPItimeNS:" + str(RPItimeNS))
                if line.startswith("resp_rx_ts"): # Retrieve the decawave time (automatically converting from a HEX string to INT)
                    DECAtime = int(line.split(":")[1].strip(),16)
                    DECAtimeNS = DECAtime * 1.0 * (10**3) / (499.2 * 128)
                    print("DECAtimeNS:" + str(DECAtimeNS))
                if line.startswith("anchor"): # Retrieve the anchor ID as a STRING
                    anchorID = line.split(":")[1].strip()
                    print("anchorID:" + str(anchorID))
                if line.startswith("tag"):  # Retrieve the tag ID as a STRING
                    tagID = line.split(":")[1].strip()
                    print("tagID:" + str(tagID))
                if line.startswith("END"): # Reached end of frame
                    fh.write("Reception #: {}\nAnchor ID: {}\nTag ID: {}\nRPI Time(NS): {}\nDECAWAVE Time(NS): {}\n".format(receptionNum, anchorID, tagID, RPItimeNS, DECAtimeNS))
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
serial_port = str(sys.argv[2])
main(filename,serial_port)

