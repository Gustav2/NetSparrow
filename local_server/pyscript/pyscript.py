import os
import struct
import requests
import threading
import time
from pathlib import Path

centralToken = "Token f990deebf6b6f888560a4b2bc131989496a55030"
myIP = "172.26.120.53"

PIPE_NAME = "/shared/analysis_pipe"
FORMAT = "=4s4sf"
blacklist_path = Path('/shared/blacklist.txt')

tempSettings = {
    "mlPercentage": 100,
    "caution": 5
}

def pullBlacklist(token):
    url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    print(response.json())
    blacklist_data = response.json()["myblacklists"]

    #ACTUAL FUNCTION
    with open(blacklist_path, 'w', newline='') as file:
        for i in blacklist_data:
            ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
            file.write(ip + "\n")
            #url = str(i["blacklist_entry__capturedpacket_entry__url"])

    """ TESTING FUNCTION
    with open("blacklist.txt", 'w', newline='') as file:
        for i in blacklist_data:
            ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
            file.write(ip + "\n")
            #url = str(i["blacklist_entry__capturedpacket_entry__url"])
    """

    time.sleep(5)

def pushBlacklist(token):
    url = "https://netsparrow.viktorkirk.com/packet_capture/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    with open(blacklist_path, 'r') as file:
        for line in file:
            data = {
                "ip": line.strip()
            }
            print(data)

            response = requests.post(url, headers=headers, json=data)
            print(url, headers, data)
            print("Status Code:", response.status_code)
            print("Response JSON:", response.json())

def ip_bytes_to_string(ip_bytes):
    return '.'.join(str(b) for b in ip_bytes)

def read_from_pipe():
    # Wait for the pipe to exist
    while not os.path.exists(PIPE_NAME):
        print("Waiting for pipe to be created...")
        time.sleep(1)

    print(f"Opening pipe: {PIPE_NAME}")
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

                if confidence > 0.9:
                    if source_ip_str == myIP:
                        data = {
                            "ip": dest_ip_str
                        }
                    else:
                        data = {
                            "ip": source_ip_str
                        }

                    print(data)
                    response = requests.post(url, headers=headers, json=data)

                    print(f"Source IP: {source_ip_str}")
                    print(f"Destination IP: {dest_ip_str}")
                    print(f"Confidence: {confidence}")
                    print("-" * 50)

            except KeyboardInterrupt:
                print("\nStopping...")
                break
            except Exception as e:
                print(f"Error reading from pipe: {e}")
                time.sleep(0.1)

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

""" # Det der virker
    print("Reading from pipe")
    read_from_pipe()
"""
