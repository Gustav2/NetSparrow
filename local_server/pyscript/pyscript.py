import os
import struct
import requests
import errno
from pathlib import Path
from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import NamedTuple
import uvicorn
import time

centralToken = "Token f990deebf6b6f888560a4b2bc131989496a55030"

PIPE_NAME = "/tmp/analysis_pipe"
FORMAT = "=4s4sf"

INPUT_PIPE_NAME = "/tmp/packet_pipe"
OUTPUT_PIPE_NAME = "/tmp/analysis_pipe"
BATCH_SIZE = 100
MAX_WAIT_TIME = 30
RECONNECT_DELAY = 0.1
ERROR_CHECK_INTERVAL = 0.01
MAX_EMPTY_READS = 500
CONNECTION_TIMEOUT = 5.0
CONFIDENCE_THRESHOLD = 0.9

tempSettings = {
    "mlPercentage": 100,
    "caution": 5
}

app = FastAPI()
blacklist_path = Path('/shared/blacklist.txt')

class Data(BaseModel):
    value: str

class Settings(BaseModel):
    mlPercentage: int
    caution: int

class PacketData(NamedTuple):
    timestamp: int
    source_ip: bytes
    dest_ip: bytes
    packet_size: int
    protocol: int
    data: bytes

@app.post("/settings", status_code=status.HTTP_200_OK)
def handle_settings(data: Settings):
    print("Settings received")
    print("mlPercentage: " + str(data.mlPercentage))
    print("Caution: " + str(data.caution))
    return {"status": "success"}

    # % of packages to ML
    #

@app.get("/settings")
def get_settings():
    return {"mlPercentage": tempSettings["mlPercentage"], "caution": tempSettings["caution"]}

@app.get("/test")
def test():
    return {"status": "success"}

def pullBlacklist(token):
    url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    print(response.json())
    blacklist_data = response.json()["myblacklists"]

    """ ACTUAL FUNCTION
    with open(blacklist_path, 'w', newline='') as file:
        for i in blacklist_data:
            ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
            file.write(ip + "\n")
            #url = str(i["blacklist_entry__capturedpacket_entry__url"])
    """
    with open("blacklist.txt", 'w', newline='') as file:
        for i in blacklist_data:
            ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
            file.write(ip + "\n")
            #url = str(i["blacklist_entry__capturedpacket_entry__url"])

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

                # Unpack the binary data
                source_ip, dest_ip, confidence = struct.unpack(FORMAT, raw_data)

                # Convert IP addresses to readable format
                source_ip_str = ip_bytes_to_string(source_ip)
                dest_ip_str = ip_bytes_to_string(dest_ip)

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
    while True:
        print("pulling")
        pullBlacklist(centralToken)
        print("pulled blacklist")

        print("Reading from pipe!")
        read_from_pipe()

        time.sleep(5)
        print("sleep")
    #pushBlacklist(centralToken)
    #uvicorn.run(app, host="0.0.0.0", port=8000)
