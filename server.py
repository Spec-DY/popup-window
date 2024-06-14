import socket
from tkinter import simpledialog, Toplevel, Button, Tk, Label, font
import threading
import pyperclip
import os
from pystray import Icon as icon, MenuItem as item, Menu as menu
from PIL import Image, ImageDraw

def create_image():
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    d = ImageDraw.Draw(image)
    d.rectangle([8, 8, 56, 56], fill=(255, 105, 180)) # pink
    return image

class Server:
    def __init__(self, host="0.0.0.0", port=12345):
        self.root = Tk()
        self.root.title("Server")
        self.root.geometry("200x140")
        # List to store client connections
        self.clients = []
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
        # window close button
        self.root.protocol("WM_DELETE_WINDOW", self.close_server)
        self.root.bind("<Unmap>", self.on_minimize)
        self.setup_tray_icon()
        self.icon.run_detached()
        # threading.Thread(target=self.receive_message, daemon=True).start() 

        self.root.mainloop()
    
    def setup_tray_icon(self):
        self.icon = icon("Server",
                         create_image(),
                         menu=menu(item('Show Window', lambda: self.show_window())))
    
    def on_minimize(self, event=None):
        if self.root.state() == 'iconic':
            self.root.withdraw()
            self.icon.visible = True

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.icon.visible = False

    def accept_connections(self):
        while self.running:
            try:
                client, address = self.server.accept()
                if self.running:
                    # Add client to the list
                    self.clients.append(client)
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
                    # Remove client from the list
                    self.clients.remove(client)
                    break
            except ConnectionResetError:
                self.clients.remove(client)
                break

    def show_message(self, msg, on_close=None):
        # set window size
        avg_width = 50
        extra_space = 10
        window_size = avg_width*len(msg)+extra_space
        alert_window = Toplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry(f"{window_size}x170")

        # keep window on top
        alert_window.attributes('-topmost', True)

        message_font = font.Font(family="Arial Black", size=40, weight="bold")

        # Display the message with the custom font
        Label(alert_window, text=msg, font=message_font, padx=20, pady=20, fg="red").pack()
        Button(alert_window, text="OK", command=lambda: [alert_window.destroy(), on_close() if on_close else None]).pack(pady=10)

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
        self.icon.stop()
        try:
            self.server.close()
        except Exception as e:
            print(f"Error closing socket: {str(e)}")
        finally:
            self.root.destroy()

if __name__ == "__main__":
    server = Server()
