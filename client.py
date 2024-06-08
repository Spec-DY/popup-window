import socket
from tkinter import simpledialog, Toplevel, Button, Tk, Label, font
import threading
import pyperclip

class Client:
    def __init__(self, host, port=12345):
        self.root = Tk()
        self.root.title("Client")
        self.root.geometry("200x140")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((host, port))

        # start the thread for receiving messages
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
        window_size = avg_width * len(msg) + extra_space

        alert_window = Toplevel(self.root)
        alert_window.title("Received Message")
        alert_window.geometry(f"{window_size}x150")

        # keep window on top
        alert_window.attributes('-topmost', True)
        message_font = font.Font(family="Arial", size=40, weight="bold")

        # Display the message with custom font
        Label(alert_window, text=msg, font=message_font, padx=20, pady=20).pack()

        # message ok button
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

def main():
    
    host = "192.168.50.157"
    client = Client(host)
    

if __name__ == "__main__":
    main()
