import redis as valkey
import time

#Connect to Valkey
v = valkey.Redis(host='127.0.0.1', port=6379)


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
    if verify == True:
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

def speedtest(sample_size):
    # Something smart that sets the amount of samples in a "sample" database
    # and then runs a speed test of checking through the entire list
    # returning a time value in miliseconds
