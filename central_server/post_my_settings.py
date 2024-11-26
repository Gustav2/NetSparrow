import requests

url = "http://yourdomain.com/api/settings/update/"

headers = {
    "Authorization": "Token your_token_here",
    "Content-Type": "application/json",
}

data = {
    "auto_add_blacklist": True,
    "log_suspicious_packets": True,
    "enable_ip_blocking": False,
    "dark_mode": True,
    "notify_blacklist_updates": True,
    "notify_suspicious_activity": False,
}

response = requests.post(url, json=data, headers=headers)

print(response.status_code)
print(response.json())
