# Netsparrow Local Unit Installation Guide

## Introduction
The **Netsparrow Local Unit** is designed to streamline your home network setup by leveraging a Raspberry Pi and Docker. This guide will walk you through the installation and configuration process step by step.

---

## Prerequisites
### Hardware
- Raspberry Pi (preferably with USB 3.0 ports)
- Two USB-to-Ethernet adapters
- Ethernet cables

### Software/Accounts
- [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/operating-systems/)
- GitHub account with access to your repository
- A computer with SSH capability

---

## Installation Steps
### 1. Prepare the Raspberry Pi
1. Download and install **Raspberry Pi OS Lite** onto an SD card.
2. Enable the following on the SD card:
   - SSH
   - Wi-Fi credentials
   - Username and password
3. Insert the SD card into the Raspberry Pi and power it on.

### 2. Access the Raspberry Pi
1. Locate the Raspberry Pi's IP address on your router’s admin page.
2. SSH into the Raspberry Pi using the IP address:
   ```bash
   ssh pi@<raspberry-pi-ip>
   ```

### 3. Update and Install Dependencies
1. Run the following commands:
   ```bash
   sudo apt update
   sudo apt upgrade -y
   sudo apt install git -y
   ```
2. Install Docker:
   ```bash
   curl -sSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```
3. Generate an SSH key:
   ```bash
   ssh-keygen -t rsa
   ```
4. Display the public key:
   ```bash
   cat /home/pi/.ssh/id_rsa.pub
   ```
5. Add the displayed SSH key as a **Deploy Key** in your GitHub repository settings:
   - Navigate to: `https://github.com/<user_name>/<repository_name>/settings/keys`
   - Paste the key and enable write access.

### 4. Clone and Setup the Repository
1. Clone the Netsparrow repository:
   ```bash
   git clone git@github.com:Gustav2/NetSparrow.git
   ```
2. Reboot the Raspberry Pi:
   ```bash
   sudo reboot
   ```
3. Navigate to the local server directory:
   ```bash
   cd NetSparrow/local_server
   ```
4. Build and run the Docker containers:
   ```bash
   docker compose up -d --build
   ```

### 5. Connect the Hardware
1. Plug the two USB-to-Ethernet adapters into the Raspberry Pi's USB 3.0 ports.
2. Connect the following:
   - Ethernet cable from your modem to one of the USB Ethernet adapters on the Raspberry Pi.
   - Ethernet cable from the second USB Ethernet adapter on the Raspberry Pi to your router's WAN port.

---

## Troubleshooting
- **SSH Issues**: Ensure SSH is enabled and the correct IP address is used.
- **Docker Permissions**: If Docker commands fail, try logging out and back in to refresh group permissions.
- **Network Connectivity**: Double-check Ethernet connections and adapter placement.

For further assistance, consult the project’s [GitHub Issues](https://github.com/Gustav2/NetSparrow/issues).

---

## Contributions
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or bug reports.

---

## License
This project is licensed under the [MIT License](LICENSE).
