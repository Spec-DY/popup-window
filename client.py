import socket
from tkinter import simpledialog, Toplevel, Button, Tk, Label, font
import threading
import pyperclip

class Client:
    def __init__(self, host="192.168.50.157", port=12345):
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry("200x140")

        # socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((host, port))

        # Start the thread for receiving messages
        threading.Thread(target=self.receive_message).start()

        Button(self.root, text="Send Message", command=self.send_message).pack(pady=20)
        Button(self.root, text="Close", command=self.close_connection).pack(pady=10)
        self.root.mainloop()

    def receive_message(self):
        while True:
            try:
                msg = self.server.recv(1024).decode()
                if msg:
                    self.show_message(msg)
                    pyperclip.copy(msg)
                else:
                    self.server.close()
                    break
            except ConnectionResetError:
                break

    def show_message(self, msg):
        # set window size
        avg_width = 50
        extra_space = 10
        window_size = avg_width*len(msg)+extra_space
        alert_window = Toplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry(f"{window_size}x150")
        alert_window.attributes('-topmost', True)  # keep window on top

        message_font = font.Font(family="Arial", size=40, weight="bold")

        # Display the message with custom font
        Label(alert_window, text=msg, font=message_font, padx=20, pady=20).pack()

        ok_button = Button(alert_window, text="OK", command=alert_window.destroy)
        ok_button.pack(pady=10)

    def send_message(self):
        msg = simpledialog.askstring("Input", "Enter your message:")
        if msg:
            self.server.send(msg.encode())
    
    def close_connection(self):
        try:
            # close socket
            self.server.close()
        except Exception as e:
            print(f"Failed to close the connection: {e}")
        finally:
            self.root.quit()

if __name__ == "__main__":
    client = Client()
