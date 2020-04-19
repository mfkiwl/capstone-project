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
            receptionNum = "N/A"
            pulseNum = -1
            RPItimeNS = -1
            # DECAtime = -1
            DECAtimeNS = -1
            anchorID = "N/A"
            tagID = "N/A"
            while True:
                line = sio.readline()

                if line.startswith("TimeOut"): continue
                if "Error" in line: continue

                if line.startswith("Reception"): # Retrieve the frame number as an INT & get the RPI current time
                    receptionNum = int(line.split(":")[1].strip())
                    RPItimeNS = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
                if line.startswith("Pulse"): # Retrieve the tag pulse number as an INT for synchronization
                    pulseNum = int(line.split(":")[1].strip())
                if line.startswith("sync_ts_nanosec"): # Retrieve the synchronized decawave time
                    DECAtimeNS = int(line.split(":")[1].strip())
                    # print("DECAtimeNS:" + str(DECAtimeNS))
                if line.startswith("anchor"): # Retrieve the anchor ID as a STRING
                    anchorID = line.split(":")[1].strip()
                    # print("anchorID:" + str(anchorID))
                if line.startswith("tag"):  # Retrieve the tag ID as a STRING
                    tagID = line.split(":")[1].strip()
                    # print("tagID:" + str(tagID))

                if line.startswith("END"): # Reached end of frame, write fields & reset 
                    fh.write("Reception #: {}\nPulse #: {}\nAnchor ID: {}\nTag ID: {}\nRPI Time(NS): {}\nDECAWAVE Synced Time(NS): {}\n\n".format(
                        receptionNum, pulseNum, anchorID, tagID, RPItimeNS, DECAtimeNS))
                    receptionNum = ""
                    pulseNum = -1
                    RPItimeNS = -1
                    DECAtime = -1
                    DECAtimeNS = -1
                    anchorID = ""
                    tagID = ""
    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
serial_port = str(sys.argv[2])
main(filename,serial_port)

