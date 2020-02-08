import socket
import pickle
# define length of fixed-length header
HEADERSIZE = 10
# A socket is the endpoint that allows a computer to receive information 
# Define a streaming-type socket object from the IPV4 family
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# connect to server socket @ host address and port#
s.connect((socket.gethostbyname('localhost'),1234))
# receive N bytes of data from server socket
N = 16
while True:
    full_msg = b''
    new_msg = True
    while True:
        msg = s.recv(N)
        if new_msg:
            print(f"new message length: {msg[:HEADERSIZE]}")
            msglen = int(msg[:HEADERSIZE])
            new_msg = False
        # bytes are pickled so we don't need to decode
        full_msg += msg

        # once we receive the entire message, print it out (minus the header) and reset
        if (len(full_msg) - HEADERSIZE == msglen):
            print("full message received")
            # to remove message, print from 'HEADERSIZE:' , NOT from ':HEADERSIZE'
            print(full_msg[HEADERSIZE:])
            d = pickle.loads(full_msg[HEADERSIZE:])
            print(d)
            new_msg = True
            full_msg = b''

    print(full_msg)

