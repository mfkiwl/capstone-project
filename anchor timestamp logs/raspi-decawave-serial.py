import serial
import io
import time
import sys
from timeit import timeit

def main(filename, serial_port, debug=0):
    fh = open(filename,'w+')
    print("filename opened!")
    switch = "Tag"
    try:
        with serial.Serial(serial_port, 115200, timeout=1) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

            receptionNum = -1
            pulseNum = -1
            syncNum = -1

            tS = -1
            tSnew = -1
            tM = -1
            tMnew = -1
            tMraw = -1
            R = -1

            tagID = "N/A"
            DECAtime = -1
            dT = -1
            syncT = -1

            while True:
                line = sio.readline()

                if line.startswith("TimeOut"): continue
                if "Error" in line: continue

                try:
                    if line.startswith("Master"): # Write sync pulse from Master 
                        switch = "Master"
                    if line.startswith("Tag"):  # Write data pulse from Tag 
                        switch = "Tag"

                    if line.startswith("ID"):
                        tagID = line.split(":")[1].strip()

                    if line.startswith("Reception"): # Retrieve the frame number as an INT & 
                        receptionNum = int(line.split(":")[1].strip())
                    if line.startswith("Pulse"): # Retrieve the tag pulse number as an INT for synchronization
                        pulseNum = int(line.split(":")[1].strip())
                    if line.startswith("Sync"): # Retrieve the tag pulse number as an INT for synchronization
                        syncNum = int(line.split(":")[1].strip())

                    if line.startswith("tS:"): # Retrieve the 
                        tS = int(line.split(":")[1].strip())

                    if line.startswith("tSnew:"): # Retrieve the 
                        tSnew = int(line.split(":")[1].strip())

                    if line.startswith("tM:"): # Retrieve the 
                        tM = int(line.split(":")[1].strip())

                    if line.startswith("tMnew:"): # Retrieve the 
                        tMnew = int(line.split(":")[1].strip())

                    if line.startswith("tMraw:"): # Retrieve the 
                        tMraw = int(line.split(":")[1].strip())

                    if line.startswith("R:"): # Retrieve the 
                        R = int(line.split(":")[1].strip())    

                    if line.startswith("T:"): # Retrieve the synchronized decawave time
                        DECAtime = int(line.split(":")[1].strip())
                    if line.startswith("dT:"): # Retrieve the synchronized decawave time
                        dT = int(line.split(":")[1].strip())
                    if line.startswith("syncT:"): # Retrieve the synchronized decawave time
                        syncT = int(line.split(":")[1].strip())

                    if line.startswith("END"): # Reached end of frame, write fields & reset 
                        if (switch == "Master"):
                            if (debug):
                                fh.write("Master Sync\nReception: {}\nSync: {}\ntS: {}\ntSnew: {}\ntM: {}\ntMnew: {}\ntMraw: {}\nR: {}\n\n".format(
                            receptionNum, syncNum, tS, tSnew, tM, tMnew, tMraw, R))
                            else:
                                fh.write("Master Sync\nSync: {}\n\n")
                        if (switch == "Tag"):
                            if (debug):
                                fh.write("Tag Pulse\nID: {}\nReception: {}\nPulse: {}\nanchorT: {}\ndT: {}\nsyncT: {}\n\n".format(
                            tagID, receptionNum, pulseNum, DECAtime, dT, syncT))
                            else:
                                fh.write("Tag Pulse\nID: {}\nPulse: {}\nsyncT: {}\n\n".format(tagID, pulseNum, syncT))
                except ValueError:
                    continue
                
                receptionNum = -1
                pulseNum = -1
                tS = -1
                tSnew = -1
                tM = -1
                tMnew = -1
                tMraw = -1
                R = -1
                DECAtime = -1
                dT = -1
                syncT = -1
                tagID = "N/A"

    except KeyboardInterrupt:
        fh.close()
        print(filename + " closed!")

filename = str(sys.argv[1])
serial_port = str(sys.argv[2])
debug = int(sys.argv[3])
main(filename,serial_port, debug=0)

