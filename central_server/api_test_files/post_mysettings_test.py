import requests

# API endpoint
url = "https://netsparrow.viktorkirk.com/api/settings/update/"

# User token for authentication
headers = {
    "Authorization": "Token f990deebf6b6f888560a4b2bc131989496a55030",
    "Content-Type": "application/json",
}

data = {
    "auto_add_blacklist": False,
    "log_suspicious_packets": False,
    "enable_ip_blocking": False,
    "dark_mode": False,
    "notify_blacklist_updates": False,
    "notify_suspicious_activity": False,
    "mlCaution" : 0.9,
    "mlPercentage" : 1,
}

# Make the POST request
response = requests.post(url, json=data, headers=headers)

# Print the response
print(response.status_code)
print(response.json())
