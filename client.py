import socket
import customtkinter as ctk
import threading
import pyperclip
import os
from pystray import Icon as icon, MenuItem as item, Menu as menu
from PIL import Image, ImageDraw, ImageTk
import time

def create_image():
    image = Image.open("./appicon.jpg")
    return image

class Client:
    def __init__(self, host, port=12345):
        
        # Configure customtkinter appearance
        ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
        ctk.set_default_color_theme("green")  # Themes: "blue" (default), "green", "dark-blue"
        
        self.root = ctk.CTk()
        self.root.title("Client")
        self.root.geometry("300x200")
        
        # Set window icon
        self.root.iconbitmap("./appicon.ico")
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        while True:
            try:
                self.server.connect((host, port))
                break
            except (ConnectionRefusedError, OSError):
                time.sleep(10)

        ctk.CTkLabel(self.root, text="Message Client", font=("Arial", 18)).pack(pady=20)
        ctk.CTkButton(self.root, text="Send Message", command=self.send_message).pack(pady=10)
        ctk.CTkButton(self.root, text="Close", command=self.shutdown).pack(pady=10)

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
                    print(f"Received message: {msg}")
                    self.show_message(msg)
                    pyperclip.copy(msg)
            except ConnectionResetError:
                self.shutdown()
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def show_message(self, msg, on_close=None):
        print(f"Received message: {msg}")
        # Set window size based on message length
        
        
        avg_width = 50
        extra_space = 50
        min_width = 100
        screen_width = self.root.winfo_screenwidth()  # Get the user's screen width
        max_width = screen_width - 100
        
        calculated_width = avg_width * len(msg) + extra_space
        window_width = max(min_width, min(calculated_width, max_width))
        window_height = 170
        
        alert_window = ctk.CTkToplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry(f"{window_width}x{window_height}")
        alert_window.attributes('-topmost', True)
        
        scrollable_frame = ctk.CTkScrollableFrame(alert_window, width=window_width, height= window_height - 60)
        scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        ctk.CTkLabel(scrollable_frame, text=msg, font=("Arial Black", 46), text_color="red", wraplength=window_width - 40).pack(pady=10, padx=10, fill="both", expand=True)
    
    def send_message(self):
        dialog = ctk.CTkInputDialog(title="Send Message", text="Enter your message:")

        msg = dialog.get_input()
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
        dialog = ctk.CTkInputDialog(title="Server IP", text="Enter server IP address:")
        host = dialog.get_input()
        save_ip_address(host)
    client = Client(host)

if __name__ == "__main__":
    main()
