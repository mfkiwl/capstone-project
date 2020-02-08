import socket
import time
import pickle
# define length of fixed-length header
HEADERSIZE = 10
# A socket is the endpoint that allows a computer to receive information 
# Can only send and receive BYTES over socket
# Define a streaming-type socket object from the IPV4 family
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
# bind socket to tuple containing (IP address, port#)
s.bind((socket.gethostbyname('localhost'),1234))
# prep socket to receive data, being able to queue up N messages

N = 5
s.listen(N)

while True:
    # Accept connection from client and register socket & address of client
    clientsocket, clientaddr = s.accept()
    print(f"connection from {clientaddr} has been established!")
    # Pickle object into bytes
    obj = {1: "Hello", 2: "World"}
    msg = pickle.dumps(obj)
    # Add encoded fixed-length header 
    msg = bytes(f'{len(msg) :<{HEADERSIZE}}','utf-8') + msg
    # Send message to client socket
    clientsocket.send(msg)
