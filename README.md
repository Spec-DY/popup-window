# Malware Popups

## Pop up some message windows to your friend's screen while they are using their PC!

### Features:

- Send messages to any connected client.
- Messages appear as popup windows on the client's screen.

### Installation:

1. Run `server.py` in your home server (e.g. Raspberry pi)
2. Run `client.exe` on any Windows PC
3. Enter your server IP address in client end (only required by first time).

#### Note:

- You can change the host ip address in `ip_address.txt` after first use.
- Right click icon in system tray after minimized.
- `ip_address.txt` is located in `C:\Users\<Username>\AppData\Roaming\annoybox\`
- When clients receive message, it will be automatically copied to clipboard.
