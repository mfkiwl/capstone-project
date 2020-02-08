# Based on work by sentdex: https://pythonprogramming.net/server-chatroom-sockets-tutorial-python-3/
import socket
# Select module gives operating level IO 
import select

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1234
# initialize server socket and modify it to let us reuse address
server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# connect socket to IP and port and begin listening
server_socket.bind((IP,PORT))
server_socket.listen()
# Keep list of sockets to keep track of and begin dictionary of clients
sockets_list = [server_socket]
clients = {}

def receive_message(client_socket):
    try:
        # Extract header
        message_header = client_socket.recv(HEADER_LENGTH)
        # if no header received, then client closed connection
        if not len(message_header): return False
        # Else, extract message length from header and return a dictionary containing header and message
        message_length = int(message_header.decode('utf-8'))
        return {"header":message_header,"data": client_socket.recv(message_length)}

    except: # if client sends absolute bonkers big message
        return False
def main():
    while True:
        # may want to add 4th param that decides how long to wait before timing out
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
        for notified_socket in read_sockets:
            # if someone just connected, accept connection 
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                user = receive_message(client_socket)
                if user is False:
                    continue
                # add new connection to list of client sockets
                sockets_list.append(client_socket)
                clients[client_socket] = user
                print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username:{user['data'].decode('utf-8')}")
            
            else:
                message = receive_message(notified_socket)
                if message is False:
                    print(f"Closed section from {clients[notified_socket]['data'].decode('utf-8')}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue

                user = clients[notified_socket]
                print(f"Received message from {user['data'].decode('utf-8')}:{message['data'].decode('utf-8')}")

                # Relay message sent from one client to all others (except original sender)
                for client_socket in clients:
                    if client_socket != notified_socket:
                        client_socket.send(user['header'] + user['data'] + message['header'] + message['data'])

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            del clients[notified_socket]

main()