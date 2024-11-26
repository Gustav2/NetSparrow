import requests

url = "https://netsparrow.viktorkirk.com/api/settings/update/"

headers = {
    "Authorization": "f990deebf6b6f888560a4b2bc131989496a55030",
    "Content-Type": "application/json",
}

data = {
    "auto_add_blacklist": True,
    "log_suspicious_packets": True,
    "enable_ip_blocking": True,
    "dark_mode": True,
    "notify_blacklist_updates": True,
    "notify_suspicious_activity": True,
}

response = requests.post(url, json=data, headers=headers)

print(response.status_code)
print(response.json())
