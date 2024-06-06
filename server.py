import socket
import threading
from tkinter import *
from tkinter import simpledialog, messagebox
from tkinter.font import Font
import pyperclip

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
        self.root.protocol("WM_DELETE_WINDOW", self.close_server)  # window close button
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
                    pyperclip.copy(msg)
                else:
                    client.close()
                    self.clients.remove(client)  # Remove client from the list
                    break
            except ConnectionResetError:
                self.clients.remove(client)
                break

    def show_message(self, msg):
        alert_window = Toplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry("300x200")
        alert_window.attributes('-topmost', True)  # keep window on top

        message_font = Font(family="Arial", size=60, weight="bold")

        # Display the message with the custom font
        Label(alert_window, text=msg, font=message_font, padx=20, pady=20).pack()
        
        ok_button = Button(alert_window, text="OK", command=alert_window.destroy)
        ok_button.pack(pady=10)

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
