import socket
import threading
import signal
import sys
import json
from datetime import datetime
import logging

PORT_NUMBER = 12345

# Configure logging
logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class Server:
    def __init__(self, host="0.0.0.0", port=PORT_NUMBER):
        self.clients = {}
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
    
    def create_message(self, msg_type, data):
        return json.dumps({
            "type": msg_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_client_list(self):
        """Get list of connected clients"""
        return [f"{address[0]}:{address[1]}" for _, address, _ in self.clients.values()]
        
    
    def signal_handler(self, sig, frame):
        logging.info("\nShutting down server...")
        self.close_server()
        sys.exit(0)

    def accept_connections(self):
        self.server.settimeout(1)  # Add timeout to accept()
        while self.running:
            try:
                client, address = self.server.accept()
                client_addr = f"{address[0]}:{address[1]}"
                self.clients[client_addr] = (client, address, datetime.now().isoformat())
                logging.info(f"Connected with {client_addr}")
                
                # Send welcome status
                welcome_msg = self.create_message("status", {"code": "200", "message": "Connected successfully"})
                client.send(welcome_msg.encode())
                
                # Broadcast updated client list
                self.broadcast_client_list()
                
                threading.Thread(target=self.handle_client, args=(client_addr,)).start()
            except socket.timeout:
                continue  # Check running flag every second
            except Exception as e:
                logging.error(f"Accept error: {e}")
                break

    def handle_client(self, client_addr):
        client, address, _ = self.clients[client_addr]
        while self.running:
            try:
                msg = client.recv(1024).decode()
                if msg:
                    logging.info(f"Received message from {client_addr}: {msg}")
                    self.log_message(address, msg)
                    
                    # Create and broadcast message
                    broadcast_msg = self.create_message("msg", msg)
                    self.broadcast(broadcast_msg, client)
                    
                    # Send status response to sender
                    status_msg = self.create_message("status", {"code": "200", "message": "Message sent successfully"})
                    client.send(status_msg.encode())
                else:
                    self.remove_client(client_addr)
                    break
            except Exception as e:
                logging.error(f"Error handling client {client_addr}: {e}")
                self.remove_client(client_addr)
                break


    def broadcast_client_list(self):
            """Broadcast updated client list to all connected clients"""
            client_list = self.get_client_list()
            client_msg = self.create_message("client", client_list)
            self.broadcast(client_msg)
            
            
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
        
        
    def broadcast(self, message, sender=None):
        """Broadcast JSON message to all clients except sender"""
        for client_socket, _, _ in list(self.clients.values()):
            if sender is None or client_socket != sender:
                try:
                    client_socket.send(message.encode())
                    logging.info(f"Broadcasted message: {message}")
                except Exception as e:
                    logging.error(f"Error broadcasting to client: {e}")
                    # Find and remove the failed client
                    for addr, (socket, _, _) in list(self.clients.items()):
                        if socket == client_socket:
                            self.remove_client(addr)
                            break

    def remove_client(self, client_addr):
        if client_addr in self.clients:
            client, _, _ = self.clients[client_addr]
            try:
                client.close()
            except Exception as e:
                logging.error(f"Error closing client {client_addr}: {e}")
            del self.clients[client_addr]
            logging.info(f"Disconnected from {client_addr}")
            # Broadcast updated client list
            self.broadcast_client_list()

    def close_server(self):
        self.running = False
        for client_addr in list(self.clients.keys()):
            self.remove_client(client_addr)
        try:
            self.server.close()
        except:
            pass
        logging.info("Server closed")

if __name__ == "__main__":
    logging.info("Server started. Type 'quit' or 'exit' to stop the server.")
    server = Server()