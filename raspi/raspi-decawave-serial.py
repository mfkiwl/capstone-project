import serial
import io
import time

def main(filename,pointMarker="Reception #"):
    fh = open(filename,"w+")
    try:
        with serial.Serial('/dev/ttyACM0', 115200, timeout=0) as ser:
            sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
            while True:
                if sio.readline().startswith(pointMarker):
                    fh.write("RPI_rx_ts_nanosec:" + str(time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)) + "\r\n")
                fh.write(sio.readline())
    except KeyboardInterrupt:
        fh.close()
        printf(filename + "closed!")

filename = sys.argv[1]
pointMarker = sys.argv[2]
main(filename,pointMarker)

