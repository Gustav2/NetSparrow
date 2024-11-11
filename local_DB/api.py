import valkey
from time import perf_counter_ns
import random as rand
import requests
import json

#from django_central_server.app.website.models import Blacklist

#Connect to Valkey // consider if this should be a function instead
v = valkey.Valkey(host='127.0.0.1', port=6379)

# SHOULD THIS BE IN RUST?????????

# Most of these could potentially benefit from an added "badness" score value
# so that upper layers could decide how to handle the packet

# Maybe use the expiration function to block IPs for a certain amount of time?

# Need functions to manually save, start, stop and restart DB if needed

# Compare function to check if key exists
def checkPacket(packet):
    return v.exists(packet)

# Function to add malicous key to DB
def addPacket(packet):
    v.set(packet, 'malicious')

# Function to remove key from DB
def removePacket(packet):
    v.delete(packet)

# Function to flush DB
def flushDB(verify):
    if verify == "verify":
        v.flushdb()
    else:
        print("No verify, not flushing DB")

# Function to check value of key
def checkVal(packet):
    return v.get(packet)

# Function to list all keys in DB
def listDB():
    return v.keys()

# Function to check size of DB
def sizeDB():
    return v.dbsize()


# Function to copy central DB
def pullCentral(token):
    url = "https://netsparrow.viktorkirk.com/settings/myblacklist/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    blacklist_data = response.json()["myblacklists"]

    for i in blacklist_data:
        ip = str(i["blacklist_entry__capturedpacket_entry__ip"])
        url = str(i["blacklist_entry__capturedpacket_entry__url"])
        v.set(ip, url)


# Function to push local DB to central DB
def pushCentral(token):
    url = "https://netsparrow.viktorkirk.com/packet_capture/"
    headers = {
        "Authorization": str(token),
        "Content-Type": "application/json"
    }

    for key in v.scan_iter():
        data = {
            "ip": key.decode('utf-8'),
            "url": v.get(key).decode('utf-8') #type:ignore
        }

        response = requests.post(url, headers=headers, json=data)
        print(url, headers, data)
        print("Status Code:", response.status_code)
        print("Response JSON:", response.json())

    """
    # fix for only sending unique packages
    data_list = []
    for key in v.scan_iter():
        entry = {
            "ip": key.decode('utf-8'),
            "url": v.get(key).decode('utf-8')
        }
        data_list.append(entry)
    """


def speedtest(sample_size, random=False):
    if random == True:
        target = rand.randint(0, sample_size)
    else:
        target = sample_size / 2
    print("Creating list...")
    for i in range(sample_size):
        v.set(str(i), 'test')
    t1 = perf_counter_ns()
    checkPacket(str(target))
    t2 = perf_counter_ns()
    flushDB("verify")

    return ((t2-t1) / 1000000)


if __name__ == "__main__":
    flushDB("verify")
    v.set('1.2.3.4', "a")
    v.set('5.6.7.8', "b")
    v.set('12.13.14.15', "c")
    pushCentral("Token c4a591a7123521fe94b36eb5f40f4c2bd5d5415f")

"""
    flushDB("verify")

    v.set('1.2.3.4', "a")
    v.set('5.6.7.8', "b")
    v.set('12.13.14.15', "c")

    pullCentral("Token c4a591a7123521fe94b36eb5f40f4c2bd5d5415f")
"""
