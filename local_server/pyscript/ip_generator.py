from os import write
import random
import requests
from pathlib import Path

BLACKLIST_PATH = Path('/shared/blacklist_test.txt')
CENTRALTOKEN = "Token f990deebf6b6f888560a4b2bc131989496a55030"

def generate_unique_ips(count):
    # Create a list of all possible IPs
    all_possible = set()

    while len(all_possible) < count:
        # Generate random octets
        first = random.randint(1, 255)
        second = random.randint(0, 255)
        third = random.randint(0, 255)
        fourth = random.randint(0, 255)

        # Skip private and reserved IPs
        if first == 0: continue  # Skip 0
        if first == 10: continue  # Skip 10.0.0.0/8
        if first == 172 and 16 <= second <= 31: continue  # Skip 172.16.0.0/12
        if first == 192 and second == 168: continue  # Skip 192.168.0.0/16
        if first == 127: continue  # Skip loopback
        if first == 169 and second == 254: continue  # Skip link-local

        ip = f"{first}.{second}.{third}.{fourth}"
        all_possible.add(ip)

    return list(all_possible)

def write_ips(num_ips):
    ip_list = generate_unique_ips(num_ips)
    with open(BLACKLIST_PATH, 'w') as f:
        for ip in ip_list:
            f.write(f"{ip}\n")

    return True

if __name__ == "__main__":
    print("Enter amount of IPs to generate: ")
    num_ips = int(input())
    write_ips(num_ips)
    print(f"Finished generating {num_ips} unique IPs in {BLACKLIST_PATH}")
