import requests

url = "https://netsparrow.viktorkirk.com/api/settings/update/"

headers = {
    "Authorization": "Token f990deebf6b6f888560a4b2bc131989496a55030",
    "Content-Type": "application/json",
}

data = {
    "auto_add_blacklist": False,
    "log_suspicious_packets": True,
    "enable_ip_blocking": False,
    "dark_mode": True,
    "notify_blacklist_updates": True,
    "notify_suspicious_activity": True,
}

response = requests.post(url, json=data, headers=headers)

print(response.status_code)
print(response.json())
