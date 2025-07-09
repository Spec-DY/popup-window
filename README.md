# Popup Window Like Malware

## Pop up some message windows to your friend's screen while they are using their PC!

[Mobile Version here](https://github.com/Spec-DY/HomeMalwarePopups-Mobile)

### Features:

- Send messages to any connected client.
- Messages appear as popup windows on the client's screen.

### Installation:

1. Run `server.py` in your home server (e.g. Raspberry pi)
2. Find `client.exe` in Releases and run on any Windows PC
3. Enter your server IP address in client end (only required by first time).

### Persistent server.py

You can set up server.py to run as a systemd service. This will ensure that the server restarts automatically in case of an accidental close or machine restart.

#### Steps to Set Up server.py as a systemd Service

1.  Create the systemd Service File: Define the service configuration.
2.  Enable and Start the Service: Enable the service to start at boot and start it immediately.

##### Step 1: Create the systemd Service File

Create a new service file for your server. You can do this by creating a file in the `/etc/systemd/system/`directory. For example, create a file named `messagehub.service`:

```bash
sudo nano /etc/systemd/system/messagehub.service
```

Add the following content to the file:

```bash
[Unit]
Description=MessageHub Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/your/server.py
WorkingDirectory=/path/to/your/working/directory
Restart=always
RestartSec=5
User=yourusername
StandardOutput=append:/var/log/homechat.log
StandardError=append:/var/log/homechat.log

[Install]
WantedBy=multi-user.target
```

Replace `/path/to/your/server.py` with the actual path to your server.py actual path. For me this is: `/home/specdy/HomeMalwarePopups/server.py`. <br>Replace `/path/to/your/working/directory` with the directory where your server should run. For me this is: `/home/specdy/HomeMalwarePopups`. <br>Replace `yourusername` with actual username.

##### Step 2: Enable and Start the Service

Reload the systemd manager configuration to recognize the new service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable messagehub.service
sudo systemctl start messagehub.service
sudo systemctl status messagehub.service
```

You should see output indicating that the service is active and running.

#### Note:

- You can change the host ip address in `ip_address.txt` after first use.
- Right click icon in system tray after minimized.
- `ip_address.txt` is located in `C:\Users\<Username>\AppData\Roaming\annoybox\`
- When clients receive message, it will be automatically copied to clipboard.
