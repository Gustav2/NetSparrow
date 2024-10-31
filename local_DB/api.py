import valkey
from time import perf_counter_ns
import random as rand

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
