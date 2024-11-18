import socket
import threading
import signal
import sys
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Server:
    def __init__(self, host="0.0.0.0", port=12345):
        self.clients = []
        self.running = True
        
        # Socket setup
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        logging.info(f"Server is listening on {host}:{port}")
        
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
        logging.info("\nShutting down server...")
        self.close_server()
        sys.exit(0)

    def accept_connections(self):
        self.server.settimeout(1)  # Add timeout to accept()
        while self.running:
            try:
                client, address = self.server.accept()
                self.clients.append((client, address))
                logging.info(f"Connected with {address}")
                threading.Thread(target=self.handle_client, args=(client, address)).start()
            except socket.timeout:
                continue  # Check running flag every second
            except Exception as e:
                logging.error(f"Accept error: {e}")
                break

    def handle_client(self, client, address):
        while self.running:
            try:
                msg = client.recv(1024).decode()
                if msg:
                    logging.info(f"Received message from {address}: {msg}")
                    self.log_message(address, msg)
                    self.broadcast(msg, client)
                else:
                    self.remove_client(client)
                    break
            except Exception as e:
                logging.error(f"Error handling client {address}: {e}")
                self.remove_client(client)
                break

    def log_message(self, address, message):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ip": address[0],
            "message": message
        }
        try:
            with open("message_logs.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            logging.info(f"Logged message: {log_entry}")
        except Exception as e:
            logging.error(f"Error logging message: {e}")
        
        
    def broadcast(self, message, sender):
        for client, _ in self.clients[:]:  # Use a copy of the list
            if client != sender:
                try:
                    client.send(message.encode())
                    logging.info(f"Broadcasted message: {message}")
                except Exception as e:
                    logging.error(f"Error broadcasting to client: {e}")
                    self.remove_client(client)

    def remove_client(self, client):
        for c, address in self.clients:
            if c == client:
                self.clients.remove((c, address))
                try:
                    client.close()
                except Exception as e:
                    logging.error(f"Error closing client {address}: {e}")
                logging.info(f"Disconnected from {address}")
                break

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
        logging.info("Server closed")

if __name__ == "__main__":
    logging.info("Server started. Type 'quit' or 'exit' to stop the server.")
    server = Server()