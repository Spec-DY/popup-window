import socket
import threading
from tkinter import *
from tkinter import simpledialog, messagebox

class Server:
    def __init__(self, host="0.0.0.0", port=12345):
        self.root = Tk()
        self.root.title("Server")
        self.root.geometry("200x140")
        self.clients = []  # List to store client connections
        self.running = True

        # Socket setup
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen(1)
        print(f"Server is listening on localhost:{port}")

        # Start the thread for accepting connections
        threading.Thread(target=self.accept_connections).start()

        # GUI for sending messages
        Button(self.root, text="Send Message", command=self.send_message).pack(pady=20)
        Button(self.root, text="Close Server", command=self.close_server).pack(pady=20)
        self.root.protocol("WM_DELETE_WINDOW", self.close_server)  # Handle window close button
        self.root.mainloop()

    def accept_connections(self):
        while self.running:
            try:
                client, address = self.server.accept()
                if self.running:
                    self.clients.append(client)  # Add client to the list
                    print(f"Connected with {address}")
                    threading.Thread(target=self.handle_client, args=(client,)).start()
            except socket.timeout:
                continue
            except OSError:
                break

    def handle_client(self, client):
        while True:
            try:
                msg = client.recv(1024).decode()
                if msg:
                    self.show_message(msg)
                else:
                    client.close()
                    self.clients.remove(client)  # Remove client from the list
                    break
            except ConnectionResetError:
                self.clients.remove(client)
                break

    def show_message(self, msg):
        messagebox.showinfo("Received Message", msg)

    def send_message(self):
        msg = simpledialog.askstring("Input", "Enter your message:")
        if msg:
            # Send message to all connected clients
            for client in self.clients:
                client.send(msg.encode())

    def close_server(self):
        self.running = False
        for client in self.clients:
            client.close()
        self.server.close()
        self.root.destroy()  

if __name__ == "__main__":
    server = Server()
