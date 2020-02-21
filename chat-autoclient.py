# Based on work by sentdex https://pythonprogramming.net/client-chatroom-sockets-tutorial-python-3/
# Variant of chat-client.py, that automatically sends a message
# For load-testing and potentially the final product
import socket
import select
import errno
import sys
from time import time
import timeit
from serverconfigs import *
# SERVER_IP and SERVER_PORT are the IP and port # of the chat server. Can be changed from serverconfigs.py
# BYTE_FORMAT is the encoding format used. Currently UTF-8, can be changed from serverconfigs.py

my_username = input("Username: ")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP,SERVER_PORT))
client_socket.setblocking(False)

username = my_username.encode(BYTE_FORMAT)
username_header = f"{len(username):<{HEADER_LENGTH}}".encode(BYTE_FORMAT)
client_socket.send(username_header + username)

timeSinceLastMsg = 0
timerExecTime = timeit.timeit('time.time()')
print(f"time executes in {timerExecTime} seconds")

while True:
    message = f"timeSinceLastMsg:{timeSinceLastMsg}"
    startTime = time()

    if message:
        message = message.encode(BYTE_FORMAT)
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode(BYTE_FORMAT)
        client_socket.send(message_header + message)

    try:
        while True: # receive messages until an error occurs
            username_header = client_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                print("connection closed by server")
                sys.exit()

            username_length = int(username_header.decode(BYTE_FORMAT).strip())
            username = client_socket.recv(username_length).decode(BYTE_FORMAT)
            # since server sends (user['header'] + user['data'] + message['header'] + message['data']),
            # we have already extracted username header & data
            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode(BYTE_FORMAT).strip())
            message = client_socket.recv(message_length).decode(BYTE_FORMAT)

            print(f"{username} > {message}")

    except IOError as e:
        if e.errno != errno.EAGAIN or e.errno != errno.EWOULDBLOCK:
            print('Reading error',str(e))
            sys.exit()
        continue

    except Exception as e:
        print('General error',str(e))
        sys.exit()
    # take current time, subtract start time, and subtract time for both time calls
    timeSinceLastMsg = time() - startTime - 2*timerExecTime