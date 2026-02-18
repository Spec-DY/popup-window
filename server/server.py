import socket
import threading
import signal
import sys
import json
import os
import base64
from datetime import datetime
import logging
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives import serialization

PORT_NUMBER = 12345
KEY_ROTATION_INTERVAL = 14400  # Rotate AES key (in seconds)

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

        # Generate AES-256 session key
        self.aes_key = os.urandom(32)
        self.key_exchanged = set()
        self.client_public_keys = {}
        self.stop_event = threading.Event()
        logging.info("AES-256 session key generated")

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

        # Start AES key rotation thread
        self.rotation_thread = threading.Thread(
            target=self.key_rotation_loop, daemon=True)
        self.rotation_thread.start()

        # Wait for commands (skip if no stdin, e.g. systemd)
        if sys.stdin and sys.stdin.isatty():
            while self.running:
                try:
                    cmd = input().strip().lower()
                    if cmd == 'quit' or cmd == 'exit':
                        self.close_server()
                        break
                except EOFError:
                    break
        else:
            try:
                self.stop_event.wait()
            except KeyboardInterrupt:
                self.close_server()

    def create_message(self, msg_type, data):
        return json.dumps({
            "type": msg_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    def get_client_list(self):
        """Get list of connected clients"""
        return [f"{address[0]}:{address[1]}" for _, address, _ in self.clients.values()]

    def handle_key_exchange(self, client_addr, public_key_pem):
        """Encrypt AES session key with client's RSA public key and send it back"""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode())
            self.client_public_keys[client_addr] = public_key
            encrypted_key = public_key.encrypt(
                self.aes_key.hex().encode(),
                asym_padding.PKCS1v15()
            )
            response = self.create_message("session_key", {
                "encrypted_key": base64.b64encode(encrypted_key).decode()
            })
            client_socket, _, _ = self.clients[client_addr]
            client_socket.send(response.encode())
            self.key_exchanged.add(client_addr)
            logging.info(f"Key exchange completed with {client_addr}")
        except Exception as e:
            logging.error(f"Key exchange failed for {client_addr}: {e}")

    def key_rotation_loop(self):
        """Periodically rotate the AES session key"""
        while not self.stop_event.wait(KEY_ROTATION_INTERVAL):
            self.rotate_aes_key()

    def rotate_aes_key(self):
        """Generate a new AES key and distribute to all connected clients"""
        self.aes_key = os.urandom(32)
        logging.info("AES key rotated")
        for client_addr, public_key in list(self.client_public_keys.items()):
            try:
                encrypted_key = public_key.encrypt(
                    self.aes_key.hex().encode(),
                    asym_padding.PKCS1v15()
                )
                response = self.create_message("session_key", {
                    "encrypted_key": base64.b64encode(encrypted_key).decode()
                })
                client_socket, _, _ = self.clients[client_addr]
                client_socket.send(response.encode())
            except Exception as e:
                logging.error(
                    f"Failed to send rotated key to {client_addr}: {e}")

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
                self.clients[client_addr] = (
                    client, address, datetime.now().isoformat())
                logging.info(f"Connected with {client_addr}")

                # Send welcome status
                welcome_msg = self.create_message(
                    "status", {"code": "200", "message": "Connected successfully"})
                client.send(welcome_msg.encode())

                # Broadcast updated client list
                self.broadcast_client_list()

                threading.Thread(target=self.handle_client,
                                 args=(client_addr,)).start()
            except socket.timeout:
                continue  # Check running flag every second
            except Exception as e:
                logging.error(f"Accept error: {e}")
                break

    def handle_client(self, client_addr):
        client, address, _ = self.clients[client_addr]
        while self.running:
            try:
                msg = client.recv(4096).decode()
                if msg:
                    logging.info(f"Received data from {client_addr}")

                    # Check if this is a key exchange message
                    try:
                        parsed = json.loads(msg)
                        if isinstance(parsed, dict) and parsed.get("type") == "key_exchange":
                            self.handle_key_exchange(
                                client_addr, parsed.get("public_key", ""))
                            continue
                    except (json.JSONDecodeError, ValueError):
                        pass

                    # Encrypted message - broadcast opaquely with sender info
                    broadcast_msg = json.dumps({
                        "type": "msg",
                        "data": msg,
                        "sender": client_addr,
                        "timestamp": datetime.now().isoformat()
                    })
                    self.broadcast(broadcast_msg, client, encrypted_only=True)

                    # Send status response to sender
                    status_msg = self.create_message(
                        "status", {"code": "200", "message": "Message sent successfully"})
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

    def broadcast(self, message, sender=None, encrypted_only=False):
        """Broadcast JSON message to all clients except sender.
        If encrypted_only=True, only send to clients that completed key exchange."""
        for client_addr, (client_socket, _, _) in list(self.clients.items()):
            if sender is None or client_socket != sender:
                if encrypted_only and client_addr not in self.key_exchanged:
                    continue
                try:
                    client_socket.send(message.encode())
                except Exception as e:
                    logging.error(f"Error broadcasting to {client_addr}: {e}")
                    self.remove_client(client_addr)

    def remove_client(self, client_addr):
        if client_addr in self.clients:
            client, _, _ = self.clients[client_addr]
            try:
                client.close()
            except Exception as e:
                logging.error(f"Error closing client {client_addr}: {e}")
            del self.clients[client_addr]
            self.key_exchanged.discard(client_addr)
            self.client_public_keys.pop(client_addr, None)
            logging.info(f"Disconnected from {client_addr}")
            # Broadcast updated client list
            self.broadcast_client_list()

    def close_server(self):
        self.running = False
        self.stop_event.set()
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
