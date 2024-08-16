import socket
import sys
import threading

"""Wait for incoming data from the server
.decode will for the data into a string
"""


def receive(socket, signal):
    while signal[0]:
        try:
            data = socket.recv(32)
            if not data:
                print("Connection closed by the server.")
                signal[0] = False
            else:
                print(str(data.decode("utf-8")))
        except OSError as e:
            print(f"Error: {e}")
            signal[0] = False
            break


# Gets input for host and designated tcp port
desHost = input("Host: ")
desPort = int(input("Port: "))
# Attempts to connect to the server
try:
    socketVar = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socketVar.connect((desHost, desPort))
except socket.error as e:
    print(f"Could not make connection to server")
    print(f"Press enter to exit: {e}")
    sys.exit(0)
"""
creates a new thread 
to wait for the data 
"""
thread_receive = threading.Thread(target=receive, args=(socketVar, True))
thread_receive.start()


"""
Sends data to the server using the .decode will form the data 
into a string to turn it into bytes. 
To be sent across the network
"""
while True:
    message = input()
    if message.lower() == "quit":
        socketVar.close()
        break
    socketVar.send(str.encode(message))
