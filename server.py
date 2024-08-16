import socket
import threading
import logging
import re

# Variables for holding information about connections
connections = []
total_connections = 0
connections_lock = threading.Lock()

# Setting up logging
logging.basicConfig(
    filename="server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

"""
Client class, new instance created for each connected client
Each instance has the socket and address that is associated with it
Along with an assigned ID and a name chosen by the client
"""


class Client(threading.Thread):
    def __init__(self, socket, address, id, name, signal):
        threading.Thread.__init__(self)
        self.socket = socket
        self.address = address
        self.id = id
        self.name = name
        self.signal = signal

    def __str__(self):
        return f"{self.id} ({self.name}) - {self.address}"

    """Attempt to get data from client
    If unable to, assume client has disconnected and remove them from server data
    If able to and we get data back, print it in the server and send it back to every
    client aside from the client that has sent it
    .decode is used to convert the byte data into a printable string
    """

    def run(self):
        while self.signal:
            try:
                data = self.socket.recv(1024)  # Increased buffer size
                if not data:
                    break

                # Handle initial client name setting
                if self.name == "Name":
                    self.name = data.decode("utf-8").strip()
                    logging.info(f"Client {self.id} has set their name to {self.name}")
                    continue

                # Broadcast message to other clients
                logging.info(f"ID {self.id} ({self.name}): {data.decode('utf-8')}")
                self.broadcast(data)

            except OSError as e:
                logging.error(f"Error: {e}")
                break

        self.disconnect()

    def broadcast(self, data):
        with connections_lock:
            for client in connections:
                if client.id != self.id:
                    try:
                        client.socket.sendall(data)
                    except OSError as e:
                        logging.error(f"Error sending data to client {client.id}: {e}")

    def disconnect(self):
        with connections_lock:
            logging.info(f"Client {self.id} ({self.name}) has disconnected.")
            connections.remove(self)
        self.socket.close()
        self.signal = False


# Wait for new connections
def new_connections(server_socket):
    global total_connections
    while True:
        try:
            client_socket, address = server_socket.accept()
            with connections_lock:
                client = Client(client_socket, address, total_connections, "Name", True)
                connections.append(client)
                client.start()
                logging.info(f"New connection at ID {client}")
                total_connections += 1
        except OSError as e:
            logging.error(f"Error accepting new connection: {e}")
            break


def shutdown_server(server_socket):
    logging.info("Shutting down server...")
    with connections_lock:
        for client in connections:
            client.signal = False
            client.socket.close()
    server_socket.close()
    logging.info("Server has been shut down.")


def main():
    try:
        # Get host and port with validation
        host = input("Host (e.g., 127.0.0.1): ")
        if not re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", host):
            print("Invalid IP address.")
            return

        port = input("Port (e.g., 5555): ")
        try:
            port = int(port)
            if not (1 <= port <= 65535):
                raise ValueError("Port out of range.")
        except ValueError as e:
            print(f"Invalid port: {e}")
            return

        # Create new server socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(5)
        logging.info(f"Server started on {host}:{port}. Waiting for connections...")

        # Create new thread to wait for connections
        new_connections_thread = threading.Thread(
            target=new_connections, args=(server_socket,)
        )
        new_connections_thread.start()

        # Wait for thread to complete (if ever)
        new_connections_thread.join()

    except KeyboardInterrupt:
        print("\nServer is shutting down...")
        shutdown_server(server_socket)
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        shutdown_server(server_socket)


if __name__ == "__main__":
    main()
