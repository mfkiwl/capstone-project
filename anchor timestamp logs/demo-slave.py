import serial
import io
import sys

with serial.Serial(str(sys.argv[1]), 115200, timeout=1) as ser:
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))

    anchorID = ""
    pulseNum = -1
    syncT = -1

    while True:
        line = sio.readline()
        if line.startswith("TimeOut"): continue
        if "Error" in line: continue

        try:
            if line.startswith("Anchor"):
                anchorID = line.split(":")[1].strip()

            if line.startswith("Pulse"): # Retrieve the tag pulse number as an INT for synchronization
                pulseNum = int(line.split(":")[1].strip())

            if line.startswith("syncT:"): # Retrieve the synchronized decawave time
                syncT = int(line.split(":")[1].strip())

            if line.startswith("END"): # Reached end of frame, write fields & reset 
                sys.stdout.write("anchor {} Pulse {} syncT {}\n".format(anchorID,pulseNum,syncT))
                anchorID = ""
                pulseNum = -1
                syncT = -1

        except ValueError:
            continue
                

