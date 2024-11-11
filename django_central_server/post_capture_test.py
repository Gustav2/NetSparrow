import requests
import json

url = "https://netsparrow.viktorkirk.com/packet_capture/"

data = {
    "ip": "3.3.3.3",
    "url": "http://333.com"
}

headers = {
    "Authorization": "Token 71c08c598319cded9587ff36b0069226fd0565a1",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json=data) 

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
