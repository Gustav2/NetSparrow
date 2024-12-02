import os
import struct
import requests
import threading
import time
import ipaddress
import logging
from pathlib import Path

centralToken = "Token f990deebf6b6f888560a4b2bc131989496a55030"
myIP = "172.26.120.53"

PIPE_NAME = "/shared/analysis_pipe"
FORMAT = "=4s4sf"
blacklist_path = Path('/shared/blacklist.txt')

logging.basicConfig(
    filename = "/shared/pyscript.log",
    level = logging.INFO,
    format = "%(asctime)s - %(levelname)s - %(message)s",
    filemode = "a"
)

tempSettings = {
    "mlPercentage": 100,
    "caution": 5
}

def pullBlacklist(centralToken):
    while True:
        try:
            url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"
            headers = {
                "Authorization": str(centralToken),
                "Content-Type": "application/json"
            }
            logging.info("URL Set...")

            response = requests.get(url, headers=headers)
            logging.info(response.json())
            blacklist_data = response.json()["myblacklists"]

            with open(blacklist_path, 'w', newline='') as file:
                for i in blacklist_data:
                    ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
                    file.write(ip + "\n")
                    #url = str(i["blacklist_entry__capturedpacket_entry__url"])
            logging.info("Finished writing new blacklist")

        except Exception:
            logging.info("Failed to pull blacklist, retrying...")

        time.sleep(5)

def ip_bytes_to_string(ip_bytes):
    return '.'.join(str(b) for b in ip_bytes)

def read_from_pipe():
    # Wait for the pipe to exist
    while not os.path.exists(PIPE_NAME):
        logging.info("Waiting for pipe to be created...")
        time.sleep(1)

    logging.info(f"Opening pipe: {PIPE_NAME}")
    with open(PIPE_NAME, 'rb') as pipe:
        while True:
            try:
                # Read one record worth of bytes
                raw_data = pipe.read(struct.calcsize(FORMAT))
                if not raw_data:
                    continue

                url = "https://netsparrow.viktorkirk.com/packet_capture/"
                headers = {
                    "Authorization": str(centralToken),
                    "Content-Type": "application/json"
                }

                # Unpack the binary data
                source_ip, dest_ip, confidence = struct.unpack(FORMAT, raw_data)

                # Convert IP addresses to readable format
                source_ip_str = ip_bytes_to_string(source_ip)
                dest_ip_str = ip_bytes_to_string(dest_ip)

                if confidence >= 0.9:
                    if source_ip_str == myIP:
                        data = {
                            "ip": dest_ip_str
                        }
                    else:
                        data = {
                            "ip": source_ip_str
                        }
                    current_ip = ipaddress.ip_address(data["ip"])

                    exempt_ranges = [
                        ipaddress.ip_network("10.0.0.0/8"), # 10.0.0.0 - 10.255.255.255
                        ipaddress.ip_network("172.16.0.0/12"), # 172.16.0.0 - 172.31.255.255
                        ipaddress.ip_network("192.168.0.0/16"), # 192.168.0.0 - 192.168.255.255
                    ]

                    if any(current_ip in exempt_range for exempt_range in exempt_ranges):
                        logging.info(f"Exempt IP: {data['ip']}")
                        continue

                    else:
                        logging.info(f"Pushing to blacklist: {current_ip}")
                        logging.info(f"with confidence: {confidence}")
                        logging.info("-" * 50)
                        try:
                            response = requests.post(url, headers=headers, json=data)
                        except requests.exceptions.RequestException as e:
                            logging.error(f"Failed to push to blacklist: {e}")
                            continue

            except Exception as e:
                logging.error(f"Error reading from pipe: {e}")
                time.sleep(0.5)

if __name__ == "__main__":
    pipe_thread = threading.Thread(target=read_from_pipe, daemon=True)
    communication_thread = threading.Thread(target=pullBlacklist, args=(centralToken,), daemon=True)

    pipe_thread.start()
    communication_thread.start()

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
