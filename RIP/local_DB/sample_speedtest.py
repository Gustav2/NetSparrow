import random
import csv

# Define how many IPs you want to generate
num_ips = 1000

with open('rand_ip_addresses.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    # Write header (optional)
    writer.writerow(['IP Address'])

    for i in range(num_ips):
        ip = ".".join(str(random.randint(0, 255)) for i in range(4))
        writer.writerow([ip])
        print(ip)

print(f"{num_ips} IP addresses have been written to rand_ip_addresses.csv")
