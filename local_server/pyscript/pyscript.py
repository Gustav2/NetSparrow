import os
import struct
import requests
import threading
import time
import ipaddress
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

myIP = "172.26.120.53"
CENTRALTOKEN = "Token f990deebf6b6f888560a4b2bc131989496a55030"
PIPE_NAME = "/shared/analysis_pipe"
FORMAT = "=4s4sf"
BLACKLIST_PATH = Path('/shared/blacklist.txt')
SETTINGS_PATH = Path('/shared/settings.txt')

ml_confidence_threshold = 0.9

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            "/shared/ns_service_manager.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
    ]
)

def pull_blacklist(CENTRALTOKEN):
    try:
        url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"
        headers = {
            "Authorization": str(CENTRALTOKEN),
            "Content-Type": "application/json"
        }
        logging.info("Blacklist URL set...")

        response = requests.get(url, headers=headers)
        logging.info("Got blacklist data...")
        blacklist_data = response.json()["myblacklists"]

        with open(BLACKLIST_PATH, 'w', newline='') as file:
            for key in blacklist_data:
                ip = str(key["blacklist_entry__capturedpacket_entry__ip"])
                file.write(ip + "\n")

        logging.info(f"Finished writing new blacklist of {len(blacklist_data)} entries")

    except Exception:
        logging.info("Failed to pull blacklist, passing...")

def pull_settings(CENTRALTOKEN):
    global ml_confidence_threshold
    try:
        url = "https://netsparrow.viktorkirk.com/api/settings/get/pi/"
        headers = {
            "Authorization": str(CENTRALTOKEN),
        }
        logging.info("Settings URL set...")

        response = requests.get(url, headers=headers)
        settings_data = response.json()
        logging.info(settings_data)

        if "mlCaution" in settings_data:
            ml_confidence_threshold = settings_data["mlCaution"]
            logging.info(f"New ML Confidence Threshold: {ml_confidence_threshold}")

        with open(SETTINGS_PATH, 'w', newline='') as file:
            for key, value in settings_data.items():
                file.write(f"{key}={value}\n")

        logging.info("Finished writing settings")

    except Exception as e:
        logging.info(f"Failed to pull settings with error: {str(e)}, passing...")

def pull_all(CENTRALTOKEN):
    while True:
        pull_blacklist(CENTRALTOKEN)
        time.sleep(1)
        pull_settings(CENTRALTOKEN)
        logging.info("-" * 50)
        time.sleep(4)

def ip_bytes_to_string(ip_bytes):
    return '.'.join(str(b) for b in ip_bytes)

def read_from_pipe():
    url = "https://netsparrow.viktorkirk.com/packet_capture/"
    headers = {
        "Authorization": str(CENTRALTOKEN),
        "Content-Type": "application/json"
    }

    # IP function here

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

                # Unpack the binary data
                source_ip, dest_ip, confidence = struct.unpack(FORMAT, raw_data)
                source_ip_str = ip_bytes_to_string(source_ip)
                dest_ip_str = ip_bytes_to_string(dest_ip)

                logging.info(f"Packet read from pipe: {source_ip_str} -> {dest_ip_str} with confidence {confidence}")

                if float(confidence) >= float(ml_confidence_threshold):
                    logging.info("Confidence passed, pushing to blacklist...")
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
                        ipaddress.ip_network("0.0.0.0"), #
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
    communication_thread = threading.Thread(target=pull_all, args=(CENTRALTOKEN,), daemon=True)

    pipe_thread.start()
    communication_thread.start()

    try:
        while True:
            time.sleep(1)       # Keep the main thread alive
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
