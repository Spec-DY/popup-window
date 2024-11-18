import socket
import threading
import signal
import sys

class Server:
    def __init__(self, host="0.0.0.0", port=12345):
        self.clients = []
        self.running = True
        
        # Socket setup
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        print(f"Server is listening on {host}:{port}")
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        
        # Start accepting connections in a separate thread
        self.accept_thread = threading.Thread(target=self.accept_connections)
        self.accept_thread.start()
        
        # Wait for commands
        while self.running:
            cmd = input().strip().lower()
            if cmd == 'quit' or cmd == 'exit':
                self.close_server()
                break

    def signal_handler(self, sig, frame):
        print("\nShutting down server...")
        self.close_server()
        sys.exit(0)

    def accept_connections(self):
        self.server.settimeout(1)  # Add timeout to accept()
        while self.running:
            try:
                client, address = self.server.accept()
                self.clients.append(client)
                print(f"Connected with {address}")
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except socket.timeout:
                continue  # Check running flag every second
            except Exception as e:
                print(f"Accept error: {e}")
                break

    def handle_client(self, client):
        while self.running:
            try:
                msg = client.recv(1024).decode()
                if msg:
                    self.broadcast(msg, client)
                else:
                    self.remove_client(client)
                    break
            except:
                self.remove_client(client)
                break

    def broadcast(self, message, sender):
        for client in self.clients[:]:  # Use a copy of the list
            if client != sender:
                try:
                    client.send(message.encode())
                except:
                    self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
            try:
                client.close()
            except:
                pass

    def close_server(self):
        self.running = False
        # Close all client connections
        for client in self.clients[:]:
            self.remove_client(client)
        # Close server socket
        try:
            self.server.close()
        except:
            pass
        print("Server closed")

if __name__ == "__main__":
    print("Server started. Type 'quit' or 'exit' to stop the server.")
    server = Server()