import serial
import io
import sys

with serial.Serial(str(sys.argv[1]), 115200, timeout=1) as ser:
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

    anchorID = ""
    pulseNum = -1
    syncT = -1
    anchorPulse = False

    while True:
        line = sio.readline()
        if line.startswith("TimeOut"):
            anchorPulse = False 
            continue
        if "Error" in line: 
            anchorPulse = False 
            continue

        try:
            if line.startswith("Anchor"):
                anchorID = line.split(":")[1].strip()
                anchorPulse = True

            if line.startswith("Pulse"): # Retrieve the tag pulse number as an INT for synchronization
                pulseNum = int(line.split(":")[1].strip())

            if line.startswith("syncT:"): # Retrieve the synchronized decawave time
                syncT = int(line.split(":")[1].strip())

            if line.startswith("END") and anchorPulse: # Reached end of frame, write fields & reset 
                # print("anchor {} Pulse {} syncT {}\n".format(anchorID,pulseNum,syncT))
                sys.stdout.write("anchor {} Pulse {} syncT {}\n".format(anchorID,pulseNum,syncT))
                sys.stdout.flush()
                anchorID = ""
                pulseNum = -1
                syncT = -1
                anchorPulse = False

        except ValueError:
            anchorPulse = False
            continue
                

