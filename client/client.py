import socket
import customtkinter as ctk
import threading
import pyperclip
import os
from pystray import Icon as icon, MenuItem as item, Menu as menu
from PIL import Image
import time
import sys
import json


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def create_image():
    image = Image.open(resource_path("appicon.jpg"))
    return image


def get_appdata_path():
    """ Get the path to the application data directory """
    appdata_dir = os.getenv('APPDATA')
    if not appdata_dir:
        appdata_dir = os.path.expanduser("~")
    appdata_path = os.path.join(appdata_dir, "annoybox")
    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)
    return appdata_path


class Client:
    def __init__(self, host, port=12345):

        # Configure customtkinter appearance
        # Modes: "System" (default), "Dark", "Light"
        ctk.set_appearance_mode("System")
        # Themes: "blue" (default), "green", "dark-blue"
        ctk.set_default_color_theme("green")

        self.host = host
        self.port = port
        self.root = ctk.CTk()
        self.root.title("Client")
        self.root.geometry("300x220")

        # Set window icon
        self.root.iconbitmap(resource_path("appicon.ico"))

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected_clients = []
        self.is_connected = False

        # Create main UI elements
        ctk.CTkLabel(self.root, text="Message Client",
                     font=("Arial", 18)).pack(pady=20)
        ctk.CTkButton(self.root, text="Send Message",
                      command=self.send_message).pack(pady=10)
        ctk.CTkButton(self.root, text="Settings",
                      command=self.change_ip_address).pack(pady=10)
        ctk.CTkButton(self.root, text="Close",
                      command=self.shutdown).pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        self.root.bind("<Unmap>", self.on_minimize)

        self.setup_tray_icon()
        self.icon.run_detached()  # Start the tray icon in a detached thread immediately

        # Start connection in a separate thread
        threading.Thread(target=self.connect_to_server, daemon=True).start()

        # Minimize after 200ms
        self.root.after(200, self.auto_minimize)

        self.root.mainloop()

    def connect_to_server(self):
        """Attempt to connect to the server with the current host and port"""
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts and not self.is_connected:
            try:
                self.server.connect((self.host, self.port))
                self.is_connected = True
                # Start the receiver thread only after successful connection
                threading.Thread(target=self.receive_message,
                                 daemon=True).start()
                break
            except (ConnectionRefusedError, OSError) as e:
                attempt += 1
                if attempt == max_attempts:
                    self.root.after(0, self.show_connection_error, str(e))
                    break
                time.sleep(1)

    def show_connection_error(self, error_msg):
        """Show a dialog when connection fails and allow retry or cancel"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Connection Error")
        dialog.geometry("400x220")
        dialog.attributes('-topmost', True)

        # Center the dialog
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        dialog_width = 400
        dialog_height = 220
        x_offset = (screen_width - dialog_width) // 2
        y_offset = (screen_height - dialog_height) // 2
        dialog.geometry(
            f"{dialog_width}x{dialog_height}+{x_offset}+{y_offset}")

        ctk.CTkLabel(dialog, text=f"Failed to connect to {self.host}:{self.port}\nError: {error_msg}",
                     wraplength=350).pack(pady=20)
        ctk.CTkButton(dialog, text="Retry",
                      command=lambda: [dialog.destroy(), threading.Thread(target=self.connect_to_server, daemon=True).start()]).pack(pady=10)
        ctk.CTkButton(dialog, text="Change IP",
                      command=lambda: [dialog.destroy(), self.change_ip_address()]).pack(pady=10)
        ctk.CTkButton(dialog, text="Cancel",
                      command=lambda: [dialog.destroy(), self.shutdown()]).pack(pady=10)

    def auto_minimize(self):
        self.root.withdraw()  # hide window
        self.icon.visible = True  # display tray icon

    def setup_tray_icon(self):
        self.icon = icon("Client",
                         create_image(),
                         title="Popups",
                         menu=menu(
                             item('Show', lambda: self.show_window()),
                             item('Exit', lambda: self.shutdown()))
                         )

    def update_clients_list(self, clients):
        """Update the clients list in the UI"""
        self.connected_clients = clients
        self.clients_textbox.configure(state="normal")
        self.clients_textbox.delete("1.0", "end")
        for client in clients:
            self.clients_textbox.insert("end", f"{client}\n")
        self.clients_textbox.configure(state="disabled")

    def handle_message(self, message_data):
        """Handle different types of messages"""
        try:
            msg = json.loads(message_data)
            msg_type = msg.get("type")
            data = msg.get("data")

            if msg_type == "msg":
                self.show_message(data)
                pyperclip.copy(data)
            elif msg_type == "client":
                self.update_clients_list(data)
            elif msg_type == "status":
                print(f"Status received: {data}")

        except json.JSONDecodeError:
            print(f"Error decoding message: {message_data}")
        except Exception as e:
            print(f"Error handling message: {e}")

    def receive_message(self):
        while self.is_connected:
            try:
                msg = self.server.recv(1024).decode()
                if msg:
                    print(f"Received raw message: {msg}")
                    self.handle_message(msg)
            except ConnectionResetError:
                self.is_connected = False
                self.shutdown()
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def on_minimize(self, event=None):
        if self.root.state() == 'iconic':
            self.root.withdraw()
            self.icon.visible = True

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.icon.visible = False

    def show_message(self, msg):
        print(f"Showing message: {msg}")

        avg_width = 50
        extra_space = 50
        min_width = 100
        screen_width = self.root.winfo_screenwidth()  # Get the user's screen width
        screen_height = self.root.winfo_screenheight()
        max_width = screen_width - 100

        calculated_width = avg_width * len(msg) + extra_space
        window_width = max(min_width, min(calculated_width, max_width))
        window_height = 150

        # Calculate position for the alert window to be centered
        x_offset = (screen_width - window_width) // 2
        y_offset = (screen_height - window_height) // 2

        alert_window = ctk.CTkToplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry(
            f"{window_width}x{window_height}+{x_offset}+{y_offset}")
        alert_window.attributes('-topmost', True)

        # Create main frame
        main_frame = ctk.CTkFrame(alert_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Add scrollable frame for message
        scrollable_frame = ctk.CTkScrollableFrame(
            main_frame, width=window_width-20, height=window_height-60)
        scrollable_frame.pack(fill="both", expand=True)

        # Add message label
        ctk.CTkLabel(
            scrollable_frame,
            text=msg,
            font=("Arial Black", 46),
            text_color="red",
            wraplength=window_width-40
        ).pack(pady=5, padx=5, fill="both", expand=True)

        # Add reply button in scrollable frame instead of main frame
        # so we dont have to increase window height
        ctk.CTkButton(
            scrollable_frame,
            text="Reply",
            command=self.send_message
        ).pack(pady=(5, 0))  # Top padding only

    def send_message(self):
        if not self.is_connected:
            self.root.after(0, self.show_connection_error,
                            "Not connected to server")
            return
        dialog = ctk.CTkInputDialog(
            title="Send Message", text="Enter your message:")

        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Get dialog window size (after it has been created)
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()

        # Calculate position for the dialog window to be centered
        x_offset = (screen_width - dialog_width) // 2
        y_offset = (screen_height - dialog_height) // 2

        # Set the geometry of the dialog window
        dialog.geometry(f"{x_offset}+{y_offset}")

        msg = dialog.get_input()
        if msg:
            self.server.send(msg.encode())

    def change_ip_address(self):
        """Open a dialog to change the IP address and reconnect"""
        dialog = ctk.CTkInputDialog(
            title="Change Server IP", text="Enter new server IP address:")

        # Get screen width and height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Get dialog window size (after it has been created)
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()

        # Calculate position for the dialog window to be centered
        x_offset = (screen_width - dialog_width) // 2
        y_offset = (screen_height - dialog_height) // 2

        # Set the geometry of the dialog window
        dialog.geometry(f"{x_offset}+{y_offset}")

        new_ip = dialog.get_input()
        if new_ip:
            # Save the new IP address
            save_ip_address(new_ip)
            # Update the host
            self.host = new_ip
            # Close the current socket
            try:
                self.server.close()
            except Exception as e:
                print(f"Error closing socket: {str(e)}")
            # Create a new socket and reconnect
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.is_connected = False
            threading.Thread(target=self.connect_to_server,
                             daemon=True).start()

    def shutdown(self):
        # display window first
        self.root.deiconify()

        # close socket
        try:
            self.server.close()
        except Exception as e:
            print(f"Error closing socket: {str(e)}")

        # stop icon
        if hasattr(self, 'icon'):
            self.icon.stop()

        # destroy window after 300ms
        self.root.after(300, self.root.destroy)


def save_ip_address(ip):
    appdata_path = get_appdata_path()
    ip_file_path = os.path.join(appdata_path, "ip_address.txt")
    with open(ip_file_path, "w") as file:
        file.write(ip)


def load_ip_address():
    appdata_path = get_appdata_path()
    ip_file_path = os.path.join(appdata_path, "ip_address.txt")
    if os.path.exists(ip_file_path):
        with open(ip_file_path, "r") as file:
            return file.readline().strip()
    return None


def main():
    host = load_ip_address()
    if host is None:
        dialog = ctk.CTkInputDialog(
            title="Server IP", text="Enter server IP address:")
        host = dialog.get_input()
        if host:  # only save if user entered something
            save_ip_address(host)
    if host:  # only create client if we have a host
        client = Client(host)


if __name__ == "__main__":
    main()
