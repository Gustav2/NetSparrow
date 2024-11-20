import requests
import json

url = "https://netsparrow.viktorkirk.com/settings/add_to_myblacklist/"

data = {
    "ip": "10.10.10.10",
    "url": "No URL"
}

headers = {
    "Authorization": "Token 71c08c598319cded9587ff36b0069226fd0565a1",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=data) 

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
