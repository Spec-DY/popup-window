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
    d.rectangle([8, 8, 56, 56], fill=(10, 186, 181))
    return image

class Client:
    def __init__(self, host, port=12345):
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry("200x140")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.server.connect((host, port))
        except (ConnectionRefusedError, OSError):
            self.show_message("Connection Failed", self.shutdown)  # callback

        Button(self.root, text="Send Message", command=self.send_message).pack(pady=20)
        Button(self.root, text="Close", command=self.shutdown).pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.bind("<Unmap>", self.on_minimize)

        self.setup_tray_icon()
        self.icon.run_detached()  # Start the tray icon in a detached thread immediately

        threading.Thread(target=self.receive_message, daemon=True).start()  # Start the receiver thread as a daemon
        self.root.mainloop()

    def setup_tray_icon(self):
        self.icon = icon("Client",
                         create_image(),
                         menu=menu(item('Show Window', lambda: self.show_window())))
                                   #item('Exit', lambda: self.shutdown())))

    def on_minimize(self, event=None):
        if self.root.state() == 'iconic':
            self.root.withdraw()
            self.icon.visible = True

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.icon.visible = False

    def receive_message(self):
        while True:
            try:
                msg = self.server.recv(1024).decode()
                if msg:
                    self.show_message(msg)
                    pyperclip.copy(msg)
            except ConnectionResetError:
                self.shutdown()
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def show_message(self, msg, on_close=None):
        # set window size
        avg_width = 50
        extra_space = 10
        window_size = avg_width*len(msg)+extra_space
        alert_window = Toplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry(f"{window_size}x170")
        alert_window.attributes('-topmost', True)
        
        message_font = font.Font(family="Arial Black", size=40, weight="bold")

        Label(alert_window, text=msg, font=message_font, padx=20, pady=20).pack()
        Button(alert_window, text="OK", command=lambda: [alert_window.destroy(), on_close() if on_close else None]).pack(pady=10)

    def send_message(self):
        msg = simpledialog.askstring("Input", "Enter your message:")
        if msg:
            self.server.send(msg.encode())

    def shutdown(self):
        self.icon.stop()
        try:
            self.server.close()
        except Exception as e:
            print(f"Error closing socket: {str(e)}")
        finally:
            self.root.destroy()

def save_ip_address(ip):
    with open("ip_address.txt", "w") as file:
        file.write(ip)

def load_ip_address():
    if os.path.exists("ip_address.txt"):
        with open("ip_address.txt", "r") as file:
            return file.readline().strip()
    return None

def main():
    host = load_ip_address()
    if host is None:
        host = simpledialog.askstring("Target", "Enter host IP address:")
        save_ip_address(host)
    client = Client(host)

if __name__ == "__main__":
    main()
