import socket
from tkinter import *
from tkinter import simpledialog, messagebox
import threading

class Client:
    def __init__(self, host="192.168.50.157", port=12345):
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry("200x140")

        # Setup the socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((host, port))

        # Start the thread for receiving messages
        threading.Thread(target=self.receive_message).start()

        # GUI for sending messages
        Button(self.root, text="Send Message", command=self.send_message).pack(pady=20)
        self.root.mainloop()

    def receive_message(self):
        while True:
            try:
                msg = self.server.recv(1024).decode()
                if msg:
                    messagebox.showinfo("Received Message", msg)
                else:
                    self.server.close()
                    break
            except ConnectionResetError:
                break

    def send_message(self):
        msg = simpledialog.askstring("Input", "Enter your message:")
        if msg:
            self.server.send(msg.encode())

if __name__ == "__main__":
    client = Client()
