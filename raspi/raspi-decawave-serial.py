import serial
import io
import time

def main(filename,pointMarker="Reception #"):
    try:
        fh = open(filename,"w+")
        with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            while True:
                if sio.readline.startswith(pointMarker):
                    fh.write("RPI_rx_ts_nanosec: %d\r\n", %time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW))
                fh.write(sio.readline())
    except KeyboardInterrupt:
        printf(filename + "closed!")
        close(filename)


