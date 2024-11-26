import requests

url = "https://netsparrow.viktorkirk.com/api/settings/update/"

headers = {
    "Authorization": "Token your_token_here",
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
