import serial
import io
try:
    with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
        sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
        while True:
            print(sio.readline())
except KeyboardInterrupt:
    pass


